import os
import asyncio
import logging
from icecream import ic

from pyrogram import Client, filters
from pytgcalls import GroupCallFactory

from dotenv import load_dotenv
from rich.logging import RichHandler


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

log = logging.getLogger("rich")

load_dotenv()

app = Client('fai', os.environ["API_ID"], os.environ["API_HASH"])
app.get_users()

group_call = GroupCallFactory(app).get_device_group_call(
    os.environ["INPUT_DEVICE"],  # group_call.get_recording_devices()
    os.environ["OUTPUT_DEVICE"]  # group_call.get_playout_devices()
)


def compare(old, new):
    result = {}

    if old is None:
        return new
    else:
        for key in old:
            if old[key] != getattr(new, key):
                result[key] = {
                    "old": old[key],
                    "new": getattr(new, key)
                }

    return result


def get_id(peer):
    if isinstance(peer, int):
        return peer

    try:
        return peer.user_id
    except:
        return peer.channel_id


class State:
    chat_id = 0
    members = dict()
    raised_hand_members = []
    pointed = None

    handlers = dict()

    def __init__(self) -> None:
        self.on_changed(["raise_hand_rating"])(
            self.raise_hand_handler
        )
        self.on_changed(["muted"])(
            self.muted_handler
        )

    async def update(self, client, participant):
        changed = dict()
        user_id = get_id(participant.peer)

        if participant.left:
            self.members[user_id] = None

            log.info(
                f"{(await id_to_name(client, [user_id]))[0]}: Left"
            )
        else:
            # if not First created
            if self.members.get(user_id, None) is not None:
                changed = compare(self.members[user_id], participant)
            else:
                log.info(
                    f"{(await id_to_name(client, [user_id]))[0]}: Join"
                )

                changed = {
                    "peer": participant.peer,
                    "date": {"old": None, "new": participant.date},
                    "source": {"old": None, "new": participant.source},
                    "muted": {"old": None, "new": participant.muted},
                    "can_self_unmute": {"old": None, "new": participant.can_self_unmute},
                    "just_joined": {"old": None, "new": participant.just_joined},
                    "versioned": {"old": None, "new": participant.versioned},
                    "muted_by_you": {"old": None, "new": participant.muted_by_you},
                    "volume_by_admin": {"old": None, "new": participant.volume_by_admin},
                    "is_self": {"old": None, "new": participant.is_self},
                    "video_joined": {"old": None, "new": participant.video_joined},
                    "active_date": {"old": None, "new": participant.active_date},
                    "volume": {"old": None, "new": participant.volume},
                    "about": {"old": None, "new": participant.about},
                    "raise_hand_rating": {"old": None, "new": participant.raise_hand_rating},
                }

            self.members[user_id] = {
                "peer": participant.peer,
                "date": participant.date,
                "source": participant.source,
                "muted": participant.muted,
                "can_self_unmute": participant.can_self_unmute,
                "just_joined": participant.just_joined,
                "versioned": participant.versioned,
                "muted_by_you": participant.muted_by_you,
                "volume_by_admin": participant.volume_by_admin,
                "is_self": participant.is_self,
                "video_joined": participant.video_joined,
                "active_date": participant.active_date,
                "volume": participant.volume,
                "about": participant.about,
                "raise_hand_rating": participant.raise_hand_rating,
            }

        log.debug(participant.peer)
        log.debug(changed)

        await self._trigger_change(client, participant, changed)
        await self._trigger_member_io(client, participant, changed)

        return changed

    def on_changed(self, changes:list):
        def decorator(func):
            for change in changes:
                if self.handlers.get(change, None) is None:
                    self.handlers[change] = [func]
                else:
                    self.handlers[change].append(func)

        return decorator

    async def _trigger_member_io(self, client, participant, changed):
        tasks = []

        for func in self.handlers.get("member_io", []):
            tasks.append(asyncio.ensure_future(
                func(
                    client,
                    peer=participant.peer,
                    enter=not participant.left,
                    changed=changed
                )
            ))

        await asyncio.gather(*tasks)

    async def _trigger_change(self, client, participant, changed):
        tasks = []

        for key in changed:
            if self.handlers.get(key, None) is not None:
                for func in self.handlers[key]:
                    tasks.append(asyncio.ensure_future(
                        func(
                            client,
                            peer=participant.peer,
                            old=changed[key]["old"],
                            new=changed[key]["new"],
                            changed=changed
                        )
                    ))

        await asyncio.gather(*tasks)

    async def raise_hand_handler(self, client, peer, old, new, changed):
        if (old is not None):
            log.info(
                f"{(await id_to_name(client, [get_id(peer)]))[0]}: lower hand"
            )
            self.raised_hand_members.remove(get_id(peer))

            if changed.get('can_self_unmute', {}) == {
                "old": False, "new": True
            }:
                if self.pointed is None:
                    log.debug(f"{get_id(peer)}: pointed")
                    self.pointed = get_id(peer)

                for member in self.raised_hand_members:
                    input_peer = await client.resolve_peer(member)

                    # Unraise hand
                    await group_call.edit_group_call_member(input_peer, muted=False)
                    await group_call.edit_group_call_member(input_peer, muted=True)

        elif (new is not None):
            log.info(
                f"{(await id_to_name(client, [get_id(peer)]))[0]}: raise hand"
            )
            self.raised_hand_members.append(get_id(peer))

    async def muted_handler(self, client, peer, old, new, changed):
        if (new and
            (self.pointed == get_id(peer)) and
            (changed.get('can_self_unmute', {}) == {
                "old": True, "new": False
            })
        ):
            log.info("Revoke pointed")
            self.pointed == None


state = State()


async def id_to_name(client:Client, user_list:list) -> list:
    members = []

    for user in await client.get_users(user_list):
        username = (
            f"{user.first_name}_"
            f"{user.last_name if user.last_name else ''}"
        )
        members.append(username)

    return members


async def name_to_id(client:Client, name) -> list:
    members = []

    for user in await client.get_users(state.members):
        username = (
            f"{user.first_name}_"
            f"{user.last_name if user.last_name else ''}"
        )
        if name == username:
            return user.id

    return None


@group_call.on_network_status_changed
async def on_network_changed(_, is_connected):
    log.info('Successfully joined!' if is_connected else 'Disconnected from voice chat..')


@group_call.on_participant_list_updated
async def on_participant_updated(_, participants):
    for participant in participants:
        await state.update(group_call.client, participant)


@app.on_message(filters.command('id'))
async def join_handler(client, message):
    await client.delete_messages(message.chat.id, message.message_id)
    await client.send_message(message.chat.id, f"ID: {message.chat.id}")


if __name__ == "__main__":
    app.run()

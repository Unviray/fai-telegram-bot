import os
import asyncio
import logging

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
        user_id = participant.peer.user_id

        if participant.left:
            self.members[user_id] = None
        else:
            # if not First created
            if self.members.get(user_id, None) is not None:
                changed = compare(self.members[user_id], participant)
            else:
                changed = {
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
        if old is not None:
            log.info(f"{peer.user_id}: lower hand")
            self.raised_hand_members.remove(peer.user_id)

            if changed.get('can_self_unmute', {}) == {
                "old": False, "new": True
            }:
                if self.pointed is None:
                    log.debug(f"{peer.user_id}: pointed")
                    self.pointed = peer.user_id

                for member in self.raised_hand_members:
                    input_peer = await client.resolve_peer(member)

                    # Unraise hand
                    await group_call.edit_group_call_member(input_peer, muted=False)
                    await group_call.edit_group_call_member(input_peer, muted=True)

        else:
            log.info(f"{peer.user_id}: raise hand")
            self.raised_hand_members.append(peer.user_id)

    async def muted_handler(self, client, peer, old, new, changed):
        if (new and
            (self.pointed == peer.user_id) and
            (changed.get('can_self_unmute', {}) == {
                "old": True, "new": False
            })
        ):
            log.info("Revoke pointed")
            self.pointed == None



state = State()


@group_call.on_network_status_changed
async def on_network_changed(_, is_connected):
    log.info('Successfully joined!' if is_connected else 'Disconnected from voice chat..')


@group_call.on_participant_list_updated
async def on_participant_updated(_, participants):
    for participant in participants:
        await state.update(group_call.client, participant)


@state.on_changed(["raise_hand_rating"])
async def raise_hand_handler(client, peer, old, new, changed):
    # Auto unmute If member raise hand
    # if isinstance(new, int):
    #     await group_call.edit_group_call_member(
    #         await client.resolve_peer(peer.user_id),
    #         muted=False
    #     )
    pass


@app.on_message(filters.command('count'))
async def count_handler(client, message):
    await client.delete_messages(message.chat.id, message.message_id)
    result = 0
    no_result = 0
    for member in state.members:
        try:
            if state.members[member] is not None:
                result += int(state.members[member]["about"])
        except ValueError:
            no_result += 1
        except TypeError:
            no_result += 1

    await client.send_message(state.chat_id,
        f"Isa: {result}\n"
        f"Tsy Nandefa isa: {no_result}"
    )


@app.on_message(filters.command('point'))
async def join_handler(client, message):
    await client.send_message(message.chat.id, message.chat.id)
    log.info(await client.get_users(message.command[1]))
    # await client.delete_messages(message.chat.id, message.message_id)
    # input_peer = await client.resolve_peer(message.command[1])

    # await group_call.edit_group_call_member(input_peer, muted=False)


def main():
    app.run()


if __name__ == "__main__":
    app.run()

import os

from icecream import ic

from pyrogram import Client, filters
from pytgcalls import GroupCallFactory
from dotenv import load_dotenv


load_dotenv()

app = Client('fai', os.environ["API_ID"], os.environ["API_HASH"])
group_call = GroupCallFactory(app).get_file_group_call()


def compare(old, new):
    result = {}

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

        ic(participant.peer, changed)

        await self._trigger_change(client, participant.peer, changed)

        return changed

    def on_changed(self, changes:list):
        def decorator(func):
            for change in changes:
                if self.handlers.get(change, None) is None:
                    self.handlers[change] = [func]
                else:
                    self.handlers[change].append(func)

        return decorator

    async def _trigger_change(self, client, peer, changed):
        for key in changed:
            if self.handlers.get(key, None) is not None:
                for func in self.handlers[key]:
                    await func(
                        client,
                        peer=peer,
                        old=changed[key]["old"],
                        new=changed[key]["new"],
                        changed=changed
                    )

    async def raise_hand_handler(self, client, peer, old, new, changed):
        if new is None:
            self.raised_hand_members.remove(peer.user_id)

            if changed.get('can_self_unmute', {}) == {
                "old": False, "new": True
            }:
                if self.pointed is None:
                    self.pointed = peer.user_id

                for member in self.raised_hand_members:
                    input_peer = await client.resolve_peer(member)

                    # Unraise hand
                    await group_call.edit_group_call_member(input_peer, muted=False)
                    await group_call.edit_group_call_member(input_peer, muted=True)

        else:
            self.raised_hand_members.append(peer.user_id)

    async def muted_handler(self, client, peer, old, new, changed):
        if new and (self.pointed == peer.user_id):
            self.pointed == None



state = State()


@group_call.on_network_status_changed
async def on_network_changed(_, is_connected):
    if is_connected:
        await app.send_message(state.chat_id, 'Successfully joined!')
    else:
        await app.send_message(state.chat_id, 'Disconnected from voice chat..')


@group_call.on_participant_list_updated
async def on_participant_updated(_, participants):
    for participant in participants:
        user_id = participant.peer.user_id

        # ic(user_id)
        changed = await state.update(group_call.client, participant)
        # {'can_self_unmute': (False, True), 'raise_hand_rating': (4294988038, None)}
        # pointed = (
        #     (changed.get('can_self_unmute', {}) == {"old": False, "new": True}) and
        #     (isinstance(changed.get('raise_hand_rating', {}).get("old", None), int)) and
        #     (not isinstance(changed.get('raise_hand_rating', {}).get("New", 0), int))
        # )
        # ic(changed)
        # ic(pointed)


@state.on_changed(["raise_hand_rating"])
async def raise_hand_handler(client, peer, old, new, changed):
    # Auto unmute If member raise hand
    # if isinstance(new, int):
    #     await group_call.edit_group_call_member(
    #         await client.resolve_peer(peer.user_id),
    #         muted=False
    #     )
    pass



@app.on_message(filters.command('join'))
async def join_handler(client, message):
    state.chat_id = message.chat.id
    await group_call.start(state.chat_id)


@app.on_message(filters.command('raised'))
async def raised_handler(client, message):
    ic(state.handlers)
    await app.send_message(
        state.chat_id,
        state.raised_hand_members
    )


@app.on_message(filters.command('count'))
async def count_handler(client, message):
    result = 0
    for member in state.members:
        try:
            result += int(state.members[member]["about"])
        except ValueError:
            pass
        except TypeError:
            pass

    await client.send_message(state.chat_id, f"Isa: {result}")


@app.on_message(filters.command('point'))
async def join_handler(client, message):
    input_peer = await client.resolve_peer(message.command[1])

    await group_call.edit_group_call_member(input_peer, muted=False)



@app.on_message(filters.command('down'))
async def mute_handler(client, message):
    for member in state.members:
        input_peer = await client.resolve_peer(member)

        # Unraise hand
        await group_call.edit_group_call_member(input_peer, muted=False)
        await group_call.edit_group_call_member(input_peer, muted=True)


app.run()

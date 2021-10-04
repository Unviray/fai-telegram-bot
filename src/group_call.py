import os

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

    def update(self, participant):
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
                "min": participant.min,
                "muted_by_you": participant.muted_by_you,
                "volume_by_admin": participant.volume_by_admin,
                "is_self": participant.is_self,
                "video_joined": participant.video_joined,
                "active_date": participant.active_date,
                "volume": participant.volume,
                "about": participant.about,
                "raise_hand_rating": participant.raise_hand_rating,
            }

        return changed

state = State()


@group_call.on_network_status_changed
async def on_network_changed(client, is_connected):
    if is_connected:
        await app.send_message(state.chat_id, 'Successfully joined!')
    else:
        await app.send_message(state.chat_id, 'Disconnected from voice chat..')


@group_call.on_participant_list_updated
async def on_participant_updated(client, participants):
    for participant in participants:
        user_id = participant.peer.user_id

        print(user_id)
        changed = state.update(participant)
        # {'can_self_unmute': (False, True), 'raise_hand_rating': (4294988038, None)}
        # pointed = (
        #     (changed.get('can_self_unmute', None) == (False, True)) and
        #     (changed.get('raise_hand_rating', [None, None])[0] > 0)
        # )
        print("----")


@app.on_message(filters.command('join'))
async def join_handler(client, message):
    state.chat_id = message.chat.id
    await group_call.start(state.chat_id)


@app.on_message(filters.command('down'))
async def mute_handler(client, message):
    for member in state.members:
        input_peer = await client.resolve_peer(member)

        # Unraise hand
        await group_call.edit_group_call_member(input_peer, muted=False)
        await group_call.edit_group_call_member(input_peer, muted=True)


app.run()

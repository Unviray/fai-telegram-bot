import re
import asyncio
from functools import partial, wraps
from typing import List

from pytgcalls.exceptions import GroupCallNotFoundError

from main import log, state, group_call, id_to_name, name_to_id


class Commands:
    def __init__(self, client):
        self.client = client
        self.joinned = False
        self.command_mute = partial(self.command_mic_member, False)
        self.command_unmute = partial(self.command_mic_member, True)

        self.command_m = self.command_mute
        self.command_um = self.command_unmute

    def need_joinned(func):
        @wraps(func)
        async def wraped(self, *args, **kwargs):
            if self.joinned:
                return await func(self, *args, **kwargs)
            else:
                log.error("Join a group call first")

        return wraped

    async def command_join(self, group_id:int) -> bool:
        log.info(f"Joinning {group_id}")
        state.chat_id = int(group_id)
        # await group_call.start(state.chat_id, join_as=state.chat_id)
        try:
            await group_call.start(state.chat_id)
            self.joinned = True
        except GroupCallNotFoundError:
            self.joinned = False

        return self.joinned

    @need_joinned
    async def command_mic(self, activate:bool):
        if activate:
            log.info("Activating mic")
        else:
            log.info("Deactivating mic")

        await group_call.set_is_mute(not activate)

    @need_joinned
    async def command_raised(self) -> List[str]:
        raised_hand_members = await id_to_name(self.client, state.raised_hand_members)

        log.info(f"{len(raised_hand_members)} raise hand")
        if len(raised_hand_members) > 0:
            log.info("\n".join(raised_hand_members))

        return raised_hand_members

    @need_joinned
    async def command_unraise(self, username:str):
        member = await name_to_id(self.client, username)
        input_peer = await self.client.resolve_peer(member)

        await group_call.edit_group_call_member(input_peer, muted=False)
        await group_call.edit_group_call_member(input_peer, muted=True)

    @need_joinned
    async def command_members(self) -> List[str]:
        members = await id_to_name(self.client, state.members)

        log.info(f"{len(members)} members")
        if len(members) > 0:
            log.info("\n".join(members))

        return members

    @need_joinned
    async def command_count(self, send:bool=False) -> dict:
        result = 0
        no_result_names = []
        for member in state.members:
            try:
                if state.members[member] is not None:
                    found = re.search(r"(\d+)", state.members[member]["about"])
                    result += int(found.group(0))

            except ValueError:
                no_result_names.append((await id_to_name(self.client, [member]))[0])

            except TypeError:
                no_result_names.append((await id_to_name(self.client, [member]))[0])

        string_result = (
            f"Isa: {result}\n"
            f"Tsy Nandefa isa: {len(no_result_names)}"
        )

        if len(no_result_names) > 0:
            string_result += f"\n\nIreto avy no tsy nandefa isa:"
            try:
                for name in no_result_names:
                    string_result += f"\n - {name}"
            except Exception as e:
                log.error(e)

        log.info(string_result)

        if send:
            await self.client.send_message(
                state.chat_id,
                string_result
            )

        return {
            "number": result,
            "no_result_names": no_result_names,
        }


    @need_joinned
    async def command_mic_member(self, activate:bool, username:str):
        if username in ["*", "all"]:
            username = "all members"

        if activate:
            log.info(f"Activating mic of {username}")
        else:
            log.info(f"Deactivating mic of {username}")

        if username == "all members":
            tasks = []

            for member in state.members:
                tasks.append(asyncio.ensure_future(
                    self.command_mic_member(
                        activate,
                        member
                    )
                ))

            await asyncio.gather(*tasks)
        else:
            if isinstance(username, str):
                user_id = await name_to_id(self.client, username)
            else:
                user_id = username

            input_peer = await self.client.resolve_peer(user_id)

            await group_call.edit_group_call_member(input_peer, muted=(not activate))

    async def command_exit(self, *args):
        return "exit"

    command_quit = command_exit

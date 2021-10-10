import os
import sys
import asyncio
from functools import partial

import nest_asyncio
from rich.traceback import install
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import NestedCompleter, WordCompleter

from main import log, group_call, state, app

install(show_locals=True)
nest_asyncio.apply()


async def id_to_name(client, user_list:list) -> list:
    members = []

    for member in user_list:
        user = await client.get_users(member)
        username = (
            f"{user.first_name}_"
            f"{user.last_name if user.last_name else ''}"
        )
        members.append(username)

    return members


async def name_to_id(client, name) -> list:
    members = []

    for member in state.members:
        user = await client.get_users(member)
        username = (
            f"{user.first_name}_"
            f"{user.last_name if user.last_name else ''}"
        )
        if name == username:
            return member

    return None


def arg_parse(arg):
    if arg.lower() in ["0", "off", "false", "n", "no"]:
        return False
    elif arg.lower() in ["1", "on", "true", "y", "yes"]:
        return True

    try:
        return int(arg)
    except ValueError:
        pass

    return arg


def member_completer(client, user_list):
    def completer():
        return asyncio.run(id_to_name(client, user_list))

    return completer


class Commands:
    def __init__(self, client):

        self.session = PromptSession(completer=NestedCompleter.from_nested_dict({
            'join': None,
            'mic': {'on', 'off'},
            'mic_member': {
                'on': WordCompleter(member_completer(client, state.members)),
                'off': WordCompleter(member_completer(client, state.members))
            },
            'raised': None,
            'members': None,
            'count': {'on', 'off'},
            'mute': WordCompleter(member_completer(client, state.members)),
            'unmute': WordCompleter(member_completer(client, state.members)),
            'exit': None,
            'quit': None,
        }))

        self.command_mute = partial(self.command_mic_member, False)
        self.command_unmute = partial(self.command_mic_member, True)

    async def command_join(self, group_id:int):
        log.info(f"Joinning {group_id}")
        state.chat_id = int(group_id)
        await group_call.start(state.chat_id)

    async def command_mic(self, activate:bool):
        if activate:
            log.info("Activating mic")
        else:
            log.info("Deactivating mic")

        await group_call.set_is_mute(not activate)

    async def command_raised(self):
        raised_hand_members = await id_to_name(self.client, state.raised_hand_members)

        log.info(f"{len(raised_hand_members)} raise hand")
        if len(raised_hand_members) > 0:
            log.info("\n".join(raised_hand_members))

    async def command_members(self):
        members = await id_to_name(self.client, state.members)

        log.info(f"{len(members)} members")
        if len(members) > 0:
            log.info("\n".join(members))

    async def command_count(self, send:bool=False):
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

        string_result = (
            f"Isa: {result}\n"
            f"Tsy Nandefa isa: {no_result}"
        )

        log.info(string_result)

        if send:
            await self.client.send_message(
                state.chat_id,
                string_result
            )

    async def command_mic_member(self, activate:bool, username:str):
        user_id = await name_to_id(self.client, username)
        input_peer = await self.client.resolve_peer(user_id)

        await group_call.edit_group_call_member(input_peer, muted=(not activate))

    async def command_exit(self, *args):
        return "exit"

    command_quit = command_exit


class Cli(Commands):
    def __init__(self, client):
        self.client = client
        super(Cli, self).__init__(self.client)

    async def get_input(self):
        try:
            with patch_stdout(True):
                return (await self.session.prompt_async("> ")).split(" ")
        except EOFError:
            return ["exit"]
        except KeyboardInterrupt:
            return ["exit"]

    async def process_input(self, command):
        if (len(command) > 0) and (command != [""]):
            cmd = command.pop(0)
            try:
                func = getattr(self, f"command_{cmd}")

                command = list(map(arg_parse, command))
                try:
                    return await func(*command)
                except Exception as e:
                    log.error(e)
            except AttributeError:
                log.error(f"command {cmd} not found")

            print()

    async def run(self, auto_join=True):
        if auto_join:
            await self.process_input(["join", os.environ["GROUP_ID"]])

        while True:
            command = await self.get_input()
            result = await self.process_input(command)
            if result == "exit":
                break


async def main():
    cli = Cli(app)
    await cli.run()
    # cli = Cli(None)
    # await cli.run()


if __name__ == "__main__":
    with app:
        asyncio.run(main())

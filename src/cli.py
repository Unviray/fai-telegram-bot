import os
import asyncio

import nest_asyncio
from rich.traceback import install
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import NestedCompleter, WordCompleter

from main import log, state, app, id_to_name
from controller import Commands

install(show_locals=True)
nest_asyncio.apply()


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


class Cli(Commands):
    def __init__(self, client):
        self.client = client

        MemberCompeter = WordCompleter(member_completer(client, state.members))

        self.session = PromptSession(completer=NestedCompleter.from_nested_dict({
            'join': None,
            'mic': {'on', 'off'},
            'mic_member': {
                'on': MemberCompeter,
                'off': MemberCompeter
            },
            'mute': MemberCompeter,
            'unmute': MemberCompeter,
            'm': MemberCompeter,
            'um': MemberCompeter,
            'raised': None,
            'unraise': MemberCompeter,
            'members': None,
            'count': {'on', 'off'},
            'exit': None,
            'quit': None,
        }))

        super(Cli, self).__init__(self.client)

    async def get_input(self):
        try:
            with patch_stdout(raw=True):
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
            joinned = await self.process_input(["join", os.environ["GROUP_ID"]])

            if joinned:
                await self.process_input(["mic", "off"])

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

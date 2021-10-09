import sys
import asyncio

import nest_asyncio
from prompt_toolkit import PromptSession
from rich.traceback import install

from main import log, group_call, state, app

install(show_locals=True)
nest_asyncio.apply()


class Commands:
    async def command_join(self, group_id:int):
        log.info(f"Joinning {group_id}")
        state.chat_id = int(group_id)
        await group_call.start(state.chat_id)

    async def command_members(self):
        members = [member for member in state.members]
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

    async def command_exit(self, *args):
        sys.exit(0)

    command_quit = command_exit


class Cli(Commands):
    session = PromptSession()

    def __init__(self, client):
        self.client = client

    async def get_input(self):
        try:
            return self.session.prompt("> ").split(" ")
        except EOFError:
            return ["exit"]
        except KeyboardInterrupt:
            return ["exit"]

    async def process_input(self, command):
        if (len(command) > 0) and (command != [""]):
            try:
                func = getattr(self, f"command_{command[0]}")
                try:
                    await func(*command[1:])
                except Exception as e:
                    log.error(e)
            except AttributeError:
                log.error(f"command {command[0]} not found")

            print()

    async def run(self):
        while True:
                command = await self.get_input()
                await self.process_input(command)


async def main():
    cli = Cli(app)
    await cli.run()
    # cli = Cli(None)
    # await cli.run()


if __name__ == "__main__":
    with app:
        asyncio.run(main())

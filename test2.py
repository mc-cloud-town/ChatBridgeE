import asyncio

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import CompleteStyle

from server import Server, init_logging

init_logging()

ser = Server()

ser.load_plugin("plugins", recursive=True)

ser.add_command("add plugin")
ser.add_command("add plug")


async def prompt_align():
    session = PromptSession(
        complete_style=CompleteStyle.MULTI_COLUMN,
        complete_in_thread=True,
        complete_while_typing=True,
        reserve_space_for_menu=3,
    )

    while True:
        result: str = (
            await session.prompt_async(
                "> ",
                completer=WordCompleter(ser.commands),
                complete_while_typing=True,
                auto_suggest=AutoSuggestFromHistory(),
            )
            or ""
        )
        ser.dispatch("console_input", result.split())


async def main():
    task1 = asyncio.create_task(prompt_align())
    task2 = asyncio.create_task(ser.start())

    with patch_stdout():
        await asyncio.gather(task1, task2)


asyncio.run(main())

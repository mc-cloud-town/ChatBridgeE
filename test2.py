import asyncio

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from server import Server, init_logging

init_logging()

ser = Server()

ser.load_plugin("plugins", recursive=True)


async def prompt_align():
    session = PromptSession()
    html_completer = WordCompleter(ser.commands)

    while True:
        result = await session.prompt_async(
            "> ",
            completer=html_completer,
            complete_while_typing=True,
            auto_suggest=AutoSuggestFromHistory(),
        )
        ser.dispatch("console_input", result)


async def main():
    task1 = asyncio.create_task(prompt_align())
    task2 = asyncio.create_task(ser.start())

    with patch_stdout():
        await asyncio.gather(task1, task2)


asyncio.run(main())

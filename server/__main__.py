import asyncio

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import CompleteStyle

from . import Server, init_logging
from .core.command import CommandCompleter


def main():
    init_logging()

    ser = Server()

    ser.load_plugin("plugins", recursive=True)

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
                    completer=CommandCompleter(ser.command_manager),
                    complete_while_typing=True,
                    auto_suggest=AutoSuggestFromHistory(),
                )
                or ""
            )
            ser.command_manager.call_command(result)

    async def main():
        with patch_stdout(raw=True):
            await asyncio.gather(
                asyncio.create_task(prompt_align()),
                asyncio.create_task(ser.start()),
            )

    asyncio.run(main())


if __name__ == "__main__":
    main()

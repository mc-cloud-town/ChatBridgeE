import asyncio
import platform

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import CompleteStyle

from . import Server, init_logging
from .core.command import CommandCompleter


def main():
    log = init_logging()
    log.info(
        f"[red]python version: [/red][cyan]{platform.python_version()}[/cyan]",
        extra=dict(markup=True),
    )

    ser = Server()
    ser.load_plugin(
        "plugins",
        block_plugin=ser.config.get("stop_plugins"),
    )

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

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        with patch_stdout(raw=True):
            loop.create_task(prompt_align())
            loop.create_task(ser.start())

        loop.run_forever()
    except KeyboardInterrupt:
        ser.log.info("[red]關閉中請稍後...[/red]", extra=dict(markup=True))
        for name in ser.plugins.copy().keys():
            ser.remove_plugin(name)


if __name__ == "__main__":
    main()

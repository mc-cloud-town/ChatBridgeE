from typing import TYPE_CHECKING, Any, Iterable, Optional, Union

from prompt_toolkit.completion import CompleteEvent, Completion, WordCompleter
from prompt_toolkit.document import Document

if TYPE_CHECKING:
    from . import BaseServer

__all__ = ("CommandCompleter", "CommandManager")


class CommandCompleter(WordCompleter):
    def __init__(self, command_manager: "CommandManager", **kwargs: Any) -> None:
        self.command_manager = command_manager

        super().__init__([], sentence=True, **kwargs)

    def get_completions(
        self,
        document: Document,
        complete_event: CompleteEvent,
    ) -> Iterable[Completion]:
        self.words = self.command_manager.words
        self.display_dict = self.command_manager.display_dict

        return super().get_completions(document, complete_event)


class CommandManager:
    def __init__(self, server: "BaseServer") -> None:
        self.server = server
        self.commands: dict[str, Optional[str]] = {}  # {name: display}

    def add_command(self, name: str, display: Optional[str] = None) -> None:
        self.commands[name] = display

    def add_commands(
        self,
        commands: Union[dict[str, Optional[str]], tuple[str]],
    ) -> None:
        self.commands.update(
            {command: None for command in commands}  # from tuple to dict
            if isinstance(commands, tuple)
            else commands  # is dict
        )

    def remove_command(self, *names: str) -> None:
        for name in names:
            self.commands.pop(name, None)

    def call_command(self, name: str) -> None:
        split = name.split()
        base = ""
        for k in sorted(self.commands.keys(), key=lambda x: len(x)):
            if name.startswith(k):
                base = k
                break

        if not base:
            print(f"未知指令: {name}")
            return

        self.server.dispatch(
            f"command_{base.replace(' ', '_')}",
            *split[len(base.split()) :],
        )

    @property
    def words(self) -> list[str]:
        return self.commands.keys()

    @property
    def display_dict(self) -> dict[str, Optional[str]]:
        return self.commands

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

    def add_commands(self, commands: Union[dict[str, Optional[str]], set[str]]) -> None:
        self.commands.update(
            {command: None for command in commands}  # from set to dict
            if isinstance(commands, set)
            else commands  # is dict
        )

    def remove_command(self, name: str) -> Optional[str]:
        return self.commands.pop(name, None)

    def call_command(self, name: str) -> None:
        split = name.split()
        self.server.dispatch(f"command_{split}", *split)

    @property
    def words(self) -> list[str]:
        return self.commands.keys()

    @property
    def display_dict(self) -> dict[str, Optional[str]]:
        return self.commands

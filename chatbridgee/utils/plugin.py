from typing import TYPE_CHECKING

from chatbridgee.utils.events import Events


if TYPE_CHECKING:
    from chatbridgee.server.server import Server


class Plugin(Events):
    def __init__(self, name: str) -> None:
        self.name = name

    def _inject(self, server: "Server") -> None:
        try:
            self.plugin_load()
        except Exception:
            pass

    def _eject(self, server: "Server") -> None:
        try:
            self.plugin_unload()
        except Exception:
            pass

    def plugin_unload(self) -> None:
        """plugin unload event for this plugin"""
        pass

    def plugin_load(self) -> None:
        """plugin load event for this plugin"""
        pass

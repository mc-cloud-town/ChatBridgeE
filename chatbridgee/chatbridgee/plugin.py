from abc import ABC

from mcdreforged.api.all import (
    PluginServerInterface,
    RColor,
    RText,
    RTextBase,
    ServerInterface,
)

from .config import ChatBridgeEConfig
from .utils import Client

META = ServerInterface.get_instance().as_plugin_server_interface().get_self_metadata()


def tr(key: str, *args, **kwargs) -> RTextBase:
    return ServerInterface.get_instance().rtr(f"{META.id}.{key}", *args, **kwargs)


class BasePlugin(ABC):
    def __init__(
        self,
        server: PluginServerInterface,
        sio: Client,
        config: ChatBridgeEConfig,
    ) -> None:
        self.server = server
        self.config = config
        self.sio = sio
        self.log = server.logger

        self.setup()

    def setup(self) -> None:
        pass

    def say(self, msg: str) -> None:
        self.server.broadcast(msg)

    def from_server(
        self,
        server_name: str,
        msg: str,
        *,
        set_start: bool = True,
        color: RColor = RColor.gray,
    ) -> None:
        if set_start:
            msg = f"[{server_name}] {msg}"

        self.say(RText(msg, color=color))

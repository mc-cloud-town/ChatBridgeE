import socketio
from mcdreforged.api.all import PluginServerInterface

from .config import ChatBridgeEConfig


class ReadClient:
    def __init__(
        self,
        server: PluginServerInterface,
        sio: socketio.Client,
        config: ChatBridgeEConfig,
    ) -> None:
        self.server = server
        self.config = config
        self.sio = sio

        self.sio.on("chat", self.on_chat)
        self.sio.on("new_connect", self.on_new_connect)
        self.sio.on("new_disconnect", self.on_new_disconnect)
        self.sio.on("server_start", self.on_server_start)
        self.sio.on("server_startup", self.on_server_startup)
        self.sio.on("server_stop", self.on_server_stop)
        self.sio.on("player_chat", self.on_player_chat)
        self.sio.on("player_joined", self.on_player_joined)
        self.sio.on("player_left", self.on_player_left)

    def on_chat(self, *args, **kwargs):
        print(args, kwargs)

    def on_new_connect(self, *args, **kwargs) -> None:
        print(args, kwargs)

    def on_new_disconnect(self, *args, **kwargs) -> None:
        print(args, kwargs)

    def on_server_start(self, *args, **kwargs) -> None:
        print(args, kwargs)

    def on_server_startup(self, *args, **kwargs) -> None:
        print(args, kwargs)

    def on_server_stop(self, *args, **kwargs) -> None:
        print(args, kwargs)

    def on_player_chat(self, *args, **kwargs) -> None:
        print(args, kwargs)

    def on_player_joined(self, *args, **kwargs) -> None:
        print(args, kwargs)

    def on_player_left(self, *args, **kwargs) -> None:
        print(args, kwargs)

        # , ctx.display_name
        # , ctx.display_name
        # , ctx.display_name
        # , ctx.display_name
        # , ctx.display_name
        # , [ctx.display_name, player_name, content]
        # , ctx.display_name, player_name
        # , ctx.display_name, player_name

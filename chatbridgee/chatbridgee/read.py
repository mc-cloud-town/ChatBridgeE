import socketio
from mcdreforged.api.all import PluginServerInterface, RText, RColor

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
        # self.sio.on("new_connect", self.on_new_connect)
        # self.sio.on("new_disconnect", self.on_new_disconnect)
        # self.sio.on("server_startup", self.on_server_startup)
        self.sio.on("server_start", self.on_server_start)
        self.sio.on("server_stop", self.on_server_stop)
        self.sio.on("player_chat", self.on_player_chat)
        self.sio.on("player_joined", self.on_player_joined)
        self.sio.on("player_left", self.on_player_left)

    def say(self, msg: str) -> None:
        self.server.say(msg)

    def on_chat(self, *args, **kwargs):
        print(args, kwargs)

    # def on_new_connect(self, server_name: str) -> None:
    #     print(server_name)

    # def on_new_disconnect(self, server_name: str) -> None:
    #     print(server_name)

    # def on_server_startup(self, server_name: str) -> None:
    #     self.from_server(server_name, "啟動中...")

    def on_server_start(self, server_name: str) -> None:
        self.from_server(server_name, "啟動完成")

    def on_server_stop(self, server_name: str) -> None:
        self.from_server(server_name, "停止")

    def on_player_chat(self, server_name: str, player_name: str, content: str) -> None:
        self.from_server(server_name, f"<{player_name}> {content}")

    def on_player_joined(self, server_name: str, player_name: str) -> None:
        self.from_server(
            server_name,
            f"{player_name} 加入了 {server_name}",
            set_start=False,
        )

    def on_player_left(self, server_name: str, player_name: str) -> None:
        self.from_server(
            server_name,
            f"{player_name} 離開了 {server_name}",
            set_start=False,
        )

    def from_server(
        self,
        server_name: str,
        msg: str,
        *,
        set_start: bool = True,
    ) -> None:
        if set_start:
            msg = f"[{server_name}] {msg}"

        self.say(RText(msg, color=RColor.gray))

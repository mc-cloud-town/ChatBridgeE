from typing import Optional

import socketio
from mcdreforged.api.all import PluginServerInterface, RColor, RText

from .config import ChatBridgeEConfig


class RTextJSON(RText):
    def __init__(self, data) -> None:
        self.data = data

    def to_json_object(self) -> str:
        if isinstance(self.data, dict):
            return self.data.get("mc", {})
        return {}

    def to_plain_text(self) -> str:
        if isinstance(self.data, dict):
            return self.data.get("ansi", "")
        return ""


# TODO add format event data from config
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
        self.sio.on("server_startup", self.on_server_startup)
        self.sio.on("server_start", self.on_server_start)
        self.sio.on("server_stop", self.on_server_stop)
        self.sio.on("player_chat", self.on_player_chat)
        self.sio.on("player_joined", self.on_player_joined)
        self.sio.on("player_left", self.on_player_left)

    def say(self, msg: str) -> None:
        self.server.say(msg)

    def on_chat(self, server_name: str, msg: dict):
        data = RTextJSON(msg)

        self.server.say(data)
        print(data.to_plain_text())

    # def on_new_connect(self, server_name: str) -> None:
    #     print(server_name)

    # def on_new_disconnect(self, server_name: str) -> None:
    #     print(server_name)

    def on_server_startup(self, server_name: str) -> None:
        self.from_server(server_name, "啟動中...")

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

    # stats:
    #   success>
    #     code: 0
    #   unknown stat>
    #     code: 1
    #   no stats_helper>
    #     code: 2
    #
    # <unknown command>
    #   code: -1
    def on_command(self, command: str):
        if command.startswith("!!stats "):
            try:
                import stats_helper  # pyright: ignore
            except (ImportError, ModuleNotFoundError):
                result = {"code": 2}
            else:
                try:
                    _, type, cls, target = (
                        command.replace("-bot", "").replace("-all", "").split()
                    )
                except:  # noqa: E722
                    res_raw: Optional[str] = None
                else:
                    res_raw = stats_helper.show_rank(
                        self.server.get_plugin_command_source(),
                        cls,
                        target,
                        list_bot="-bot" in command,
                        is_tell=False,
                        is_all="-all" in command,
                        is_called=True,
                    )

                if res_raw is not None:
                    lines = res_raw.splitlines()
                    result = {
                        "code": 0,
                        "stats_name": lines[0],
                        "data": lines[1:-1],
                        "total": int(lines[-1].split(" ")[1]),
                    }
                else:
                    result = {"code": 1}

        self.sio.call("command_callback", result)

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

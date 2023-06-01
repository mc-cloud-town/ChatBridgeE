from typing import Optional

from mcdreforged.api.all import RText

from .plugin import BasePlugin


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
class ReadClient(BasePlugin):
    def setup(self) -> None:
        self.sio.on("chat", self.on_chat)
        # self.sio.on("new_connect", self.on_new_connect)
        # self.sio.on("new_disconnect", self.on_new_disconnect)
        self.sio.on("server_startup", self.on_server_startup)
        self.sio.on("server_start", self.on_server_start)
        self.sio.on("server_stop", self.on_server_stop)
        self.sio.on("player_chat", self.on_player_chat)
        self.sio.on("player_joined", self.on_player_joined)
        self.sio.on("player_left", self.on_player_left)
        self.sio.on("extra_command", self.on_extra_command)

    async def on_chat(self, msg: dict) -> None:
        data = RTextJSON(msg)

        self.server.say(data)
        print(data.to_plain_text())

    # def on_new_connect(self, server_name: str) -> None:
    #     print(server_name)

    # def on_new_disconnect(self, server_name: str) -> None:
    #     print(server_name)

    async def on_server_startup(self, server_name: str) -> None:
        self.from_server(server_name, "啟動中...")

    async def on_server_start(self, server_name: str) -> None:
        self.from_server(server_name, "啟動完成")

    async def on_server_stop(self, server_name: str) -> None:
        self.from_server(server_name, "伺服器關閉")

    async def on_player_chat(
        self, server_name: str, player_name: str, content: str
    ) -> None:
        self.from_server(server_name, f"<{player_name}> {content}")

    async def on_player_joined(self, server_name: str, player_name: str) -> None:
        self.from_server(
            server_name,
            f"{player_name} 加入了 {server_name}",
            set_start=False,
        )

    async def on_player_left(self, server_name: str, player_name: str) -> None:
        self.from_server(
            server_name,
            f"{player_name} 離開了 {server_name}",
            set_start=False,
        )

    # stats:
    #   success>
    #     code: 0
    #   unknown stats>
    #     code: 1
    #   no stats_helper>
    #     code: 2
    #
    # <unknown command>
    #   code: -1
    async def on_extra_command(self, command: str) -> None:
        result = {"command": command, "code": -1}
        if command.startswith("stats "):
            try:
                import stats_helper  # pyright: ignore
            except (ImportError, ModuleNotFoundError):
                result.update({"code": 2})
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
                    result.update(
                        {
                            "code": 0,
                            "stats_name": lines[0],
                            "data": lines[1:-1],
                            "total": int(lines[-1].split(" ")[1]),
                        }
                    )
                else:
                    result.update({"code": 1})

        self.sio.emit("cmd_callback", result)

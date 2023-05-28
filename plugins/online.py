import re
from typing import overload

from server import BaseServer, Context, Plugin
from server.utils import Config, RconClient

minecraft_list_match = re.compile(
    r"There are \d+ of a max(?: of)? \d+ players online:(.*)"
)
minecraft_GList_match = re.compile(r"\[(.*)\] \(\d*\):((?:.*[ ,]?)+)")


class OnlineConfig(Config):
    online_enabled = True
    query_online_names = ["Survival"]
    bungeecord_list = {
        "BungeecordA": {
            "address": "127.0.0.1",
            "port": 39999,
            "password": "Bungee Rcon Password",
        }
    }


class Online(Plugin, config=OnlineConfig):
    def __init__(self, server: BaseServer) -> None:
        super().__init__(server)
        self._glist_rcon_catch: dict[str, RconClient] = {}

    # <1.16  There are 3 of a max 50 players online: A, B, C
    # >=1.16 There are 3 of a max of 50 players online: A, B, C
    @staticmethod
    def handle_minecraft(data: str) -> set[str]:
        if parsed := minecraft_list_match.match(data):
            return set(filter(bool, parsed.group(1).strip().split(" ")))

        return set()

    # [Creative] (2): A, B
    # [Survival] (4): A, B, C, D
    # Total players online: 6
    @staticmethod
    def handle_bungee(data: str) -> dict[str, set[str]] | None:
        result, no_command = {}, False

        for line in data.splitlines():
            if line.startswith("Total players online:"):
                no_command = True
                continue
            if parsed := minecraft_GList_match.match(data):
                result[parsed.group(1)] = parsed.group(2).strip().split(" ")

        if no_command:
            return None
        return result

    # fmt: off
    @overload
    async def query(self, *, order = True) -> list[tuple[Context, set[str]]]:  ...  # noqa: E
    @overload
    async def query(self, *, order=False) -> dict[Context, set[str]]:  ...  # noqa: E
    # fmt: on

    async def query(self, *, order: bool = False):
        result: dict[Context, set[str]] = {}
        minecraft_GList_match: dict[str, dict] = self.config.get(
            "minecraft_GList_match",
            {},
        )

        for name, server in minecraft_GList_match.items():
            rcon = self._glist_rcon_catch.get(
                name,
                RconClient(
                    host=server.get("address", None),
                    port=server.get("port", None),
                    password=server.get("password", None),
                ),
            )
            self._glist_rcon_catch[name] = rcon
            await rcon.connect()

            if (res := await rcon.execute("glist")) and (
                data := self.handle_bungee(res["data"])
            ):
                for id, value in data.items():
                    result.update({self.server.get_client(id): value})

        for client in self.server.clients.values():
            if res := await client.execute_command("list"):
                result.update({client: self.handle_minecraft(res["data"])})

        if order:
            ret = []
            for id in self.config.get("query_online_names", []):
                for ctx, value in result.copy().items():
                    if id == ctx.user.name:
                        ret.append((ctx, value))
                        result.pop(ctx)
                        break
            return ret

        return {
            k: v
            for k, v in result.items()
            if k.user.name in self.config.get("query_online_names", [])
        }

    def on_unload(self) -> None:
        for client in self._glist_rcon_catch.values():
            client.disconnect()


def setup(server: BaseServer):
    server.add_plugin(Online(server))

import re

from server import BaseServer, Plugin
from server.utils import Config, RconClient

minecraft_list_match = re.compile(
    r"There are \d+ of a max(?: of)? \d+ players online:((?:[a-zA-Z0-9_]*[ ,]?)+)"
)
minecraft_GList_match = re.compile(r"\[(.*)\] \(\d*\):((?:[a-zA-Z0-9_]*[ ,]?)+)")


class OnlineConfig(Config):
    online_enabled = True
    query_online_names = ["Server"]
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
        result = set[str]()

        if parsed := minecraft_list_match.match(data):
            result = set(parsed.group(1).strip().split(" "))

        return result

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

    async def query(self) -> list[str]:
        ...

    async def get_online(self) -> str:
        for client in self.server.clients.values():
            client

    async def connect(self):
        result: dict[str, set[str]] = {}
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

            if res := await rcon.execute("glist"):
                if data := self.handle_bungee(res["data"]):
                    result.update(data)

        for name, client in self.server.clients.items():
            if res := await client.execute_command("list"):
                result.update({name: self.handle_minecraft(res["data"])})

        return {
            k: v
            for k, v in result.items()
            if k in self.config.get("query_online_names", [])
        }

    def on_load(self) -> None:
        self.loop.create_task(self.connect())

    def on_unload(self) -> None:
        for client in self._glist_rcon_catch.values():
            client.disconnect()
        return super().on_unload()


def setup(server: BaseServer):
    server.add_plugin(Online(server))

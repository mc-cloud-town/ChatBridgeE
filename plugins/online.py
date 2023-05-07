from enum import Enum, auto
import re


from server import BaseServer, Plugin
from server.utils import Config


minecraft_list_match = re.compile(
    r"There are \d+ of a max( of)? \d+ players ([a-zA-Z0-9],?)+"
)


class OnlineConfig(Config):
    online_enabled = True
    query_online_names = ["Server"]


class ListCommandType(Enum):
    List = auto()
    GList = auto()


class Online(Plugin, config=OnlineConfig):
    def __init__(self, server: BaseServer):
        super().__init__(server)
        self.server_type: dict[str, ListCommandType] = {}

    @staticmethod
    def handle_minecraft(data: str) -> dict[str, str]:
        # <1.16
        # r"There are \d+ of a max \d+ players ([a-zA-Z0-9],?)+",
        # >=1.16
        # r"There are \d+ of a max of \d+ players ([a-zA-Z0-9],?)+",
        if (parsed := re.search(minecraft_list_match, data)) is not None and parsed[
            "players"
        ].startswith(" "):
            players = parsed["players"][1:]
            # if len(players) > 0:
            #     updater(server.name, players.split(", "))
            # else:
            #     updater(server.name, ())
            # break

    @staticmethod
    def handle_bungee(data: str):
        result = {}
        for line in data.splitlines():
            if not line.startswith("Total players online:"):
                result[line.split("] (", 1)[0][1:]] = line.split("): ")[-1].split(", ")

        if "" in result:
            del result[""]

        return result

    async def query(self) -> list[str]:
        ...

    async def get_online(self) -> str:
        for client in self.server.clients.values():
            client
        ...


def setup(server: BaseServer):
    server.add_plugin(Online(server))

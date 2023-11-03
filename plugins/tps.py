from __future__ import annotations

import re

from server import BaseServer, Plugin
from server.utils import Config

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


class Tps(Plugin, config=OnlineConfig):
    def __init__(self, server: BaseServer) -> None:
        super().__init__(server)


def setup(server: BaseServer):
    server.add_plugin(Tps(server))

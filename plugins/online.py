from server import BaseServer, Plugin
from server.utils import Config


class OnlineConfig(Config):
    online_enabled = True
    query_online_names = ["Server"]


class Online(Plugin, config=OnlineConfig):
    def __init__(self, server: BaseServer):
        super().__init__(server)
        server.clients


def setup(server: BaseServer):
    server.add_plugin(Online(server))

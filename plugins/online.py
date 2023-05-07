from server import BaseServer, Plugin
from server.utils import Config


class OnlineConfig(Config):
    online_enabled = True
    query_online_names = ["Server"]


class Online(Plugin, config=OnlineConfig):
    def __init__(self, server: BaseServer):
        super().__init__(server)

    async def get_online(self) -> str:
        for client in self.server.clients.values():
            client
        ...


def setup(server: BaseServer):
    server.add_plugin(Online(server))

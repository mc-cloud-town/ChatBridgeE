from server import Plugin, Server
from server.utils import Config


class TestConfig(Config):
    token: str = ""


class Test(Plugin, config=TestConfig):
    def on_load(self):
        print("test_load", self.config.get("token"))

    def on_unload(self):
        pass


def setup(server: Server):
    server.add_plugin(Test(server))

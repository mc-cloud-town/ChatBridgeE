from server import Plugin, Server


class Test(Plugin):
    def on_load(self) -> None:
        print("test")


def setup(server: Server):
    server.add_plugin(Test())

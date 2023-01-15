from server import Plugin, Server


class Test(Plugin):
    @Plugin.listener()
    async def on_connect(self, a, b):
        print("----------------------------------------")


def setup(server: Server):
    server.add_plugin(Test())

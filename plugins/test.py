from server import Plugin, BaseServer


class Test(Plugin):
    @Plugin.listener()
    async def on_connect(self, a, b):
        print("----------------------------------------")


def setup(server: BaseServer):
    server.add_plugin(Test())

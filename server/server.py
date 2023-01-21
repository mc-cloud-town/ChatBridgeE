from . import BaseServer, Context

__all__ = ("Server",)


class Server(BaseServer):
    def __init__(self):
        super().__init__()

        self.load_plugin(
            f"{__package__}.base_plugin",
            recursive=True,
            block_plugin=self.config.get("stop_plugins"),
        )

    async def on_ping(self, ctx: Context):
        await ctx.emit("server_pong")

    async def on_connect(self, ctx: Context, auth):
        ...

from . import BaseServer, Context

__all__ = ("Server",)


class Server(BaseServer):
    def __init__(self):
        super().__init__()

        self.load_plugin(
            f"{__package__}.base_plugin",
            recursive=True,
        )

    async def on_ping(self, ctx: Context):
        await ctx.emit("server_pong")

    async def on_connect(self, ctx: Context, auth):
        await ctx.emit("new_connect", ctx.display_name)

    async def on_disconnect(self, ctx: Context):
        await ctx.emit("new_disconnect", ctx.display_name)

    async def on_server_start(self, ctx: Context):
        await ctx.emit("server_start", ctx.display_name)

    async def on_server_startup(self, ctx: Context):
        await ctx.emit("server_startup", ctx.display_name)

    async def on_server_stop(self, ctx: Context):
        await ctx.emit("server_stop", ctx.display_name)

    # TODO send_event("player_chat", {"content": info.content, "player": info.player})
    async def on_player_chat(self, ctx: Context):
        await ctx.emit("player_chat", ctx.display_name)

    async def on_player_joined(self, ctx: Context, player_name: str):
        await ctx.emit("player_joined", ctx.display_name, player_name)

    async def on_player_left(self, ctx: Context, player_name: str):
        await ctx.emit("player_left", ctx.display_name, player_name)

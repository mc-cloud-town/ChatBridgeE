from asyncio import AbstractEventLoop
from . import BaseServer, Context

__all__ = ("Server",)

# TODO use struct data


class Server(BaseServer):
    def __init__(self, loop: AbstractEventLoop | None = None):
        super().__init__(loop=loop)
        self.load_plugin(f"{__package__}.base_plugin")

    async def on_ping(self, ctx: Context):
        await ctx.emit("server_pong")

    async def on_connect(self, ctx: Context, auth):
        await ctx.emit("new_connect", ctx.display_name, skip_sid=ctx.sid)

    async def on_disconnect(self, ctx: Context):
        await ctx.emit("new_disconnect", ctx.display_name, skip_sid=ctx.sid)

    async def on_server_start(self, ctx: Context):
        await ctx.emit("server_start", ctx.display_name, skip_sid=ctx.sid)

    async def on_server_startup(self, ctx: Context):
        await ctx.emit("server_startup", ctx.display_name, skip_sid=ctx.sid)

    async def on_server_stop(self, ctx: Context):
        await ctx.emit("server_stop", ctx.display_name, skip_sid=ctx.sid)

    async def on_player_chat(self, ctx: Context, player_name: str, content: str):
        await ctx.emit(
            "player_chat",
            ctx.display_name,
            player_name,
            content,
            skip_sid=ctx.sid,
        )

    async def on_player_joined(self, ctx: Context, player_name: str):
        await ctx.emit("player_joined", ctx.display_name, player_name, skip_sid=ctx.sid)

    async def on_player_left(self, ctx: Context, player_name: str):
        await ctx.emit("player_left", ctx.display_name, player_name, skip_sid=ctx.sid)

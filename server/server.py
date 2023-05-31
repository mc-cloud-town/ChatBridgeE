import sys
from asyncio import AbstractEventLoop
from pathlib import Path

from . import BaseServer, Context
from .utils import FileEncode

__all__ = ("Server",)


class Server(BaseServer):
    def __init__(self, loop: AbstractEventLoop | None = None):
        super().__init__(loop=loop)

        from .base_plugin import setup as base_setup

        base_setup(self)

        path = Path(self.config.get("plugins_path"))
        sys.path.append(str(path.parent.absolute()))
        for file in path.glob("[!_]*"):
            if self.setup_from_name(file).name in self.config.get("stop_plugins"):
                continue

            self.load_extension(file)

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

    async def on_file_sync(self, ctx: Context, raw_data: bytes):
        data = FileEncode.decode(raw_data)
        data.server_name = ctx.display_name

        await ctx.emit("file_sync", data, skip_sid=ctx.sid)

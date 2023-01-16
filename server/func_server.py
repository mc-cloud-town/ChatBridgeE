from . import BaseServer, Context


class Server(BaseServer):
    async def on_ping(self, ctx: Context):
        await ctx.emit("server_pong")

    async def on_connect(self, ctx: Context, auth):
        print(auth, type(auth))
        ...

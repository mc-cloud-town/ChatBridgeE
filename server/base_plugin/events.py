import logging

from .. import BaseServer, Context, Plugin

log = logging.getLogger("chat-bridgee")


class BasePlugin_Events(Plugin):
    @Plugin.listener()
    async def on_connect(self, ctx: Context):
        log.info(f"{ctx.sid} 以連接")

    @Plugin.listener()
    async def on_message(self, ctx: Context, msg: str):
        log.info(f"{ctx.sid} 發送了訊息: {msg}")

    @Plugin.listener()
    async def on_disconnect(self, ctx: Context):
        log.info(f"{ctx.sid} 以斷開")


def setup(server: "BaseServer") -> None:
    server.add_plugin(BasePlugin_Events(server))

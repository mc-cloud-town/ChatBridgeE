import logging

from .. import BaseServer, Context, Plugin
from .__base import BasePlugin

log = logging.getLogger("chat-bridgee")


class BasePlugin_Events(BasePlugin, description="事件日誌"):
    @Plugin.listener()
    async def on_connect(self, ctx: Context):
        log.info(f"{ctx.sid} 以連接")

    @Plugin.listener()
    async def on_message(self, ctx: Context, msg: str):
        log.info(f"[{ctx.display_name}] {ctx.sid} 發送了訊息: {msg}")

    @Plugin.listener()
    async def on_disconnect(self, ctx: Context):
        log.info(f"{ctx.sid} 以斷開")


def setup(server: "BaseServer") -> None:
    server.add_plugin(BasePlugin_Events(server))

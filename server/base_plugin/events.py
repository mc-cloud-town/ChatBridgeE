import logging

from .. import Plugin, Context

log = logging.getLogger("chat-bridgee")


class BasePlugin_Events(Plugin):
    @Plugin.listener()
    async def on_disconnect(self, ctx: Context):
        log.info(f"{ctx.sid} 以斷開")

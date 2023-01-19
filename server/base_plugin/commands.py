# ser.command_manager.add_commands({"add plugin", "remove plugin"})
import logging

from .. import Plugin, Context, BaseServer

log = logging.getLogger("chat-bridgee")


class BasePlugin_Events(Plugin):
    @Plugin.listener()
    async def on_disconnect(self, ctx: Context):
        log.info(f"{ctx.sid} 以斷開")


def setup(server: BaseServer):
    ...

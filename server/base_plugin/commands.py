# ser.command_manager.add_commands({"add plugin", "remove plugin"})
import logging

from .. import Plugin, Context, BaseServer

log = logging.getLogger("chat-bridgee")


class BasePlugin_Commands(Plugin):
    def on_load(self) -> None:
        commands = (
            "plugin list",
            "plugin add",
            "plugin remove",
        )

        self.server.command_manager.add_commands(commands)

    def on_unload(self) -> None:
        pass

    @Plugin.listener()
    async def on_disconnect(self, ctx: Context):
        log.info(f"{ctx.sid} 以斷開")

    @Plugin.listener()
    async def on_command_plugin_list(self):
        print("\n".join(self.server.plugins.keys()))


def setup(server: BaseServer):
    server.add_plugin(BasePlugin_Commands(server))

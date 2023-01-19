import logging

from server.utils import MISSING

from .. import Context, BaseServer, Plugin
from ._base import BasePlugin

log = logging.getLogger("chat-bridgee")


class BasePlugin_Commands(BasePlugin):
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
        plugins = [
            f"{i+1}: {k}" + ("\t[內建插件]" if isinstance(v, BasePlugin) else "")
            for i, (k, v) in enumerate(self.server.plugins.items())
        ]

        print("------ Plugins ------")
        print("\n".join(plugins))
        print("---------------------")

    @Plugin.listener()
    async def on_command_plugin_remove(self, name: str = MISSING):
        if name is MISSING:
            print("請輸入插件名稱")
            return
        print(self.server.get_plugin(name).__class__)
        if isinstance(self.server.get_plugin(name), BasePlugin):
            print("該插劍為內建插件，無法移除")
            return
        if self.server.remove_plugin(name) is None:
            print("插件不存在")
            return
        else:
            print("插件移除成功")


def setup(server: BaseServer):
    server.add_plugin(BasePlugin_Commands(server))

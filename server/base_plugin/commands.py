import logging

from .. import BaseServer, Plugin
from ..errors import ExtensionNotFound
from ..utils import MISSING
from .__base import BasePlugin

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
        try:
            self.server.unload_extension(f"plugins.{name}")
        except ExtensionNotFound:
            print("插件不存在")
            return
        else:
            print("插件移除成功")

    @Plugin.listener()
    async def on_command_plugin_add(self, name: str = MISSING):
        if name is MISSING:
            print("請輸入插件名稱")
            return
        self.server.load_plugin(f"plugins.{name}")


def setup(server: BaseServer):
    server.add_plugin(BasePlugin_Commands(server))

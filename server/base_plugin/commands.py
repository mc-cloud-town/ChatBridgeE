import logging

from rich.table import Table
from rich import print as rich_print

from .. import BaseServer, Plugin
from ..errors import ExtensionAlreadyLoaded, ExtensionNotFound
from ..utils import MISSING
from .__base import BasePlugin

log = logging.getLogger("chat-bridgee")


class BasePlugin_Commands(BasePlugin):
    def on_load(self) -> None:
        commands = (
            "plugin list",
            "plugin add",
            "plugin remove",
            "plugin reload",
        )

        self.server.command_manager.add_commands(commands)

    def on_unload(self) -> None:
        pass

    @Plugin.listener()
    async def on_command_plugin_list(self):
        table = Table(show_header=False, show_lines=True, header_style="bold magenta")

        for i, (k, v) in enumerate(self.server.plugins.items()):
            table.add_row(
                str(i + 1),
                str(k),
                "內建插件" if isinstance(v, BasePlugin) else f"{v.__module__[8:]}",
            )

        rich_print(table)

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
        try:
            self.server.load_plugin(f"plugins.{name}")
        except ExtensionAlreadyLoaded:
            print("插劍已經加載, 若要重新加載請使用 plugin reload")

    @Plugin.listener()
    async def on_command_plugin_reload(self, name: str = MISSING):
        if name is MISSING:
            print("請輸入插件名稱")
            return

        await self.on_command_plugin_remove(name)
        await self.on_command_plugin_add(name)


def setup(server: BaseServer):
    server.add_plugin(BasePlugin_Commands(server))

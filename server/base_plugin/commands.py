import logging

from rich import print as rich_print
from rich.table import Table

from .. import BaseServer, Plugin
from ..errors import ExtensionAlreadyLoaded, ExtensionNotFound, NoEntryPointError
from ..utils import MISSING
from .__base import BasePlugin

log = logging.getLogger("chat-bridgee")


class BasePlugin_Commands(BasePlugin, description="指令處理"):
    @Plugin.listener
    async def on_command_plugin_list(self):
        table = Table(show_header=False, show_lines=True, header_style="bold magenta")

        for i, (k, v) in enumerate(self.server.plugins.items()):
            table.add_row(
                str(i + 1),
                str(k),
                "內建插件" if isinstance(v, BasePlugin) else f"{v.__module__[8:]}",
                v.__plugin_description__,
            )

        rich_print(table)

    @Plugin.listener
    async def on_command_plugin_remove(self, name: str = MISSING):
        if name is MISSING:
            print("請輸入插件名稱")
            return

        try:
            self.server.unload_extension(f"{self.server.plugins_dir}.{name}")
        except ExtensionNotFound:
            print("插件不存在")
            return
        else:
            print("插件移除成功")

        return True

    @Plugin.listener
    async def on_command_plugin_add(self, name: str = MISSING):
        if name is MISSING:
            print("請輸入插件名稱")
            return

        try:
            self.server.load_extension(f"{self.server.plugins_dir}.{name}")
        except ExtensionAlreadyLoaded:
            log.error("插件已經加載, 若要重新加載請使用 plugin reload")
        except NoEntryPointError:
            log.error("未找到插件")

    @Plugin.listener
    async def on_command_plugin_reload(self, name: str = MISSING):
        if name is MISSING:
            for plugin in self.server.plugins.copy().values():
                if isinstance(plugin, BasePlugin):
                    continue

                name = plugin.__module__[len(self.server.plugins_dir) + 1 :]
                await self.on_command_plugin_remove(name)
                await self.on_command_plugin_add(name)

            print("插件重新加載完成")
            return

        if await self.on_command_plugin_remove(name):
            await self.on_command_plugin_add(name)

    @Plugin.listener
    async def on_command_send_all(self, message: str = MISSING):
        if message is MISSING:
            print("請輸入訊息")
            return

        await self.server.send(message, server_name="終端伺服器", no_mark=True)


def setup(server: BaseServer):
    server.add_plugin(BasePlugin_Commands(server))

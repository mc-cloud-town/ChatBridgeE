import asyncio
import threading

from discord import Intents
import discord
from discord.errors import LoginFailure

from server import BaseServer, Plugin
from server.utils.config import Config


class DiscordConfig(Config):
    token: str = "<you discord token here>"
    prefix: str = "!!"


class Test(Plugin, config=DiscordConfig):
    def __init__(self, server: BaseServer):
        super().__init__(server)

        # TODO add prefix from config
        self.bot = discord.Bot(
            command_prefix=self.config.get("prefix"),
            intents=Intents.all(),
            loop=asyncio.new_event_loop(),
        )

    @Plugin.listener()
    async def on_message(self, a, b):
        print(a, b)
        print("----------------------------------------")

    def on_load(self):
        config = self.config
        config_path = f"{config.__config_path__}/{config.__config_name__}.{config.__config_filetype__}"  # noqa

        def start():
            try:
                self.bot.run(config.get("token"))
            except LoginFailure:
                self.log.error(f"Discord Token 錯誤, 請在 {config_path} 中修改 token 的值")
                self.server.unload_extension(self.__module__)

        threading.Thread(target=start).start()

    def on_unload(self) -> None:
        async def close():
            try:
                await self.bot.close()
            except Exception as e:
                ...

        self.bot.loop.create_task(close())


def setup(server: BaseServer):
    server.add_plugin(Test(server))

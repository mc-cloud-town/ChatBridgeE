import threading

from discord.errors import LoginFailure

from server import BaseServer, Plugin
from server.utils import Config

from ._client import Bot


class DiscordConfig(Config):
    token: str = "<you discord token here>"
    prefix: str = "!!"
    chat_channels: list[int] = []


class Discord(Plugin, config=DiscordConfig):
    def __init__(self, server: BaseServer):
        super().__init__(server)

        self.bot = Bot(self)

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
            except (RuntimeError, AssertionError):
                pass

        threading.Thread(target=start).start()

    def on_unload_before(self):
        async def close():
            try:
                await self.bot.close()
            except Exception:
                pass

        self.bot.loop.create_task(close())


def setup(server: BaseServer):
    server.add_plugin(Discord(server))

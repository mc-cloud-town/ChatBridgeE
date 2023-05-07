from discord.errors import LoginFailure

from server import BaseServer, Context, Plugin
from server.utils import Config

from .client import Bot


class DiscordConfig(Config):
    token: str = "<you discord token here>"
    prefix: str = "!!"
    # slash or prefix
    command_type = "slash"
    channel_for_chat = 123400000000000000
    command_channels: list[int] = [123400000000000000]
    parents_for_command: list[int] = [123400000000000000]
    client_to_query_stats = "Survival"


class Discord(Plugin, config=DiscordConfig):
    def __init__(self, server: BaseServer):
        super().__init__(server)

        self.bot = Bot(self, loop=self.loop)

    def on_load(self):
        config = self.config

        async def runner():
            try:
                await self.bot.start(config.get("token"))
            except LoginFailure:
                self.log.error(
                    "Discord Token 錯誤, 請在 "
                    f"{config.__config_file_path__} 中修改 token 的值"
                )
                self.server.unload_extension(self.__module__)
            except (RuntimeError, AssertionError):
                pass
            finally:
                if not self.bot.is_closed():
                    await self.bot.close()

        self.loop.create_task(runner())

    def on_unload_before(self):
        async def close():
            try:
                await self.bot.close()
            except Exception:
                pass

        self.loop.create_task(close())

    @Plugin.listener
    async def on_server_start(self, ctx: Context):
        ...

    @Plugin.listener
    async def on_server_startup(self, ctx: Context):
        ...

    @Plugin.listener
    async def on_server_stop(self, ctx: Context):
        ...

    @Plugin.listener
    async def on_player_chat(self, ctx: Context, player_name: str, content: str):
        ...

    @Plugin.listener
    async def on_player_joined(self, ctx: Context, player_name: str):
        ...

    @Plugin.listener
    async def on_player_left(self, ctx: Context, player_name: str):
        self


def setup(server: BaseServer):
    server.add_plugin(Discord(server))

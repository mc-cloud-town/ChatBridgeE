import asyncio
import threading
from typing import TypedDict
from discord import Intents
import discord

from server import BaseServer, Plugin


class DiscordConfig(TypedDict):
    token: str


class Test(Plugin, config=True):
    def __init__(self, server: BaseServer):
        super().__init__(server)

        intents = Intents.default()
        intents.message_content = True

        # TODO add prefix from config
        self.bot = discord.Bot(
            command_prefix="!!",
            intents=intents,
            loop=asyncio.new_event_loop(),
        )

    @Plugin.listener()
    async def on_message(self, a, b):
        print(a, b)
        print("----------------------------------------")

    def on_load(self):
        # TODO add token from config
        def start():
            try:
                self.bot.run(
                    "",
                )
            except Exception as e:
                ...

        threading.Thread(target=start).start()

    def on_unload(self) -> None:
        async def close():
            try:
                self.bot.loop.close()
                await self.bot.close()
            except Exception as e:
                ...

        asyncio.create_task(close())


def setup(server: BaseServer):
    server.add_plugin(Test(server))

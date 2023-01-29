import asyncio
import inspect
import platform
from typing import Any, Optional

import discord
from discord import Intents, Message, TextChannel

from server import Plugin


class Bot(discord.Bot):
    def __init__(self, plugin: Plugin):
        super().__init__(
            command_prefix=self.config.get("prefix"),
            intents=Intents.all(),
            loop=asyncio.new_event_loop(),
        )

        self.plugin = plugin
        self.log = plugin.log
        self.config = plugin.config
        self.server = plugin.server

    async def on_ready(self):
        self.log.info(f"[cyan]discord 登入 {self.user}[/cyan]")

    async def get_reference_message(self, msg: Message) -> Optional[Message]:
        if not msg.reference:
            return None
        return await self.get_or_fetch_message(msg.reference.message_id, msg.channel)

    async def style_message(self, msg: Message) -> dict:
        ...

    async def on_message(self, msg: Message):
        if msg.author == self.user:
            return

        self.log.info(f"discord 收到訊息 {msg}")

    async def get_or_fetch_message(
        self,
        id: int,
        channel: TextChannel,
    ) -> Optional[Message]:
        if (message := self.get_message(channel, id)) is not None:
            return message
        try:
            return await channel.fetch_message(id)
        except discord.NotFound:
            return None

    def run(self, *args: Any, **kwargs: Any):
        for msg in inspect.cleandoc(
            f"""
            [red]python version: [/red][cyan]{platform.python_version()}[/cyan]
            [red]py-cord version: [/red][cyan]{discord.__version__}[/cyan]
            [red]bot version: [/red][cyan]{self.__version__}[/cyan]
            """
        ).split("\n"):
            self.log.info(msg)

        super().run(*args, **kwargs)

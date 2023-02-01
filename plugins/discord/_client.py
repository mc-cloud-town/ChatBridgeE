import asyncio
import json
from typing import Any, Optional

import discord
from discord import Intents, Message, TextChannel

from server import Plugin
from server.utils import chat_format


class Bot(discord.Bot):
    def __init__(self, plugin: Plugin):
        super().__init__(
            command_prefix=plugin.config.get("prefix"),
            intents=Intents.all(),
            loop=asyncio.new_event_loop(),
        )

        self.plugin = plugin
        self.log = plugin.log
        self.config = plugin.config
        self.server = plugin.server
        self.log.info(
            f"[red]py-cord version: [/red][cyan]{discord.__version__}[/cyan]",
            extra=dict(markup=True),
        )

    @property
    def chat_channels(self) -> list[int]:
        return self.config.get("chat_channels", [])

    async def on_ready(self):
        self.log.info(f"[cyan]discord 登入 {self.user}[/cyan]", extra=dict(markup=True))

    async def get_reference_message(self, msg: Message) -> Optional[Message]:
        if not msg.reference:
            return None
        return await self.get_or_fetch_message(msg.reference.message_id, msg.channel)

    def style_message(self, msg: Message) -> list:
        contents = []
        if (content := msg.content) != "":
            contents.append(("" if content.startswith("\\:") else " ") + content)
        if len(msg.attachments) > 0:
            if content != "":
                contents.append(" ")
            contents.append(f"@{msg.jump_url} <打開附件>")
        return chat_format(*contents)

    async def on_message(self, msg: Message):
        if msg.author == self.user or msg.channel.id not in self.chat_channels:
            return
        self.log.info(f"discord 收到訊息 {msg}")

        if (ref_msg := await self.get_reference_message(msg)) is not None:
            style = self.style_message(ref_msg)
            self.log.debug(json.dumps(style["mc"]))
            self.log.info(style["ansi"])
        style = self.style_message(msg)
        self.log.debug(json.dumps(style["mc"]))
        self.log.info(style["ansi"])

        # await self.server.emit()

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
        super().run(*args, **kwargs)

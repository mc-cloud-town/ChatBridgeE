import asyncio
from typing import Any, Optional

import discord
from discord import Intents, Message, TextChannel

from server import Plugin


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

    def style_message(self, msg: Message) -> str:
        contents = []
        if content := msg.content:
            contents.append(("" if content.startswith("\\:") else " ") + content)
        if len(msg.attachments) > 0:
            contents.append(f" @{msg.jump_url} <打開附件>")
        return " ".join(contents)

    async def on_message(self, msg: Message):
        if msg.author == self.user or msg.channel.id not in self.chat_channels:
            return
        self.log.info(f"discord 收到訊息 {msg}")
        if (ref_msg := await self.get_reference_message(msg)) is not None:
            style = self.style_message(ref_msg)
            print(style)
            ref_author = ref_msg.author
            # ┌─回覆自 <XX> XX
            await self.server.send(
                [
                    "g ┌─回覆自 <",
                    "c " + (ref_author.nick or ref_author.name),
                    f"g >{self.style_message(ref_msg)}\n",
                ]
            )

        author = msg.author
        content = ["g [", "c DC", "g ] "]
        content += ["g <", "c " + (author.nick or author.name), "g > "]
        content.append(self.style_message(msg))

        # [DC] <XX> XX
        await self.server.send(content)

    async def get_or_fetch_message(
        self,
        id: int,
        channel: TextChannel,
    ) -> Optional[Message]:
        if (message := self.get_message(id)) is not None:
            return message
        try:
            return await channel.fetch_message(id)
        except discord.NotFound:
            return None

    def run(self, *args: Any, **kwargs: Any):
        super().run(*args, **kwargs)

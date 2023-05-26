import asyncio
from asyncio import AbstractEventLoop
from typing import Optional

import discord
from discord import ApplicationContext, Intents, Message, TextChannel
from discord.ext import commands
from rich.text import Text

from server import Plugin
from server.utils.format import FormatMessage


class Bot(commands.Bot):
    def __init__(self, plugin: Plugin, loop: AbstractEventLoop | None = None):
        super().__init__(
            command_prefix=plugin.config.get("prefix"),
            intents=Intents.all(),
            loop=asyncio.new_event_loop() if loop is None else loop,
            help_command=None,
        )

        self.plugin = plugin
        self.log = plugin.log
        self.config = plugin.config
        self.server = plugin.server
        self.log.info(
            f"[red]py-cord version: [/red][cyan]{discord.__version__}[/cyan]",
            extra=dict(markup=True),
        )
        self.add_cog(BotCommand(self))

    @property
    def chat_channel(self) -> int | None:
        return self.config.get("channel_for_chat", None)

    async def get_or_fetch_channel(self, id: int) -> TextChannel | None:
        if channel := self.get_channel(id):
            return channel
        try:
            return await self.fetch_channel(id)
        except Exception:
            return None

    async def on_ready(self):
        self.log.info(f"[cyan]discord 登入 {self.user}[/cyan]", extra=dict(markup=True))

    async def get_reference_message(self, msg: Message) -> Optional[Message]:
        if not msg.reference:
            return None
        return await self.get_or_fetch_message(msg.reference.message_id, msg.channel)

    def style_message(self, msg: Message) -> list[FormatMessage]:
        contents = []
        if content := msg.content:
            contents.append(
                FormatMessage(
                    content[2:] if content.startswith("\\:") else f" {content}",
                )
            )
        if len(msg.attachments) > 0:
            contents += [FormatMessage("li <點我打開附件>", f"@ {msg.jump_url}")]
        return contents

    async def on_message(self, msg: Message):
        # call command handler
        if msg.channel.id in self.config.get(
            "command_channels", []
        ) or msg.channel.category_id in self.config.get("parents_for_command", []):
            asyncio.create_task(self.process_commands(msg), name="discord-command")
            return

        author = msg.author
        if msg.channel.id != self.chat_channel or author == self.user or author.system:
            return

        if (ref_msg := await self.get_reference_message(msg)) is not None:
            ref_author = ref_msg.author
            # ┌─回覆自 <XX> XX
            await self.server.send(
                ["g ┌─回覆自 <", "r " + (ref_author.nick or ref_author.name), "g > "]
                + self.style_message(ref_msg),
            )

        content = ["f [", "r Discord", "f ] "]
        content += ["f <", f"r {author.nick or author.name}", "f > "]
        content += self.style_message(msg)
        content = FormatMessage(*content)

        self.log.info(f"discord 收到訊息 {Text.from_ansi(content.ansi)}")

        # [Discord] <XX> XX
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


class BotCommand(discord.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.log = bot.log
        self.plugin = bot.plugin
        self.config = bot.config
        self.server = bot.server

    @commands.command()
    async def online(self, ctx: ApplicationContext):
        try:
            from plugins.online import Online
        except Exception:
            return await ctx.send("未啟用 Online 插件")

        plugin: Online = self.server.get_plugin(Online.__plugin_name__)

        data = await plugin.query()
        await ctx.send(data)

        # TODO: online command

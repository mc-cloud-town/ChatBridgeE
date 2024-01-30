from __future__ import annotations

import asyncio
import platform
import random
import time
from asyncio import AbstractEventLoop
from datetime import datetime
from functools import reduce
from pathlib import Path
from typing import Optional

import discord
from discord import (
    ApplicationContext,
    Color,
    DiscordException,
    Embed,
    Intents,
    Message,
    Reaction,
    TextChannel,
    User,
)
from discord.ext import commands
from discord.ext.commands import CommandError, CommandNotFound, Context, NotOwner
import rich
from rich.text import Text
from rich.box import MINIMAL
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

from server import Plugin
from server.utils import FileEncode, FormatMessage, format_number


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
        self.console = rich.get_console()
        self.config = plugin.config
        self.server = plugin.server
        self._uptime = None
        self.log.info(
            f"[red]py-cord version: [/red][cyan]{discord.__version__}[/cyan]",
            extra=dict(markup=True),
        )
        self.add_cog(BotCommand(self))
        if Path("extra/discord").exists():
            self.load_extension("extra.discord", recursive=True)

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
        if self._uptime is not None:
            return

        self._uptime = datetime.now()

        table_cogs_info = Table(show_edge=False, show_header=False, box=MINIMAL)

        table_cogs_info.add_column(style="blue")
        table_cogs_info.add_column(style="cyan")

        for cog in self.cogs.values():
            table_cogs_info.add_row(
                cog.__cog_name__,
                f"{docs[:30]}..."
                if len(docs := cog.__cog_description__) > 20
                else docs or "-",
            )

        table_general_info = Table(show_edge=False, show_header=False, box=MINIMAL)

        table_general_info.add_column(style="blue")
        table_general_info.add_column(style="cyan")

        table_general_info.add_row("Prefixes", self.command_prefix)
        table_general_info.add_row("python version", platform.python_version())
        table_general_info.add_row("py-cord version", discord.__version__)
        table_general_info.add_row("bot version", self.__version__)

        table_counts = Table(show_edge=False, show_header=False, box=MINIMAL)

        table_counts.add_column(style="blue")
        table_counts.add_column(style="cyan")

        table_counts.add_row("Servers", str(len(self.guilds)))
        table_counts.add_row(
            "Unique Users",
            str(len(self.users)) if self.intents.members else "-",
        )
        table_counts.add_row("Shards", str(self.shard_count or "-"))

        self.console.print(
            Columns(
                [
                    Panel(table_cogs_info, title=f"[yellow]cogs - {len(self.cogs)}"),
                    Panel(table_general_info, title=f"[yellow]{self.user} login"),
                    Panel(table_counts, title="[yellow]counts"),
                ]
            ),
        )

    async def on_command(self, ctx: Context):
        self.log.info(
            f"[{ctx.guild.name}] [{ctx.channel.name}] "
            f"{ctx.author} +msg-command+ -> {ctx.command.name}"
        )

    async def on_application_command(self, ctx: ApplicationContext):
        self.log.info(
            f"[{ctx.guild.name}] [{ctx.channel.name}] "
            f"{ctx.author} +slash-command+ -> {ctx.command.name}"
        )

    async def on_command_error(self, ctx: Context, error: CommandError):
        if isinstance(error, (CommandNotFound, NotOwner)):
            return

        self.log.exception(type(error).__name__, exc_info=error)

    async def on_application_command_error(
        self,
        ctx: ApplicationContext,
        error: DiscordException,
    ):
        self.log.exception(type(error).__name__, exc_info=error)

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
                    no_mark=True,
                )
            )
        if len(msg.attachments) > 0:
            contents += [
                FormatMessage(
                    "li <Click Me to open the attachment [點我打開附件]>",
                    f"@ {msg.jump_url}",
                )
            ]
        return contents

    async def on_message(self, msg: Message):
        ctx: commands.Context = await self.get_context(msg)
        if ctx.command and (
            msg.channel.id in self.config.get("command_channels", [])
            or msg.channel.category_id in self.config.get("parents_for_command", [])
        ):
            return await self.process_commands(msg)

        if (author := msg.author) == self.user or author.system or author.bot:
            return

        canned_message: dict[str, str | list[str]] = self.config.get(
            "canned_message",
            {},
        )
        if (key := msg.content) in canned_message:
            await msg.channel.send(
                random.choice(value)
                if type(value := canned_message[key]) is list
                else value
            )

        if msg.channel.id == self.chat_channel:
            if (ref_msg := await self.get_reference_message(msg)) is not None:
                ref_author = ref_msg.author
                # ┌─<XX> XX
                await self.server.send(
                    ["g ┌─<", f"r {ref_author.display_name}", "g > "]
                    + self.style_message(ref_msg),
                )

            content = ["f [", "r Discord", "f ] "]
            content += ["f <", f"r {author.display_name}", "f > "]
            content += self.style_message(msg)
            content = FormatMessage(*content)

            self.log.info(f"discord 收到訊息 {Text.from_ansi(content.ansi)}")

            # [Discord] <XX> XX
            await self.server.send(content)

        # sync_channel
        if self.config.get("sync_enabled") and msg.channel.id == self.config.get(
            "sync_channel"
        ):
            sync_file_extensions = tuple(
                self.config.get("sync_file_extensions").split(",")
            )
            if files := [
                FileEncode(
                    path=attachment.filename,
                    data=await attachment.read(),
                    server_name="Discord",
                )
                for attachment in msg.attachments
                if attachment.filename.endswith(sync_file_extensions)
            ]:
                if not self.config.get("auto_sync_updata"):
                    await msg.add_reaction("❓")
                    await msg.reply(
                        "Are you sure you want to sync files? Please click `❓` "
                        "[是否確定要同步檔案？請點擊 `❓`]",
                        mention_author=False,
                    )

                    def check(reaction: Reaction, user: User) -> bool:
                        return (
                            user == msg.author
                            and reaction.message == msg
                            and reaction.emoji == "❓"
                        )

                    try:
                        await self.wait_for("reaction_add", check=check, timeout=60)
                    except TimeoutError:
                        await msg.clear_reaction("❓")
                        return
                    else:
                        await msg.clear_reaction("❓")

                now_time = time.time()
                reply_msg = await msg.reply(
                    f"Please wait later... [同步中請稍後...](0/{len(files)})",
                    mention_author=False,
                )
                for index, file in enumerate(files):
                    await reply_msg.edit(
                        "Please wait later... [同步中請稍後...]" f"({index+1}/{len(files)})",
                    )
                    await self.server.emit("file_sync", file.encode())

                await msg.add_reaction("✅")
                await reply_msg.edit(
                    "Synchronization completed [同步完成] "
                    f"- {time.time() - now_time:.2f}s",
                )

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


class BaseCog(discord.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.log = bot.log
        self.plugin = bot.plugin
        self.config = bot.config
        self.server = bot.server


class BotCommand(BaseCog):
    @commands.command()
    async def stats(self, ctx: ApplicationContext, *args):
        if not (client_name := self.config.get("client_to_query_stats", None)):
            return
        if not (client := self.server.get_client(client_name)):
            return

        result = await client.extra_command(
            f"stats rank {' '.join(args[1:] if args[0] == 'rank' else args)}"
        )

        # stats:
        #   success> code: 0
        #   unknown stats> code: 1
        #   no stats_helper> code: 2
        if (code := result.get("code", 2)) == 0:
            embed = Embed(color=Color.blue(), timestamp=datetime.now())
            ranks, players, values = [], [], []

            for line in result.get("data", []):
                line: str
                rank, player, value = line.split(" ")

                ranks.append(rank)
                players.append(fix_msg(player))
                values.append(value)

            embed.set_author(
                name=f"Statistic Rank [統計排名]-{result.get('stats_name')}",
                icon_url=ctx.guild.icon,
            )
            embed.add_field(name="Rank [排名]", value="\n".join(ranks))
            embed.add_field(name="Player [玩家]", value="\n".join(players))
            embed.add_field(name="Value [數值]", value="\n".join(values))
            embed.set_footer(
                text=f"Total [總計]: {format_number(result.get('total', -1))}",
            )

            await ctx.send(embed=embed)
        elif code == 1:
            await ctx.send("Unknown stats name [未知的 stats 名稱]")
        elif code == 2:
            await ctx.send(
                "The stats_helper plugin is not enabled to query stats "
                "[未啟用 stats_helper 插件，無法查詢 stats]"
            )

    @commands.command()
    async def online(self, ctx: ApplicationContext):
        try:
            from plugins.online import Online

            if (plugin := self.server.get_plugin(Online.__plugin_name__)) is None:
                raise Exception
            plugin: Online
        except Exception:
            return await ctx.send("The Online plug-in is not enabled [未啟用 Online 插件]")

        data = await plugin.query(order=True)
        self.log.debug(f"get online players: {data}")
        embed = Embed(color=Color.blue(), timestamp=datetime.now())

        embed.add_field(
            name=(
                "List of members [成員列表]"
                f"({reduce(lambda x, y: x + y, map(lambda x: len(x[1]), data))})"
            ),
            value="\n".join(
                f"- [{k.display_name}]({len(v)}): {', '.join(map(fix_msg, v))}"
                for k, v in data
            )
            + f"\n\nTotal number of servers [總伺服器數]: {len(data)}",
        )

        embed.set_author(
            name=(
                self.config.get("online_display_name", ctx.guild.name)
                + "Number of online [上線人數]"
            ),
            icon_url=ctx.guild.icon
            if (url := self.config.get("online_icon_url")) == "AUTO"
            else url,
        )
        await ctx.send(embed=embed)


def fix_msg(msg: str):
    for c in ["\\", "`", "*", "_", "<", ">", "@"]:
        msg = msg.replace(c, f"\\{c}")
    return msg

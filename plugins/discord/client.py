import asyncio
from asyncio import AbstractEventLoop
from datetime import datetime
from functools import reduce
from typing import Optional

import discord
from discord import ApplicationContext, Color, Embed, Intents, Message, TextChannel
from discord.ext import commands
from rich.text import Text

from server import Plugin
from server.utils import FormatMessage, format_number


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
        self.log.info(
            f"[cyan]discord login {self.user}[/cyan]",
            extra=dict(markup=True),
        )

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

        author = msg.author
        if msg.channel.id != self.chat_channel or author == self.user or author.system:
            return

        if (ref_msg := await self.get_reference_message(msg)) is not None:
            ref_author = ref_msg.author
            # ┌─<XX> XX
            await self.server.send(
                ["g ┌─<", "r " + (ref_author.nick or ref_author.name), "g > "]
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
    async def stats(self, ctx: ApplicationContext, *args):
        if not (client_name := self.config.get("client_to_query_stats", None)):
            return
        if not (client := self.server.get_client(client_name)):
            return

        result = await client.extra_command(f"stats {' '.join(args)}")

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
                players.append(back_msg(player))
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
                [f"- [{k.display_name}]({len(v)}): {', '.join(v)}" for k, v in data]
            )
            + f"\n\nTotal number of servers [總伺服器數]: {len(data)}",
        )

        embed.set_author(
            name=(
                self.config.get("online_display_name", ctx.guild.name)
                + "Number of ongo-ins [上線人數]"
            ),
            icon_url=ctx.guild.icon
            if (url := self.config.get("online_icon_url")) == "AUTO"
            else url,
        )
        await ctx.send(embed=embed)


def back_msg(msg: str):
    for c in ["\\", "`", "*", "_", "<", ">", "@"]:
        msg = msg.replace(c, f"\\{c}")
    return msg

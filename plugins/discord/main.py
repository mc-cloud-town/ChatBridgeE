from __future__ import annotations

from io import BytesIO
from pathlib import Path

import aiohttp
from discord import MISSING, File, TextChannel, Webhook
from discord.errors import LoginFailure

from server import BaseServer, Context, Plugin
from server.utils import Config, FileEncode

from .client import Bot, fix_msg


class DiscordConfig(Config):
    token: str = "<you discord token here>"
    webhook: str = "<your webhook here (optional)>"
    avatarApi: str = "https://mc-heads.net/avatar/{player}.png"
    default_avatar: str = ""
    prefix: str = "!!"
    sync_enabled: bool = True
    sync_channel: int = 123400000000000000
    auto_sync_updata: bool = False
    sync_file_extensions: list[str] = ".schem,.schematic"
    channel_for_chat = 123400000000000000
    player_join_channel: int = 123400000000000000
    command_channels: list[int] = [123400000000000000]
    parents_for_command: list[int] = [123400000000000000]
    client_to_query_stats = "Survival"
    online_display_name = "雲鎮工藝"
    online_icon_url = "AUTO"
    canned_message: dict[str, str | list[str]] = {}
    black_canned_message_channel: dict[str, list[int]] = {}
    black_canned_message_category: dict[str, list[int]] = {}


class Discord(Plugin, config=DiscordConfig):
    def __init__(self, server: BaseServer):
        super().__init__(server)

        self.bot = Bot(self, loop=self.loop)
        self.chat_channel: TextChannel | None = ...
        self.player_join_channel: TextChannel | None = ...
        self.sync_channel: TextChannel | None = ...

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

    async def send(
        self,
        content: str,
        ctx: Context | None = None,
        channel: TextChannel | None = ...,
        player_name: str = "",
        **kwargs,
    ) -> None:
        if (webhook := str(self.config.get("webhook"))).startswith("http"):
            async with aiohttp.ClientSession() as session:
                ch: Webhook = Webhook.from_url(webhook, session=session)

                text_player_name = (
                    f"{player_name} - " if player_name else ""
                ) + ctx.display_name
                avatar_url = (
                    str(self.config.get("avatarApi")).format(player=player_name)
                    if player_name
                    else self.config.get("default_avatar") or MISSING
                )
                await ch.send(
                    content,
                    username=text_player_name,
                    avatar_url=avatar_url,
                    **kwargs,
                )
            return

        if self.chat_channel is ...:
            self.chat_channel = await self.bot.get_or_fetch_channel(
                self.config.get("channel_for_chat")
            )

        if channel := self.chat_channel if channel is ... else channel:
            content = (
                f"[{ctx.display_name}] <{fix_msg(player_name)}> {content}"
                if player_name
                else f"[{ctx.display_name}] {content}"
            )
            await channel.send(content, **kwargs)

    @Plugin.listener
    async def on_server_start(self, ctx: Context):
        await self.send("Starting - 啟動中", ctx=ctx)

    @Plugin.listener
    async def on_server_startup(self, ctx: Context):
        await self.send("Startup complete - 啟動完成", ctx=ctx)

    @Plugin.listener
    async def on_server_stop(self, ctx: Context):
        await self.send("The server shuts down - 伺服器關閉", ctx=ctx)

    @Plugin.listener
    async def on_player_chat(self, ctx: Context, player_name: str, content: str):
        await self.send(content, ctx=ctx, player_name=player_name)

    async def send_join_channel(
        self,
        content: str,
        ctx: Context | None = None,
        channel: TextChannel | None = None,
        **kwargs,
    ):
        if self.player_join_channel is ...:
            self.player_join_channel = await self.bot.get_or_fetch_channel(
                self.config.get("player_join_channel")
            )

        await self.send(
            content,
            ctx=ctx,
            channel=channel or self.player_join_channel,
            **kwargs,
        )

    @Plugin.listener
    async def on_player_joined(self, ctx: Context, player_name: str):
        await self.send_join_channel(
            f"{fix_msg(player_name)} joined {fix_msg(ctx.display_name)}",
            ctx=ctx,
        )

    @Plugin.listener
    async def on_player_left(self, ctx: Context, player_name: str):
        await self.send_join_channel(
            f"{fix_msg(player_name)} left {fix_msg(ctx.display_name)}",
            ctx=ctx,
        )

    @Plugin.listener
    async def on_file_sync(self, ctx: Context, data: FileEncode):
        if not self.config.get("sync_enabled"):
            return

        server_name, file_path = data.server_name, data.path

        if self.sync_channel is ...:
            self.sync_channel = await self.bot.get_or_fetch_channel(
                self.config.get("sync_channel")
            )

        await self.send(
            f"A file published from {server_name} - 從 {server_name} 發布的檔案",
            ctx=ctx,
            file=File(BytesIO(data.data), Path(file_path).name),
            channel=self.sync_channel,
        )


def setup(server: BaseServer):
    server.add_plugin(Discord(server))

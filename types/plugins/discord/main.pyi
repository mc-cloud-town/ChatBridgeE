from .client import Bot as Bot, fix_msg as fix_msg
from _typeshed import Incomplete
from discord import TextChannel as TextChannel
from server import BaseServer, Context, Plugin
from server.utils import Config, FileEncode

class DiscordConfig(Config):
    token: str
    webhook: str
    avatarApi: str
    default_avatar: str
    prefix: str
    sync_enabled: bool
    sync_channel: int
    auto_sync_updata: bool
    sync_file_extensions: list[str]
    channel_for_chat: int
    player_join_channel: int
    command_channels: list[int]
    parents_for_command: list[int]
    client_to_query_stats: str
    online_display_name: str
    online_icon_url: str
    canned_message: dict[str, str | list[str]]
    black_canned_message_channel: dict[str, list[int]]
    black_canned_message_category: dict[str, list[int]]

class Discord(Plugin, config=DiscordConfig):
    bot: Incomplete
    chat_channel: Incomplete
    player_join_channel: Incomplete
    sync_channel: Incomplete
    def __init__(self, server: BaseServer) -> None: ...
    def on_load(self) -> None: ...
    def on_unload_before(self) -> None: ...
    async def send(self, content: str, ctx: Context | None = None, channel: TextChannel | None = ..., player_name: str = '', **kwargs) -> None: ...
    async def on_server_start(self, ctx: Context): ...
    async def on_server_startup(self, ctx: Context): ...
    async def on_server_stop(self, ctx: Context): ...
    async def on_player_chat(self, ctx: Context, player_name: str, content: str): ...
    async def send_join_channel(self, content: str, ctx: Context | None = None, channel: TextChannel | None = None, **kwargs): ...
    async def on_player_joined(self, ctx: Context, player_name: str): ...
    async def on_player_left(self, ctx: Context, player_name: str): ...
    async def on_file_sync(self, ctx: Context, data: FileEncode): ...

def setup(server: BaseServer): ...

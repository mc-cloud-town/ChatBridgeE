import asyncio
import discord
from discord import Intents

from server import Plugin


class Bot(discord.Bot):
    def __init__(self, plugin: Plugin):
        super().__init__(
            command_prefix=plugin,
            intents=Intents.all(),
            loop=asyncio.new_event_loop(),
        )

        self.plugin = plugin

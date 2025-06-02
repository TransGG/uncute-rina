import discord

from discord._types import ClientT
from typing import Generic


class GuildInteraction(discord.Interaction[ClientT]):
    guild: discord.Guild

import discord

from discord._types import ClientT


class GuildInteraction(discord.Interaction[ClientT]):
    guild: discord.Guild

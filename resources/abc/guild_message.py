import discord
from .messageable_guild_channel import MessageableGuildChannel


class GuildMessage(discord.Message):
    guild: discord.Guild
    channel: MessageableGuildChannel  # GuildChannel but without Category
    guild_id: int

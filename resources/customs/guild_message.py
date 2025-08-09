import discord


class GuildMessage(discord.Message):
    guild: discord.Guild
    guild_id: int

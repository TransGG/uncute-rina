import discord


__all__ = ['MessageableGuildChannel']


type MessageableGuildChannel = (
    discord.TextChannel
    | discord.VoiceChannel
    | discord.StageChannel
    | discord.Thread
)

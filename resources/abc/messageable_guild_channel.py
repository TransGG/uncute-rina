import discord
import typing


type MessageableGuildChannel = (
    discord.TextChannel
    | discord.VoiceChannel
    | discord.StageChannel
    | discord.Thread
)


async def get_or_fetch_messageable_guild_channel(
        client: discord.Client,
        channel_id: int
) -> (
        MessageableGuildChannel | None
):
    """
    Use client.get_channel or client.fetch_channel if None

    :param client: The client with which to fetch the channel.
    :param channel_id: The channel to get or fetch.
    :raise discord.InvalidData: An unknown channel type was received
     from Discord.
    :raise discord.Forbidden: No permission to fetch this channel.
    :raise discord.HTTPException: Retrieving the channel failed.
    """
    ch = client.get_channel(channel_id)
    if ch is not None:
        assert isinstance(ch, MessageableGuildChannel.__value__)
        ch = typing.cast(MessageableGuildChannel, ch)
        return ch

    try:
        ch = await client.fetch_channel(channel_id)
        assert isinstance(ch, MessageableGuildChannel.__value__)
        ch = typing.cast(MessageableGuildChannel, ch)
    except discord.NotFound:
        return None

    return ch

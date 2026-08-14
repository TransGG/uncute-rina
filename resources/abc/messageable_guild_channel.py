import typing

import discord

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
    :raise TypeError: if the given channel id
     did not resolve to a messageable guild channel.
    """
    ch = client.get_channel(channel_id)
    if ch is None:
        try:
            ch = await client.fetch_channel(channel_id)
        except discord.NotFound:
            return None

    if not isinstance(ch, MessageableGuildChannel.__value__):
        raise TypeError(
            f"Expected channel id {channel_id} to resolve to a messageable guild channel but "
            f"it resolved to {ch.__class__.__name__}!"
        )

    ch = typing.cast(MessageableGuildChannel, ch)
    return ch

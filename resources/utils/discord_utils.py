from __future__ import annotations

import discord
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from resources.customs import GuildInteraction, Bot


async def get_or_fetch_channel(client: discord.Client, channel_id: int):
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
    if ch:
        return ch

    try:
        ch = await client.fetch_channel(channel_id)
    except discord.NotFound:
        return None

    return ch


def send_channel_or_interaction(itx: discord.Interaction):
    itx.response: discord.InteractionResponse  # type: ignore
    itx.followup: discord.Webhook  # type: ignore

    if (
            itx.channel is None
            or not isinstance(itx.channel, discord.abc.Messageable)
            or itx.guild is None
            or not itx.channel.permissions_for(itx.guild.me).send_messages
    ):
        return send_or_followup(itx)

    async def try_send_message(*args, **kwargs):
        assert itx.channel is not None
        assert isinstance(itx.channel, discord.abc.Messageable)

        try:
            return await itx.channel.send(*args, **kwargs)
        except discord.Forbidden:
            return await send_or_followup(itx)(*args, **kwargs)

    return try_send_message


def send_or_followup(itx: discord.Interaction):
    itx.response: discord.InteractionResponse  # type: ignore
    itx.followup: discord.Webhook  # type: ignore
    if itx.response.is_done():
        return itx.followup.send
    return itx.response.send_message


async def get_member_or_filter(
        itx: GuildInteraction[Bot],
        user: discord.User | discord.Member
) -> discord.Member | None:
    """
    Helper to send a warning response if the user is not a member of the guild.

    :param itx: The interaction to respond with. Note it is a GuildInteraction,
     because this function should only be used when you want to ensure the user
     is actually a member of the guild and automatically reply if not.
    :param user: The user to check.
    :return: The user if they are a :py:class:`discord.Member`, else None.
    """
    if isinstance(user, discord.User):
        await itx.response.send_message(
            "I could not find you in the server (I see you as User, not "
            "as Member), so I couldn't ",
            ephemeral=True,
        )
        return None
    return user

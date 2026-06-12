from __future__ import annotations
# ^ for logging, to show log time; and for parsetime
from typing import TYPE_CHECKING

import discord

from extensions.settings.objects.attribute_keys import AttributeKeys
import extensions.settings.objects.server_settings as server_settings

from resources.abc import (
    MessageableGuildChannel,
    GuildInteraction,
)
from resources.checks.errors import MissingAttributesCheckFailure
from resources.checks.command_checks import is_in_dms
from .debug import debug, DebugColor

if TYPE_CHECKING:
    from resources.customs import Bot


def get_mod_ticket_channel(
        client: Bot, guild_id: int | discord.Guild | GuildInteraction[Bot]
) -> MessageableGuildChannel | None:
    """
    Fetch the #contact-staff ticket channel for a specific guild.

    :param client: Rina's Bot class to fetch ticket channel IDs
     (hardcoded).
    :param guild_id: A class with a guild_id or guild property.

    :return: The matching guild's ticket channel id.
    :raise MissingAttributesCheckFailure: If the guild has no ticket
     channel defined in its settings.
    """
    if isinstance(guild_id, discord.Interaction):
        guild_id = guild_id.guild.id
    ticket_channel = client.get_guild_attributes(
        guild_id).ticket_create_channel

    return ticket_channel


async def log_to_guild(
        client: Bot,
        guild: discord.Guild | int | None,
        msg: str,
        *,
        crash_if_not_found: bool = False,
        ignore_dms: bool = False
) -> bool:
    """
    Log a message to a guild's logging channel (vcLog)

    :param client: The bot class with :py:func:`Bot.get_guild_info` to
     find logging channel.
    :param guild: Guild of the logging channel
    :param msg: Message you want to send to this logging channel
    :param crash_if_not_found: Whether to crash if the guild does not
     have a logging channel. Useful if this originated from an
     application command.
    :param ignore_dms: Whether to crash if the command was run in DMs.

    :return: ``True`` if a log was sent successfully, else ``False``.

    :raise KeyError: If client.vcLog channel is undefined. Note: It
     still outputs the given message to console and to the client's
     default log channel.
    :raise MissingAttributesCheckFailure: If no logging channel is
     defined.
    """
    # If we don't have a logging channel, then this ain't gonna work
    if guild is None:
        return False
    # The given key should restrict us to messagable channels
    log_channel = client.get_guild_attributes(guild).log_channel

    if log_channel is not None:
        await log_channel.send(content=msg, allowed_mentions=discord.AllowedMentions.none())
        return True

    if ignore_dms and is_in_dms(guild):
        return False
    if crash_if_not_found:
        raise MissingAttributesCheckFailure(
            "log_to_guild", [AttributeKeys.log_channel])

    # get current value for log_channel in the guild.
    attribute_raw = "<server was None>"
    if guild is not None:
        if isinstance(guild, discord.Guild):
            guild_id = guild.id
        else:
            guild_id = guild
        attribute_raw, log_channel = await _get_log_channel_from_serversettings(client, guild_id)

    if log_channel is None:
        debug(
            "Exception in log_channel (log_channel could not be loaded):\n"
            "    guild: " + repr(guild)
            + "\n    log_channel_id: "
            + attribute_raw
            + "\n    log message: "
            + msg,
            color=DebugColor.red
        )
        return False

    await log_channel.send(
        content=msg,
        allowed_mentions=discord.AllowedMentions.none()
    )
    return True


async def _get_log_channel_from_serversettings(
        client: Bot,
        guild_id: int,
) -> tuple[
        str,
        MessageableGuildChannel | None,
]:
    # fetch server settings
    entry = await server_settings.ServerSettings.get_entry(
        client.async_rina_db,
        guild_id,
    )
    channel_id_raw: str = "<no server data>"
    if entry is not None:
        channel_id_raw = str(
            entry["attribute_ids"].get(
                AttributeKeys.log_channel,
                "<no attribute data>",
            )
        )

    # parse log channel id to a channel
    log_channel_maybe: (
            MessageableGuildChannel
            | discord.CategoryChannel
            | discord.StageChannel
            | discord.ForumChannel
            | None
    ) = None  # we need to handle these other types somehow
    # ^ not that it should be anything other than a messageable guild channel...
    #  but there's a guard clause for that below this if-branch.
    # todo: surely this code can be refactored cleaner...
    if channel_id_raw.isdecimal():
        guild: discord.Guild | None = client.get_guild(guild_id)
        channel_id: int = int(channel_id_raw)
        if guild is None:
            return channel_id_raw, None

        try:
            log_channel_maybe = await guild.fetch_channel(
                channel_id)
        except discord.DiscordException:
            log_channel_maybe = None

    if (log_channel_maybe is not None
            and not isinstance(log_channel_maybe, MessageableGuildChannel.__value__)):
        log_channel_maybe = None

    return channel_id_raw, log_channel_maybe

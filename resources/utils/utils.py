from __future__ import annotations
# ^ for logging, to show log time; and for parsetime
from typing import TYPE_CHECKING

import discord

from extensions.settings.objects import (
    AttributeKeys,
    ServerSettings,
    MessageableGuildChannel,
)
from resources.checks.errors import MissingAttributesCheckFailure
from resources.checks.command_checks import is_in_dms
from .debug import debug, DebugColor

if TYPE_CHECKING:
    from resources.customs import Bot, GuildInteraction


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
    ticket_channel: MessageableGuildChannel | None = \
        client.get_guild_attribute(
            guild_id,
            AttributeKeys.ticket_create_channel
        )

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
    log_channel: discord.abc.Messageable | None = client.get_guild_attribute(
        guild, AttributeKeys.log_channel)
    if log_channel is None:
        if ignore_dms and is_in_dms(guild):
            return False
        if crash_if_not_found:
            raise MissingAttributesCheckFailure(
                "log_to_guild", [AttributeKeys.log_channel])

        # get current value for log_channel in the guild.
        if guild is None:
            attribute_raw = "<server was None>"
        else:
            guild_id = getattr(guild, "id", guild)
            assert type(guild_id) is int

            entry = await ServerSettings.get_entry(
                client.async_rina_db, guild_id)
            if entry is None:
                attribute_raw = "<no server data>"
            else:
                attribute_raw = str(entry["attribute_ids"].get(
                    AttributeKeys.log_channel, "<no attribute data>"))  # noqa

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

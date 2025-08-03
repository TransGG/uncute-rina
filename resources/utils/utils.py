from __future__ import annotations
from datetime import datetime, timezone
# ^ for logging, to show log time; and for parsetime
import logging  # for debug (logger.info)
import warnings  # for debug (if given wrong color)
from typing import TYPE_CHECKING

import discord

from extensions.settings.objects import (
    AttributeKeys,
    ServerSettings,
    MessageableGuildChannel,
)
from resources.checks.errors import MissingAttributesCheckFailure
from resources.checks.command_checks import is_in_dms
from resources.utils import DebugColor

if TYPE_CHECKING:
    from resources.customs import Bot, GuildInteraction


def debug(
        text: str = "",
        color: DebugColor = DebugColor.default,
        add_time: bool = True,
        end="\n",
        advanced=False
) -> None:
    # todo make all debug calls use DebugColor instead of string
    #  for `color`
    """
    Log a message to the console.

    :param text: The message you want to send to the console.
    :param color: The color you want to give your message
     ('red' for example).
    :param add_time: If you want to start the message with a
     '[2025-03-31T23:59:59.000001Z] [INFO]:'.
    :param end: What to end the end of the message with (similar
     to print(end='')).
    :param advanced: Whether to interpret `text` as advanced text
     (like minecraft in-chat colors). Replaces "&4" to red, "&l" to
     bold, etc. and "&&4" to a red background.
    """
    if type(text) is not str:
        text = repr(text)

    detail_color = {
        "&0": "40",
        "&8": "40",
        "&1": "44",
        "&b": "46",
        "&2": "42",
        "&a": "42",
        "&4": "41",
        "&c": "41",
        "&5": "45",
        "&d": "45",
        "&6": "43",
        "&e": "43",
        "&f": "47",
        "9": "34",
        "6": "33",
        "5": "35",
        "4": "31",
        "3": "36",
        "2": "32",
        "1": "34",
        "0": "30",
        "f": "37",
        "e": "33",
        "d": "35",
        "c": "31",
        "b": "34",
        "a": "32",
        "l": "1",
        "o": "3",
        "n": "4",
        "u": "4",
        "r": "0",
    }
    if advanced:
        for _detColor in detail_color:
            while "&" + _detColor in text:
                _text = text
                text = text.replace(
                    "m&" + _detColor,
                    ";" + detail_color[_detColor] + "m",
                    1
                )
                if _text == text:
                    # No previous coloring found to replace, so add a
                    #  new one instead. (no m&)
                    text = text.replace(
                        "&" + _detColor,
                        "\033[" + detail_color[_detColor] + "m",
                        1
                    )
        color = DebugColor.default

    if add_time:
        formatted_time_string = (datetime
                                 .now(timezone.utc)
                                 .strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
        time = f"{color.value}[{formatted_time_string}] [INFO]: "
    else:
        time = color.value
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger()
    # print = logger.info
    if end.endswith("\n"):
        end = end[:-2]
    logger.info(f"{time}{text}{DebugColor.default.value}"
                + end.replace('\r', '\033[F'))


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

        debug("Exception in log_channel (log_channel could not be loaded):\n"
              "    guild: " + repr(guild) +
              "\n"
              "    log_channel_id: " + attribute_raw +
              "\n"
              "    log message: " + msg, color=DebugColor.orange)
        return False

    await log_channel.send(
        content=msg,
        allowed_mentions=discord.AllowedMentions.none()
    )
    return True

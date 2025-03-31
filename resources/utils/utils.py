from __future__ import annotations
from datetime import datetime, timedelta, timezone  # for logging, to show log time; and for parsetime
from enum import Enum
import logging  # for debug (logger.info)
import warnings  # for debug (if given wrong color)
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from resources.customs.bot import Bot


TESTING_ENVIRONMENT = 2  # 1 = public test server (Supporter server) ; 2 = private test server (transplace staff only)


class DebugColor(Enum):
    # todo: move to own file
    default = "\033[0m"
    black = "\033[30m"
    red = "\033[31m"
    lime = "\033[32m"
    green = "\033[32m"
    yellow = "\033[33m"
    orange = "\033[33m"  # kinda orange i guess?
    blue = "\033[34m"
    magenta = "\033[35m"
    purple = "\033[35m"
    cyan = "\033[36m"
    gray = "\033[37m"
    lightblack = "\033[90m"
    darkgray = "\033[90m"
    lightred = "\033[91m"
    lightlime = "\033[92m"
    lightgreen = "\033[92m"
    lightyellow = "\033[93m"
    lightblue = "\033[94m"
    lightmagenta = "\033[95m"
    lightpurple = "\033[95m"
    lightcyan = "\033[96m"
    aqua = "\033[96m"
    lightgray = "\033[97m"
    white = "\033[97m"


def debug(
        text: str = "",
        color: DebugColor | str = DebugColor.default,
        add_time: bool =True,
        end="\n",
        advanced=False
) -> None:
    # todo make all debug calls use DebugColor instead of string for `color`
    """
    Log a message to the console.

    :param text: The message you want to send to the console.
    :param color: The color you want to give your message ('red' for example).
    :param add_time: If you want to start the message with a '[2025-03-31T23:59:59.000001Z] [INFO]:'.
    :param end: What to end the end of the message with (similar to print(end='')).
    :param advanced: Whether to interpret `text` as advanced text (like minecraft in-chat colors).
     Replaces "&4" to red, "&l" to bold, etc. and "&&4" to a red background.
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
                text = text.replace("m&" + _detColor, ";" + detail_color[_detColor] + "m", 1)
                if _text == text:
                    text = text.replace("&" + _detColor, "\033[" + detail_color[_detColor] + "m", 1)
        color = DebugColor.default
    else:
        if type(color) is str:
            color = color.replace(" ", "").replace("-", "").replace("_", "")
            color = getattr(DebugColor, color, None)
        if color is None:
            warnings.warn("Invalid color given for debug function: " + color, SyntaxWarning)
            color = DebugColor.default
    if add_time:
        time = f"{color.value}[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}] [INFO]: "
    else:
        time = color.value
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger()
    # print = logger.info
    if end.endswith("\n"):
        end = end[:-2]
    logger.info(f"{time}{text}{DebugColor.default.value}" + end.replace('\r', '\033[F'))


def get_mod_ticket_channel_id(client: Bot, guild_id: int | discord.Guild | discord.Interaction) -> int:
    """
    Fetch the #contact-staff ticket channel for a specific guild.

    :param client: Rina's Bot class to fetch ticket channel IDs (hardcoded).
    :param guild_id: A class with a guild_id or guild property.

    :return: The matching guild's ticket channel id.
    """
    if type(guild_id) is discord.Interaction:
        guild_id = guild_id.guild_id
    if type(guild_id) is discord.Guild:  # can be merged technically but whatevs
        guild_id = guild_id.guild_id

    if guild_id == client.custom_ids.get("enbyplace_server_id"):
        return client.custom_ids.get("enbyplace_ticket_channel_id")
    elif guild_id == client.custom_ids.get("transonance_server_id"):
        return client.custom_ids.get("transonance_ticket_channel_id")
    else:  # elif context.guild_id == client.custom_ids.get("transplace_server_id"):
        return client.custom_ids.get("transplace_ticket_channel_id")


async def log_to_guild(client: Bot, guild: discord.Guild, msg: str) -> None | discord.Message:
    """
    Log a message to a guild's logging channel (vcLog)

    :param client: The bot class with :py:func:`Bot.get_guild_info` to find logging channel.
    :param guild: Guild of the logging channel
    :param msg: Message you want to send to this logging channel

    :return: if client.vcLog channel is defined

    :raise KeyError: If client.vcLog channel is undefined.
     Note: It still outputs the given message to console and to the client's default log channel.
    """
    try:
        log_channel_id = await client.get_guild_info(guild, "vcLog")
    except KeyError:
        msg = "__**THIS MESSAGE CAUSES THE CRASH BELOW**__\n" + msg
        await client.log_channel.send(content=msg, allowed_mentions=discord.AllowedMentions.none())
        raise

    log_channel: discord.abc.GuildChannel | discord.Thread | None = client.get_channel(log_channel_id)
    if log_channel is None:
        debug("Exception in log_channel (log_channel could not be loaded):\n"
              "    guild: " + repr(guild) +
              "\n"
              "    log_channel_id: " + str(log_channel_id) +
              "\n"
              "    log message: " + msg, color="orange")
        return
    return await log_channel.send(content=msg, allowed_mentions=discord.AllowedMentions.none())


async def executed_in_dms(*,
        itx: discord.Interaction = None,
        message: discord.Message = None,
        channel: discord.DMChannel | discord.GroupChannel | discord.TextChannel | discord.StageChannel |
                 discord.VoiceChannel | discord.Thread = None
) -> bool:
    # make this a check
    """
    Make a command guild-only by telling people in DMs that they can't use the command

    :param itx: (used for interactions) The interaction to check if it was used in a server - and to reply to.
    :param message: (used for events) The message to check if it was used in a server.
    :param channel: The channel to check if it was used in a server.

    :return: if command was executed in DMs (for 'if ... : continue')

    :raise AssertionError: if the user provided not **exactly one** of [itx, message, channel] parameters.
    """
    assert len([i for i in [itx, message, channel] if i is not None]) == 1, ValueError(
        "Give an itx, message, or channel, not multiple!"
    )
    id_object: discord.Message | discord.Interaction | discord.TextChannel = next(
        i for i in [itx, message, channel] if i is not None)
    if id_object.server_id is None:
        await itx.response.send_message("This command is unavailable in DMs", ephemeral=True)
        return True
    return False

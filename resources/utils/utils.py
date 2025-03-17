from datetime import datetime, timedelta  # for logging, to show log time; and for parsetime
import logging  # for debug (logger.info)
import warnings  # for debug (if given wrong color)

import discord

from resources.customs.bot import Bot


__all__ = [
    "TESTING_ENVIRONMENT",
    "debug",
    "get_mod_ticket_channel_id",
    "log_to_guild",
    "executed_in_dms",
    "parse_date",
]


TESTING_ENVIRONMENT = 2  # 1 = public test server (Supporter server) ; 2 = private test server (transplace staff only)


def debug(text="", color="default", add_time=True, end="\n", advanced=False) -> None:
    """
    Log a message to the console

    Parameters
    -----------
    text: :class:`str`, optional
        The message you want to send to the console
    color: :class:`str`, optional
        The color you want to give your message ('red' for example)
    add_time: :class:`bool`, optional
        If you want to start the message with a '[23:59:59.000001] [INFO]:'
    end: :class:`str`, optional
        What to end the end of the message with (similar to print(end=''))
    advanced: :class:`bool`, optional
        Whether to interpret `text` as advanced text (like minecraft in-chat colors).
        Replaces "&4" to red, "&l" to bold, etc. and "&&4" to a red background.
    """
    if type(text) is not str:
        text = repr(text)

    colors = {
        "default": "\033[0m",
        "black": "\033[30m",
        "red": "\033[31m",
        "lime": "\033[32m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "orange": "\033[33m",  # kinda orange i guess?
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "purple": "\033[35m",
        "cyan": "\033[36m",
        "gray": "\033[37m",
        "lightblack": "\033[90m",
        "darkgray": "\033[90m",
        "lightred": "\033[91m",
        "lightlime": "\033[92m",
        "lightgreen": "\033[92m",
        "lightyellow": "\033[93m",
        "lightblue": "\033[94m",
        "lightmagenta": "\033[95m",
        "lightpurple": "\033[95m",
        "lightcyan": "\033[96m",
        "aqua": "\033[96m",
        "lightgray": "\033[97m",
        "white": "\033[97m",
    }
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
    color = color.replace(" ", "").replace("-", "").replace("_", "")
    if advanced:
        for _detColor in detail_color:
            while "&" + _detColor in text:
                _text = text
                text = text.replace("m&" + _detColor, ";" + detail_color[_detColor] + "m", 1)
                if _text == text:
                    text = text.replace("&" + _detColor, "\033[" + detail_color[_detColor] + "m", 1)
        color = "default"
    else:
        try:
            # is given color a valid option?
            colors[color]
        except KeyError:
            warnings.warn("Invalid color given for debug function: " + color, SyntaxWarning)
            color = "default"
    if add_time:
        time = f"{colors[color]}[{datetime.now().strftime('%H:%M:%S.%f')}] [INFO]: "
    else:
        time = colors[color]
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger()
    # print = logger.info
    if end.endswith("\n"):
        end = end[:-2]
    logger.info(f"{time}{text}{colors['default']}" + end.replace('\r', '\033[F'))


def get_mod_ticket_channel_id(client: Bot, guild_id: int | discord.Guild | discord.Interaction) -> int:
    """
    Fetch the #contact-staff ticket channel for a specific guild.

    Parameters
    -----------
    client: :class:`Bot`
        Rina's Bot class to fetch ticket channel IDs (hardcoded).
    guild_id: :class:`int` | :class:`discord.Guild` | :class:`discord.Interaction`
        A class with a guild_id or guild property.

    Returns
    --------
    :class:`int`
        The matching guild's ticket channel id.
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

    Parameters
    --------------
    client: :class:`Uncute_Rina.Bot`
        The bot class with `client.get_guild_info()` to find logging channel.
    guild: :class:`discord.Guild`
        Guild of the logging channel
    msg: :class:`str`
        Message you want to send to this logging channel

    Raises
    ----------
    :class:`KeyError`
        if client.vcLog channel is undefined.
        Note: It still outputs the given messge to console and to the client's default log channel.

    Returns
    -----------
    :class:`discord.Message`
        if client.vcLog channel is defined
    """
    try:
        log_channel_id = await client.get_guild_info(guild, "vcLog")
    except KeyError:
        msg = "__**THIS MESSAGE CAUSES THE CRASH BELOW**__\n" + msg
        await client.log_channel.send(content=msg, allowed_mentions=discord.AllowedMentions.none())
        raise

    log_channel: discord.abc.GuildChannel | discord.Thread | None = guild.get_channel(log_channel_id)
    if log_channel is None:
        log_channel = guild.get_thread(log_channel_id)
    if log_channel is None:
        debug("Exception in log_channel (log_channel could not be loaded):\n"
              "    guild: " + repr(guild) +
              "\n"
              "    log_channel_id: " + str(log_channel_id) +
              "\n"
              "    log message: " + msg, color="orange")
        return
    return await log_channel.send(content=msg, allowed_mentions=discord.AllowedMentions.none())


async def executed_in_dms(
        itx: discord.Interaction = None,
        message: discord.Message = None,
        channel: discord.DMChannel | discord.GroupChannel | discord.TextChannel | discord.StageChannel |
                 discord.VoiceChannel | discord.Thread = None
) -> bool:
    """
    Make a command guild-only by telling people in DMs that they can't use the command

    Parameters
    -----------
    itx: :class:`discord.Interaction`
        (used for interactions) The interaction to check if it was used in a server - and to reply to.
    message: :class:`discord.Message`
        (used for events) The message to check if it was used in a server.
    channel: :class:`discord.DMChannel` | :class:`discord.GuildChannel`
        The channel to check if it was used in a server.

    Returns
    --------
    :class:`bool`
        if command was executed in DMs (for 'if ... : continue')

    Raises
    -------
    :class:`AssertionError`
        if the user privided not **exactly one** of [itx, message, channel] parameters.
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

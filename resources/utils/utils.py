import discord
from datetime import datetime, timedelta # for logging, to show log time; and for parsetime
import logging # for debug (logger.info)
import warnings # for debug (if given wrong color)
from resources.customs.bot import Bot

__all__ = [
    "debug",
    "EnabledServers",
    "get_mod_ticket_channel_id",
    "thousand_space",
    "log_to_guild",
    "executed_in_dms"
]

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
        Whether to interpret `text` as advanced text (like minecraft in-chat colors). Replaces "&4" to red, "&l" to bold, etc. and "&&4" to a red background.
    """
    if type(text) is not str:
        text = repr(text)
    
    colors = {
        "default":"\033[0m",
        "black":"\033[30m",
        "red":"\033[31m",
        "lime":"\033[32m",
        "green":"\033[32m",
        "yellow":"\033[33m",
        "orange":"\033[33m", # kinda orange i guess?
        "blue":"\033[34m",
        "magenta":"\033[35m",
        "purple":"\033[35m",
        "cyan":"\033[36m",
        "gray":"\033[37m",
        "lightblack":"\033[90m",
        "darkgray":"\033[90m",
        "lightred":"\033[91m",
        "lightlime":"\033[92m",
        "lightgreen":"\033[92m",
        "lightyellow":"\033[93m",
        "lightblue":"\033[94m",
        "lightmagenta":"\033[95m",
        "lightpurple":"\033[95m",
        "lightcyan":"\033[96m",
        "aqua":"\033[96m",
        "lightgray":"\033[97m",
        "white":"\033[97m",
    }
    detailColor = {
        "&0" : "40",
        "&8" : "40",
        "&1" : "44",
        "&b" : "46",
        "&2" : "42",
        "&a" : "42",
        "&4" : "41",
        "&c" : "41",
        "&5" : "45",
        "&d" : "45",
        "&6" : "43",
        "&e" : "43",
        "&f" : "47",
        "9" : "34",
        "6" : "33",
        "5" : "35",
        "4" : "31",
        "3" : "36",
        "2" : "32",
        "1" : "34",
        "0" : "30",
        "f" : "37",
        "e" : "33",
        "d" : "35",
        "c" : "31",
        "b" : "34",
        "a" : "32",
        "l" : "1",
        "o" : "3",
        "n" : "4",
        "u" : "4",
        "r" : "0",
    }
    color = color.replace(" ","").replace("-","").replace("_","")
    if advanced:
        for _detColor in detailColor:
            while "&"+_detColor in text:
                _text = text
                text = text.replace("m&"+_detColor,";"+detailColor[_detColor]+"m",1)
                if _text == text:
                    text = text.replace("&"+_detColor,"\033["+detailColor[_detColor]+"m",1)
        color = "default"
    else:
        try:
            # is given color a valid option?
            colors[color]
        except KeyError:
            warnings.warn("Invalid color given for debug function: "+color, SyntaxWarning)
            color = "default"
    if add_time:
        time = f"{colors[color]}[{datetime.now().strftime('%H:%M:%S.%f')}] [INFO]: "
    else:
        time = colors[color]
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger()
    print = logger.info
    if end.endswith("\n"):
        end = end[:-2]
    print(f"{time}{text}{colors['default']}"+end.replace('\r','\033[F'))

def get_mod_ticket_channel_id(client: Bot, guild_id: int | discord.Guild | discord.Interaction):
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
    if type(guild_id) is discord.Guild: # can be merged technically but whatevs
        guild_id = guild_id.guild_id

    if guild_id == client.custom_ids.get("enbyplace_server_id"):
        return client.custom_ids.get("enbyplace_ticket_channel_id")
    elif guild_id == client.custom_ids.get("transonance_server_id"):
        return client.custom_ids.get("transonance_ticket_channel_id")
    else: #elif context.guild_id == client.custom_ids.get("transplace_server_id"):
        return client.custom_ids.get("transplace_ticket_channel_id")

#unused
def thousand_space(number, interval = 3, separator = " ") -> str:
    """
    Just use `f"{number:,}"` :|
    """
    decimals = []
    if type(number) is int or type(number) is float:
        number = str(number)
    if "." in number:
        "100.0.0"
        number, *decimals = number.split(".")
    for x in range(len(number)-interval,0,0-interval):
        number = number[:x]+separator+number[x:]
    decimals = ''.join(['.'+x for x in decimals])
    return number+decimals

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
        msg = "__**THIS MESSAGE CAUSES THE CRASH BELOW**__\n"+msg
        await client.log_channel.send(content=msg, allowed_mentions=discord.AllowedMentions.none())
        raise

    log_channel: discord.abc.GuildChannel | discord.Thread | None = guild.get_channel(log_channel_id)
    if log_channel is None:
        log_channel = guild.get_thread(log_channel_id)
    if log_channel is None:
        debug("Exception in log_channel:\n"
              "    guild: "+repr(guild)+"\n"
              "    log_channel_id: "+str(log_channel_id),color="orange")
        return
    return await log_channel.send(content=msg, allowed_mentions=discord.AllowedMentions.none())

async def executed_in_dms(itx: discord.Interaction = None, 
                          message: discord.Message = None,
                          channel: discord.DMChannel    | discord.GroupChannel | discord.TextChannel |
                                   discord.StageChannel | discord.VoiceChannel | discord.Thread      = None) -> bool:
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
    assert len([i for i in [itx, message, channel] if i is not None]) == 1, ValueError("Give an itx, message, or channel, not multiple!")
    id_object: discord.Message | discord.Interaction | discord.TextChannel = next(i for i in [itx, message, channel] if i is not None)
    if id_object.server_id is None:
        if type(id_object) == discord.Message:
            # Technically you could check if `channel` is DMChannel, but server_id==None should catch this too.
            await id_object.channel.send("This command is unavailable in DMs", ephemeral=True)
            return True
        await id_object.send("This command is unavailable in DMs", ephemeral=True)
        return True
    return False

def parse_date(time_string, now: datetime):
    # - "next thursday at 3pm"
    # - "tomorrow"
    # + "in 3 days"
    # + "2d"
    # - "2022-07-03"
    # + "2022y4mo3days"
    # - "<t:293847839273>"
    timeterms = {
        "y":["y","year","years"],
        "M":["mo","month","months"],
        "w":["w","week","weeks"],
        "d":["d","day","days"],
        "h":["h","hour","hours"],
        "m":["m","min","mins","minute","minutes"],
        "s":["s","sec", "secs","second","seconds"]
    }

    time_units = []
    low_index = 0
    number_index = 0
    is_number = True

    def magic_date_split(index, low_index, number_index) -> list[float]:
        try:
            time = [float(time_string[low_index:number_index + 1])]
        except ValueError:
            raise ValueError(f"The value for your date/time has to be a number (0, 1, 2) not '{time_string[low_index:number_index + 1]}'")
        date = time_string[number_index + 1:index]
        for unit in timeterms:
            if date in timeterms[unit]:
                time.append(unit)
                break
        else:
            raise ValueError(f"You can't use '{date}' as unit for your date/time")
        return time
    
    index = 0 #for making my IDE happy
    for index in range(len(time_string)):
        # for index in "14days7hours": get index of the first number, the last number, and the last letter before the next number:
        #    "1" to "<d" (until but not including "d") and "<7" -> so "1" to "4" and "d" to "s"
        # then it converts "14" to a number and "days" to the timedict of "d", so you get [[14,'d'], [7,'h']]
        if time_string[index] in "0123456789.":
            if not is_number:
                time_units.append(magic_date_split(index, low_index, number_index))
                low_index = index
            number_index = index
            is_number = True
        else:
            is_number = False
    time_units.append(magic_date_split(index + 1, low_index, number_index))

    timedict = {
        "y":now.year,
        "M":now.month,
        "d":now.day-1,
        "h":now.hour,
        "m":now.minute,
        "s":now.second,
        "f":0, # microseconds can only be set with "0.04s" eg.
        # now.day-1 for _timedict["d"] because later, datetime(day=...) starts with 1, and adds this value with
        # timedelta. This is required cause the datetime() doesn't let you set "0" for days. (cuz a month starts
        # at day 1)
    }
    
    # add values to each timedict key
    for unit in time_units:
        if unit[1] == "w":
            timedict["d"] += 7*unit[0]
        else:
            timedict[unit[1]] += unit[0]
    
    # check non-whole numbers, and shift "0.2m" to 0.2*60 = 12 seconds
    def decimals(time):
        return time - int(time)
    def is_whole(time):
        return time - int(time) == 0
    
    if not is_whole(timedict["y"]):
        timedict["M"] += decimals(timedict["y"]) * 12
        timedict["y"] = int(timedict["y"])
    if not is_whole(timedict["M"]):
        timedict["d"] += decimals(timedict["M"]) * (365.2425 / 12)
        timedict["M"] = int(timedict["M"])
    if not is_whole(timedict["d"]):
        timedict["h"] += decimals(timedict["d"]) * 24
        timedict["d"] = int(timedict["d"])
    if not is_whole(timedict["h"]):
        timedict["m"] += decimals(timedict["h"]) * 60
        timedict["h"] = int(timedict["h"])
    if not is_whole(timedict["m"]):
        timedict["s"] += decimals(timedict["m"]) * 60
        timedict["m"] = int(timedict["m"])
    if not is_whole(timedict["s"]):
        timedict["f"] += decimals(timedict["s"]) * 1000000
        timedict["s"] = int(timedict["s"])
    
    # check overflows
    while timedict["s"] >= 60:
        timedict["s"] -= 60
        timedict["m"] += 1
    while timedict["m"] >= 60:
        timedict["m"] -= 60
        timedict["h"] += 1
    while timedict["h"] >= 24:
        timedict["h"] -= 24
        timedict["d"] += 1
    while timedict["M"] > 12:
        timedict["M"] -= 12
        timedict["y"] += 1
    if timedict["y"] >= 3999 or timedict["d"] >= 1500000:
        raise ValueError("I don't think I can remind you in that long!")
    
    timedict = {i:int(timedict[i]) for i in timedict}
    
    distance = datetime(timedict["y"],timedict["M"],1,timedict["h"],timedict["m"],timedict["s"])
    # cause you cant have >31 days in a month, but if overflow is given, then let this timedelta calculate the new months/years
    distance += timedelta(days=timedict["d"])

    return distance

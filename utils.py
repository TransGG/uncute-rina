from Uncute_Rina import *

def is_verified(itx: discord.Interaction) -> bool:
    """
    Check if someone is verified

    ### Parameters:
    itx: :class:`discord.Interaction`
        interaction with itx.guild.roles and itx.user.roles
    
    ### Returns
    `bool` is_verified
    """
    if itx.guild is None:
        return False
    roles = [discord.utils.find(lambda r: r.name.lower() == 'verified', itx.guild.roles)]
    user_role_ids = [role.id for role in itx.user.roles]
    role_ids = [959748411844874240,  # Transplace: Verified
                1109907941454258257] # Transonance: Verified
    return len(set(roles).intersection(itx.user.roles)) > 0 or is_staff(itx) or len(set(role_ids).intersection(user_role_ids)) > 0

# def isVerifier(itx: discord.Interaction):
#     roles = [discord.utils.find(lambda r: r.name == 'Verifier', itx.guild.roles)]
#     return len(set(roles).intersection(itx.user.roles)) > 0 or is_admin(itx)

def is_staff(itx: discord.Interaction) -> bool:
    """
    Check if someone is staff

    ### Parameters:
    itx: :class:`discord.Interaction`
        interaction with itx.guild.roles and itx.user.roles
    
    ### Returns
    `bool` is_staff
    """
    if itx.guild is None:
        return False
    # case sensitive lol
    roles = [discord.utils.find(lambda r: 'staff'     in r.name.lower(), itx.guild.roles),
             discord.utils.find(lambda r: 'moderator' in r.name.lower(), itx.guild.roles),
             discord.utils.find(lambda r: 'trial mod' in r.name.lower(), itx.guild.roles),
             discord.utils.find(lambda r: 'sr. mod'   in r.name.lower(), itx.guild.roles),
             discord.utils.find(lambda r: 'chat mod'  in r.name.lower(), itx.guild.roles)]
    user_role_ids = [role.id for role in itx.user.roles]
    role_ids = [1069398630944997486,981735650971775077, #TransPlace: trial ; moderator
                1108771208931049544] # Transonance: Staff
    return len(set(roles).intersection(itx.user.roles)) > 0 or is_admin(itx) or len(set(role_ids).intersection(user_role_ids)) > 0

def is_admin(itx: discord.Interaction) -> bool:
    """
    Check if someone is an admin

    ### Parameters:
    itx: :class:`discord.Interaction`
        interaction with itx.guild.roles and itx.user
    
    ### Returns
    `bool` is_admin
    """
    if itx.guild is None:
        return False
    roles = [discord.utils.find(lambda r: r.name.lower() == 'full admin', itx.guild.roles),
             discord.utils.find(lambda r: r.name.lower() == 'head staff', itx.guild.roles),
             discord.utils.find(lambda r: r.name.lower() == 'admins'    , itx.guild.roles),
             discord.utils.find(lambda r: r.name.lower() == 'admin'     , itx.guild.roles),
             discord.utils.find(lambda r: r.name.lower() == 'owner'     , itx.guild.roles)]
    user_role_ids = [role.id for role in itx.user.roles]
    role_ids = [981735525784358962]  # TransPlace: Admin
    has_admin = itx.permissions.administrator
    return has_admin or len(set(roles).intersection(itx.user.roles)) > 0 or itx.user.id == 262913789375021056 or len(set(role_ids).intersection(user_role_ids)) > 0

def debug(text="", color="default", add_time=True, end="\n", advanced=False) -> None:
    """
    Log a message to the console

    ### Parameters:
    text: :class:`str`
        The message you want to send to the console
    color (optional): :class:`str`
        The color you want to give your message ('red' for example)
    add_time (optional): :class:`bool`
        If you want to start the message with a '[23:59:59.000001] [INFO]:'
    end (optional): :class:`str`
        What to end the end of the message with (similar to print(end=''))
    advanced (optional) :class:`bool`
        Whether to interpret `text` as advanced text (like minecraft in-chat colors). Replaces "&4" to red, "&l" to bold, etc. and "&&4" to a red background.
    """

    colors = {
        "default":"\033[0m",
        "black":"\033[30m",
        "red":"\033[31m",
        "lime":"\033[32m",
        "green":"\033[32m",
        "yellow":"\033[33m",
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

    ### Parameters
    --------------
    client: :class:`Uncute_Rina.Bot`
        The bot class with `client.get_command_info()`
    guild: :class:`discord.Guild`
        Guild of the logging channel
    msg: :class:`str`
        Message you want to send to this logging channel

    ### Raises
    ----------
    :class:`KeyError` if client.vcLog channel is undefined.
        Note: It still outputs the given messge to console and to the client's default log channel.
    
    ### Returns
    -----------
    :class:`discord.Message` if client.vcLog channel is defined
    """
    try:
        log_channel_id = await client.get_guild_info(guild, "vcLog")
    except KeyError:
        msg = "__**THIS MESSAGE CAUSES THE CRASH BELOW**__\n"+msg
        await client.logChannel.send(content=msg, allowed_mentions=discord.AllowedMentions.none())
        raise
    log_channel = guild.get_channel(log_channel_id)
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

    ### Parameters:
    itx: :class:`discord.Interaction` (used for interactions)
        The interaction to check if it was used in a server - and to reply to
    message: :class:`discord.Message` (used for events)
        The message to check if it was used in a server
    channel: DMChannel or Guild channel
        The channel to check if it was used in a server

    ### Returns:
    :class:`bool` if command was executed in DMs (for 'if ... : continue')
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

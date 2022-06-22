import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from datetime import datetime, timedelta
import warnings #used to warn for invalid color thingy in the debug function

def isVerified(itx: discord.Interaction):
    roles = [discord.utils.find(lambda r: r.name == 'Verified', itx.guild.roles)]
    return len(set(roles).intersection(itx.user.roles)) > 0 or isStaff(itx)

# def isVerifier(itx: discord.Interaction):
#     roles = [discord.utils.find(lambda r: r.name == 'Verifier', itx.guild.roles)]
#     return len(set(roles).intersection(itx.user.roles)) > 0 or isAdmin(itx)

def isStaff(itx: discord.Interaction):
    roles = [discord.utils.find(lambda r: r.name == 'Core Staff', itx.guild.roles),
             discord.utils.find(lambda r: r.name == 'Moderator' , itx.guild.roles),
             discord.utils.find(lambda r: r.name == 'Chat Mod'  , itx.guild.roles)]
    return len(set(roles).intersection(itx.user.roles)) > 0 or isAdmin(itx)

def isAdmin(itx: discord.Interaction):
    roles = [discord.utils.find(lambda r: r.name == 'Full Admin', itx.guild.roles),
             discord.utils.find(lambda r: r.name == 'Head Staff', itx.guild.roles),
             discord.utils.find(lambda r: r.name == 'Admin'     , itx.guild.roles)]
    return len(set(roles).intersection(itx.user.roles)) > 0 or itx.user.id == 262913789375021056

def debug(text="", color="default", addTime=True):
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
    color = color.replace(" ","").replace("-","").replace("_","")
    try:
        colors[color]
    except:
        warnings.warn("Invalid color given for debug function: "+color, SyntaxWarning)
        color="default"
    if addTime:
        time = f"{colors[color]}[{datetime.now().strftime('%H:%M:%S.%f')}] [INFO]:"
    else:
        time = colors[color]
    print(f"{time}{text}{colors['default']}")

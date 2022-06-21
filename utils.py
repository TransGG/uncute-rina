import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making

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

import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *

import pymongo # for online database
from pymongo import MongoClient


class Addons(commands.Cog):
    def __init__(self, client):
        global RinaDB
        RinaDB = client.RinaDB
    
    @app_commands.command(name="say",description="Force Rina to repeat your wise words")
    @app_commands.describe(text="What will you make Rina repeat?")
    async def say(self, itx: discord.Interaction, text: str):
        if not isAdmin(itx):
            await itx.response.send_message("Hi. sorry.. It would be too powerful to let you very cool person use this command.",ephemeral=True) #todo
            return
        collection = RinaDB["guildInfo"]
        query = {"guild_id": itx.guild.id}
        guild = collection.find(query)
        try:
            guild = guild[0]
        except IndexError:
            debug("Not enough data is configured to do this action! Please fix this with `/editguildinfo`!",color="red")
            return
        try:
            vcLog      = guild["vcLog"]
            logChannel = itx.guild.get_channel(vcLog)
            await logChannel.send(f"{itx.user.nick or itx.user.name} ({itx.user.id}) said a message using Rina: {text}", allowed_mentions=discord.AllowedMentions.none())
            text = text.replace("[[\\n]]","\n").replace("[[del]]","")
            await itx.channel.send(f"{text}", allowed_mentions=discord.AllowedMentions.none())
        except:
            await itx.response.send_message("Oops. Something went wrong!",ephemeral=True)
            raise
        await itx.response.send_message("Successfully sent!", ephemeral=True)

async def setup(client):
    await client.add_cog(Addons(client))

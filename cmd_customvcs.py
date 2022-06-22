import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *
from datetime import datetime, timedelta
from time import mktime # for unix time code

import pymongo # for online database
from pymongo import MongoClient
mongoURI = open("mongo.txt","r").read()
cluster = MongoClient(mongoURI)
RinaDB = cluster["Rina"]

newVcs = {} # make your own vcs!

class CustomVcs(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        global newVcs
        collection = RinaDB["guildInfo"]
        query = {"guild_id": member.guild.id}
        guild = collection.find(query)
        try:
            guild = guild[0]
        except IndexError:
            debug("Not enough data is configured to do this action! Please fix this with `/editguildinfo`!",color="red")
            return
        vcHub      = guild["vcHub"]
        vcLog      = guild["vcLog"]
        vcNoMic    = guild["vcNoMic"]
        vcCategory = guild["vcCategory"]
        if after.channel is not None:
            if after.channel.id == vcHub:
                after.channel.category.id = vcCategory
                defaultName = "Untitled voice chat"
                vc = await after.channel.category.create_voice_channel(defaultName)
                await member.move_to(vc,reason=f"Opened a new voice channel through the vc hub thing.")
                nomicChannel = member.guild.get_channel(vcNoMic)
                await nomicChannel.send(f"Voice channel <#{vc.id}> ({vc.id}) created by <@{member.id}> ({member.id}). Use `/editvc` to edit the name/user limit.", allowed_mentions=discord.AllowedMentions.none())
                logChannel = member.guild.get_channel(vcLog)
                await logChannel.send(content=f"{member.nick or member.name} joined voice channel {vc.id} (with the default name).", allowed_mentions=discord.AllowedMentions.none())
        if before.channel is None:
            return
        if before.channel in before.channel.guild.voice_channels:
            if before.channel.category.id not in [vcCategory]:
                return
            if before.channel.id == vcHub: # avoid deleting the hub channel
                return
            if len(before.channel.members) == 0:
                # cmdChannel = discord.utils.find(lambda r: r.name == 'no-mic', before.channel.category.text_channels)
                # await cmdChannel.send(f"{member.nick or member.name} left voice channel \"{before.channel.name}\", and was the last one in it, so it was deleted. ({member.id})",delete_after=32, allowed_mentions = discord.AllowedMentions.none())
                await before.channel.delete()
                try:
                    del newVcs[before.channel.id]
                except KeyError:
                    pass #haven't edit the channel yet
                logChannel = member.guild.get_channel(vcLog)
                await logChannel.send(f"{member.nick or member.name} ({member.id}) left voice channel \"{before.channel.name}\" ({before.channel.name}), and was the last one in it, so it was deleted.", allowed_mentions=discord.AllowedMentions.none())


    @app_commands.command(name="editvc",description="Edit your voice channel name or user limit")
    @app_commands.describe(name="Give your voice channel a name!",
                           limit="Give your voice channel a user limit!")
    async def editVc(self, itx: discord.Interaction, name: str, limit: int = 0):
        global newVcs
        collection = RinaDB["guildInfo"]
        query = {"guild_id": itx.guild_id}
        guild = collection.find(query)
        try:
            guild = guild[0]
        except IndexError:
            await itx.response.send_message("Not enough data is configured to do this action! Please ask an admin to fix this with `/editguildinfo`!",ephemeral=True)
            return
        vcHub = guild["vcHub"]
        vcLog = guild["vcLog"]
        vcCategory = guild["vcCategory"]
        # vcHub      = guildInfo[str(itx.guild.id)]["vcHub"]
        # vcLog      = guildInfo[str(itx.guild.id)]["vcLog"]
        # vcCategory = guildInfo[str(itx.guild.id)]["vcCategory"]
        if not isVerified(itx):
            await itx.response.send_message("You don't have the right role to be able to execute this command! (sorrryyy)\n  (This project is still in early stages, if you think this is an error, please message MysticMia#7612)",ephemeral=True) #todo
            return
        if itx.user.voice is None:
            debug(f"{itx.user} tried to make a new vc channel but isn't connected to a voice channel",color="yellow")
            await itx.response.send_message("You must be connected to a voice channel to use this command",ephemeral=True)
            return
        channel = itx.user.voice.channel
        if channel.category.id not in [vcCategory] or channel.id == vcHub:
            await itx.response.send_message("You can't change that voice channel's name!",ephemeral=True)
            return
        if len(name) < 4:
            await itx.response.send_message("Your voice channel name needs to be at least 4 letters long!",ephemeral=True)
            return
        if len(name) > 35:
            await itx.response.send_message("Please don't make your voice channel name more than 35 letters long! (gets cut off/unreadable)",ephemeral=True)
            return
        if limit < 2 and limit != 0:
            await itx.response.send_message("The user limit of your channel must be a positive amount of people... (at least 2; or 0)",ephemeral=True)
            return
        if limit > 99:
            await itx.response.send_message("I don't think you need to prepare for that many people... (max 99, or 0 for infinite)\nIf you need to, message Mia to change the limit",ephemeral=True)
            return
        if name == "Untitled voice chat":
            await itx.response.send_message("Are you really going to change it to that..",ephemeral=True)

        if channel.id in newVcs:
            # if you have made 2 renames in the past 10 minutes already
            if len(newVcs[channel.id]) < 2:
                #ignore but still continue the command
                pass
            elif newVcs[channel.id][0]+600 > mktime(datetime.now().timetuple()):
                await itx.response.send_message("You can't edit your channel more than twice in 10 minutes! (bcuz discord :P)\n"+
                f"You can rename it again <t:{newVcs[channel.id][0]+600}:R> (<t:{newVcs[channel.id][0]+600}:t>).")
                # ignore entirely, don't continue command
                return
            else:
                # clear and continue command
                newVcs[channel.id] = []
        else:
            # create and continue command
            newVcs[channel.id] = []
        newVcs[channel.id].append(int(mktime(datetime.now().timetuple())))
        category = discord.utils.find(lambda r: r.name == 'VC'      , itx.guild.categories)
        verified = discord.utils.find(lambda r: r.name == 'Verifier', itx.guild.roles)
        limitInfo = [" with a user limit of "+str(limit) if limit > 0 else ""][0]
        logChannel = itx.guild.get_channel(vcLog)
        oldName = channel.name
        await channel.edit(reason=f"Voice channel renamed from \"{channel.name}\" to \"{name}\"{limitInfo}", user_limit=limit,name=name)
        await logChannel.send(f"Voice channel ({channel.id}) renamed from \"{oldName}\" to \"{name}\" (by {itx.user.nick or itx.user.name}, {itx.user.id}){limitInfo}", allowed_mentions=discord.AllowedMentions.none())
        await itx.response.send_message(f"Voice channel successfully renamed from \"{oldName}\" to \"{name}\""+limitInfo, ephemeral=True)#allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="editguildinfo",description="Edit guild settings (staff only)")
    @app_commands.describe(vc_hub="Mention the voice channel that should make a new voice channel when you join it",
                           vc_log="Mention the channel in which logs should be posted",
                           vc_category="Mention the category in which new voice channels should be created",
                           vc_nomic="Mention the channel in which guide messages are sent ([x] joined, use /editvc to rename ur vc)")
    async def editGuildInfo(self, itx: discord.Interaction, vc_hub: discord.VoiceChannel = None, vc_log: discord.TextChannel = None, vc_category: discord.CategoryChannel = None, vc_nomic: discord.TextChannel = None):
        if not isAdmin(itx):
            await itx.response.send_message("You don't have the right role to be able to execute this command! (sorrryyy)",ephemeral=True) #todo
            return

        query = {"guild_id": itx.guild_id}
        collection = RinaDB["guildInfo"]
        guildInfo = collection.find(query)

        # if str(itx.guild.id) not in guildInfo:
        #     guildInfo[str(itx.guild_id)] = {}
        if vc_hub is not None:
            collection.update_one(query, {"$set":{"vcHub":vc_hub.id}}, upsert=True)
            # guildInfo[str(itx.guild_id)]["vcHub"] = vc_hub.id
        if vc_log is not None:
            collection.update_one(query, {"$set":{"vcLog":vc_log.id}}, upsert=True)
            # guildInfo[str(itx.guild_id)]["vcLog"] = vc_log.id
        if vc_category is not None:
            collection.update_one(query, {"$set":{"vcCategory":vc_category.id}}, upsert=True)
            # guildInfo[str(itx.guild_id)]["vcCategory"] = vc_category.id
        if vc_nomic is not None:
            collection.update_one(query, {"$set":{"vcNoMic":vc_nomic.id}}, upsert=True)
            # guildInfo[str(itx.guild_id)]["vcNoMic"] = vc_nomic.id
        await itx.response.send_message("Edited the settings.",ephemeral=True)

async def setup(client):
    # client.add_command("toneindicator")
    await client.add_cog(CustomVcs(client))

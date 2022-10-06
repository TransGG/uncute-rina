import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *
from datetime import datetime, timedelta
from time import mktime # for unix time code

import pymongo # for online database
from pymongo import MongoClient

newVcs = {} # make your own vcs!

class CustomVcs(commands.Cog):
    def __init__(self, client):
        global RinaDB
        self.client = client
        RinaDB = client.RinaDB

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        global newVcs
        collection = RinaDB["guildInfo"]
        query = {"guild_id": member.guild.id}
        guild = collection.find_one(query)
        if guild is None:
            debug("Not enough data is configured to do this action! Please fix this with `/editguildinfo`!",color="red")
            return
        vcHub      = guild["vcHub"]
        vcLog      = guild["vcLog"]
        vcNoMic    = guild["vcNoMic"]
        vcCategory = guild["vcCategory"]
        if before.channel is None:
            pass
        elif before.channel in before.channel.guild.voice_channels:
            if before.channel.category.id not in [vcCategory]:
                pass
            elif before.channel.id == vcHub: # avoid deleting the hub channel
                pass
            elif len(before.channel.members) == 0:
                # cmdChannel = discord.utils.find(lambda r: r.name == 'no-mic', before.channel.category.text_channels)
                # await cmdChannel.send(f"{member.nick or member.name} left voice channel \"{before.channel.name}\", and was the last one in it, so it was deleted. ({member.id})",delete_after=32, allowed_mentions = discord.AllowedMentions.none())
                try:
                    del newVcs[before.channel.id]
                except KeyError:
                    pass #haven't edit the channel yet
                try:
                    await before.channel.delete()
                except discord.errors.NotFound:
                    logChannel = member.guild.get_channel(vcLog)
                    await logChannel.send(f"**WARNING!! Couldn't delete CustomVC channel** {member.nick or member.name} ({member.id}) left voice channel \"{before.channel.name}\" ({before.channel.id}), and was the last one in it, but it **could not be deleted!.**", allowed_mentions=discord.AllowedMentions.none())
                    raise
                logChannel = member.guild.get_channel(vcLog)
                await logChannel.send(f"{member.nick or member.name} ({member.id}) left voice channel \"{before.channel.name}\" ({before.channel.id}), and was the last one in it, so it was deleted.", allowed_mentions=discord.AllowedMentions.none())
        if after.channel is not None:
            if after.channel.id == vcHub:
                position = 0
                if after.channel.category.id == vcCategory:
                    position = 1
                defaultName = "Untitled voice chat"
                warning = ""
                after.channel.category.id = vcCategory
                try:
                    vc = await after.channel.category.create_voice_channel(defaultName,position=position)
                except discord.errors.HTTPException:
                    nomicChannel = member.guild.get_channel(vcNoMic)
                    await nomicChannel.send(f"COULDN'T CREATE CUSTOM VOICE CHANNEL: TOO MANY", allowed_mentions=discord.AllowedMentions.none())
                    logChannel = member.guild.get_channel(vcLog)
                    await logChannel.send(f"WARNING: COULDN'T CREATE CUSTOM VOICE CHANNEL: TOO MANY (max 50?)", allowed_mentions=discord.AllowedMentions.none())
                    raise
                try:
                    await member.move_to(vc,reason=f"Opened a new voice channel through the vc hub thing.")
                except Exception as ex:
                    warning = str(ex)+": User clicked the vcHub too fast, and it couldn't move them to their new channel\n"
                    await vc.delete()
                    try:
                        member.move_to(None, reason=f"Couldn't create a new Custom voice channel so kicked them from their current vc to prevent them staying in the main customvc hub")
                    except:
                        pass
                nomicChannel = member.guild.get_channel(vcNoMic)
                await nomicChannel.send(f"Voice channel <#{vc.id}> ({vc.id}) created by <@{member.id}> ({member.id}). Use `/editvc` to edit the name/user limit.", allowed_mentions=discord.AllowedMentions.none())
                logChannel = member.guild.get_channel(vcLog)
                await logChannel.send(content=warning+f"{member.nick or member.name} ({member.id}) created and joined voice channel {vc.id} (with the default name).", allowed_mentions=discord.AllowedMentions.none())


    @app_commands.command(name="editvc",description="Edit your voice channel name or user limit")
    @app_commands.describe(name="Give your voice channel a name!",
                           limit="Give your voice channel a user limit!")
    async def editVc(self, itx: discord.Interaction, name: str = None, limit: int = None):
        global newVcs
        if not isVerified(itx):
            await itx.response.send_message("You don't have the right role to be able to execute this command! (sorrryyy)\n  (This project is still in early stages, if you think this is an error, please message MysticMia#7612)",ephemeral=True) #todo
            return
        collection = RinaDB["guildInfo"]
        query = {"guild_id": itx.guild_id}
        guild = collection.find_one(query)
        if guild is None:
            await itx.response.send_message("Not enough data is configured to do this action! Please ask an admin to fix this with `/editguildinfo`!",ephemeral=True)
            return
        vcHub = guild["vcHub"]
        vcLog = guild["vcLog"]
        vcCategory = guild["vcCategory"]
        # vcHub      = guildInfo[str(itx.guild.id)]["vcHub"]
        # vcLog      = guildInfo[str(itx.guild.id)]["vcLog"]
        # vcCategory = guildInfo[str(itx.guild.id)]["vcCategory"]
        warning = ""
        if itx.user.voice is None:
            if isStaff(itx):
                class CustomVcStaffEditor(discord.ui.Modal, title='Edit a custom vc\'s channel'):
                    channel_id = discord.ui.TextInput(label='Channel Id', placeholder="Which channel do you want to edit", required=True)
                    name = discord.ui.TextInput(label='Name', placeholder="Give your voice channel a name", required=False)
                    limit = discord.ui.TextInput(label='Limit', placeholder="Give your voice channel a user limit", required=False)
                    #todo
                    async def on_submit(self, itx: discord.Interaction):
                        name = str(self.name)
                        if name == "":
                            name = None

                        try:
                            # limit = self.limit
                            channel_id = int(str(self.channel_id))
                        except:
                            await itx.response.send_message("Your channel id has to be .. number-able. It contains a non-integer character. In other words, there's something other than a number in your Channel Id box", ephemeral=True)
                            return

                        try:
                            # limit = self.limit
                            if str(self.limit) != "":
                                limit = int(str(self.limit))
                            else:
                                limit = None
                        except:
                            await itx.response.send_message("I can only set the limit to a whole number...", ephemeral=True)
                            return

                        try:
                            channel = itx.guild.get_channel(channel_id)
                            if type(channel) is not discord.VoiceChannel:
                                await itx.response.send_message("This isn't a voice channel. You can't edit this channel.", ephemeral=True)
                        except discord.errors.HTTPException as ex:
                            await itx.response.send_message("Retrieving this channel failed. Perhaps a connection issue?", ephemeral=True)
                            return
                        except Exception as ex:
                            await itx.response.send_message("Sorry, I couldn't find that channel. Are you sure you have the correct **voice** channel id?",ephemeral=True)
                            raise
                            return

                        warning = ""
                        if channel.category.id not in [vcCategory] or channel.id == vcHub:
                            await itx.response.send_message("You can't change that voice channel's name (not with this command, at least)!",ephemeral=True)
                            return
                        if name is not None:
                            if len(name) < 4:
                                await itx.response.send_message("Make the voice channel name  at least 4 letters long, please. For readability",ephemeral=True)
                                return
                            if len(name) > 35:
                                await itx.response.send_message("Please keep the voice channels under 35 characters. They get spammy (gets cut off/unreadable)",ephemeral=True)
                                return
                            if name == "Untitled voice chat":
                                warning += "Are you really going to change it to that..\n"
                        if limit is not None:
                            if limit < 2 and limit != 0:
                                await itx.response.send_message("The user limit of your channel must be a positive amount of people... (at least 2; or 0)",ephemeral=True)
                                return
                            if limit > 99:
                                await itx.response.send_message("I can't set a limit above 99. Set the limit to 0 instead, for infinte members.",ephemeral=True)
                                return

                        if channel.id in newVcs:
                            # if you have made 2 renames in the past 10 minutes already
                            if len(newVcs[channel.id]) < 3:
                                #ignore but still continue the command
                                pass
                            elif newVcs[channel.id][0]+600 > mktime(datetime.now().timetuple()):
                                await itx.response.send_message("You can't edit channels more than twice in 10 minutes. Discord API limits queue the edit instead.\n"+
                                f"I have queued your previous renaming edit. You can rename it again <t:{newVcs[channel.id][0]+600}:R> (<t:{newVcs[channel.id][0]+600}:t>).", ephemeral = True)
                                # ignore entirely, don't continue command
                                return
                            else:
                                # clear and continue command
                                newVcs[channel.id] = []
                        else:
                            # create and continue command
                            newVcs[channel.id] = []
                        limitInfo = ""
                        logChannel = itx.guild.get_channel(vcLog)
                        oldName = channel.name
                        oldLimit = channel.user_limit
                        try:
                            if limit is None:
                                if name is None:
                                    await itx.response.send_message("You can edit a channel with this command. Set a value for the name or the maximum user limit.", ephemeral=True)
                                else:
                                    await channel.edit(reason=f"Staff: Voice channel renamed from \"{channel.name}\" to \"{name}\"{limitInfo}", name=name)
                                    await logChannel.send(f"Staff: Voice channel ({channel.id}) renamed from \"{oldName}\" to \"{name}\" (by {itx.user.nick or itx.user.name}, {itx.user.id})", allowed_mentions=discord.AllowedMentions.none())
                                    await itx.response.send_message(warning+f"Staff: Voice channel successfully renamed to \"{name}\"", ephemeral=True)#allowed_mentions=discord.AllowedMentions.none())
                                newVcs[channel.id].append(int(mktime(datetime.now().timetuple())))
                            else:
                                if name is None:
                                    await channel.edit(reason=f"Staff: Voice channel limit edited from \"{oldLimit}\" to \"{limit}\"", user_limit=limit)
                                    await logChannel.send(f"Staff: Voice channel \"{oldName}\" ({channel.id}) edited the user limit from  \"{oldLimit}\" to \"{limit}\" (by {itx.user.nick or itx.user.name}, {itx.user.id}){limitInfo}", allowed_mentions=discord.AllowedMentions.none())
                                    await itx.response.send_message(warning+f"Staff: Voice channel user limit for \"{oldName}\" successfully edited from \"{oldLimit}\" to \"{limit}\"", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                                else:
                                    await channel.edit(reason=f"Staff: Voice channel edited from name: \"{channel.name}\" to \"{name}\" and user limit from: \"{limit}\" to \"{oldLimit}\"", user_limit=limit,name=name)
                                    await logChannel.send(f"Staff: {itx.user.nick or itx.user.name} ({itx.user.id}) changed VC ({channel.id}) name \"{oldName}\" to \"{name}\" and user limit from \"{oldLimit}\" to \"{limit}\"{limitInfo}", allowed_mentions=discord.AllowedMentions.none())
                                    await itx.response.send_message(warning+f"Staff: Voice channel edited name and user limit successfully edited.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                                    newVcs[channel.id].append(int(mktime(datetime.now().timetuple())))
                        except discord.errors.HTTPException as ex:
                            await logChannel.send("Staff: Warning! >> "+ex.message+f" << {itx.user.nick or itx.user.name} ({itx.user.id}) tried to change {oldName} ({channel.id}) to {name}, but wasn't allowed to by discord, probably because it's in a banned word list for discord's discovery <@262913789375021056>")

                await itx.response.send_modal(CustomVcStaffEditor())
                return
            debug(f"{itx.user} tried to make a new vc channel but isn't connected to a voice channel",color="yellow")
            await itx.response.send_message("You must be connected to a voice channel to use this command",ephemeral=True)
            return
        channel = itx.user.voice.channel
        if channel.category.id not in [vcCategory] or channel.id == vcHub:
            await itx.response.send_message("You can't change that voice channel's name!",ephemeral=True)
            return
        if name is not None:
            if len(name) < 4:
                await itx.response.send_message("Your voice channel name needs to be at least 4 letters long!",ephemeral=True)
                return
            if len(name) > 35:
                await itx.response.send_message("Please don't make your voice channel name more than 35 letters long! (gets cut off/unreadable)",ephemeral=True)
                return
            if name == "Untitled voice chat":
                warning += "Are you really going to change it to that..\n"
        if limit is not None:
            if limit < 2 and limit != 0:
                await itx.response.send_message("The user limit of your channel must be a positive amount of people... (at least 2; or 0)",ephemeral=True)
                return
            if limit > 99:
                await itx.response.send_message("I don't think you need to prepare for that many people... (max 99, or 0 for infinite)\nIf you need to, message Mia to change the limit",ephemeral=True)
                return

        if channel.id in newVcs:
            # if you have made 2 renames in the past 10 minutes already
            if name is None:
                # don't add cooldown if you only change the limit, not the name
                pass
            elif len(newVcs[channel.id]) < 2:
                #ignore but still continue the command
                pass
            elif newVcs[channel.id][0]+600 > mktime(datetime.now().timetuple()):
                await itx.response.send_message("You can't edit your channel more than twice in 10 minutes! (bcuz discord :P)\n"+
                f"You can rename it again <t:{newVcs[channel.id][0]+600}:R> (<t:{newVcs[channel.id][0]+600}:t>).", ephemeral = True)
                # ignore entirely, don't continue command
                return
            else:
                # clear and continue command
                newVcs[channel.id] = []
        else:
            # create and continue command
            newVcs[channel.id] = []
        limitInfo = ""
        logChannel = itx.guild.get_channel(vcLog)
        oldName = channel.name
        oldLimit = channel.user_limit
        try:
            if limit is None:
                if name is None:
                    await itx.response.send_message("You can edit your channel with this command. Set a value for the name or the maximum user limit.", ephemeral=True)
                else:
                    await channel.edit(reason=f"Voice channel renamed from \"{channel.name}\" to \"{name}\"{limitInfo}", name=name)
                    await logChannel.send(f"Voice channel ({channel.id}) renamed from \"{oldName}\" to \"{name}\" (by {itx.user.nick or itx.user.name}, {itx.user.id})", allowed_mentions=discord.AllowedMentions.none())
                    await itx.response.send_message(warning+f"Voice channel successfully renamed to \"{name}\"", ephemeral=True)#allowed_mentions=discord.AllowedMentions.none())
                newVcs[channel.id].append(int(mktime(datetime.now().timetuple())))
            else:
                if name is None:
                    await channel.edit(reason=f"Voice channel limit edited from \"{oldLimit}\" to \"{limit}\"", user_limit=limit)
                    await logChannel.send(f"Voice channel \"{oldName}\" ({channel.id}) edited the user limit from  \"{oldLimit}\" to \"{limit}\" (by {itx.user.nick or itx.user.name}, {itx.user.id}){limitInfo}", allowed_mentions=discord.AllowedMentions.none())
                    await itx.response.send_message(warning+f"Voice channel user limit for \"{oldName}\" successfully edited from \"{oldLimit}\" to \"{limit}\"", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                else:
                    await channel.edit(reason=f"Voice channel edited from name: \"{channel.name}\" to \"{name}\" and user limit from: \"{limit}\" to \"{oldLimit}\"", user_limit=limit,name=name)
                    await logChannel.send(f"{itx.user.nick or itx.user.name} ({itx.user.id}) changed VC ({channel.id}) name \"{oldName}\" to \"{name}\" and user limit from \"{oldLimit}\" to \"{limit}\"{limitInfo}", allowed_mentions=discord.AllowedMentions.none())
                    await itx.response.send_message(warning+f"Voice channel edited name and user limit successfully edited.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                    newVcs[channel.id].append(int(mktime(datetime.now().timetuple())))
        except discord.errors.HTTPException as ex:
            await logChannel.send("Warning! >> "+ex.message+f" << {itx.user.nick or itx.user.name} ({itx.user.id}) tried to change {oldName} ({channel.id}) to {name}, but wasn't allowed to by discord, probably because it's in a banned word list for discord's discovery <@262913789375021056>")
        # await channel.edit(reason=f"Voice channel renamed from \"{channel.name}\" to \"{name}\"{limitInfo}", user_limit=limit,name=name) #todo
        # await logChannel.send(f"Voice channel ({channel.id}) renamed from \"{oldName}\" to \"{name}\" (by {itx.user.nick or itx.user.name}, {itx.user.id}){limitInfo}", allowed_mentions=discord.AllowedMentions.none())
        # await itx.response.send_message(warning+f"Voice channel successfully renamed from \"{oldName}\" to \"{name}\""+limitInfo, ephemeral=True)#allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="editguildinfo",description="Edit guild settings (staff only)")
    @app_commands.describe(vc_hub="Mention the voice channel that should make a new voice channel when you join it",
                           vc_log="Mention the channel in which logs should be posted",
                           vc_category="Mention the category in which new voice channels should be created",
                           vc_nomic="Mention the channel in which guide messages are sent ([x] joined, use /editvc to rename ur vc)",
                           star_channel="Mention the channel in which you want starboard messages to be sent",
                           star_minimum="How many star reactions must a message get before it is added to the starboard?")
    async def editGuildInfo(self, itx: discord.Interaction, vc_hub: discord.VoiceChannel = None, vc_log: discord.TextChannel = None, vc_category: discord.CategoryChannel = None, vc_nomic: discord.TextChannel = None, star_channel: discord.TextChannel = None, star_minimum: int = None):
        if not isAdmin(itx):
            await itx.response.send_message("You don't have the right role to be able to execute this command! (sorrryyy)",ephemeral=True) #todo
            return

        query = {"guild_id": itx.guild_id}
        collection = RinaDB["guildInfo"]

        if vc_hub is not None:
            collection.update_one(query, {"$set":{"vcHub":vc_hub.id}}, upsert=True)
        if vc_log is not None:
            collection.update_one(query, {"$set":{"vcLog":vc_log.id}}, upsert=True)
        if vc_category is not None:
            collection.update_one(query, {"$set":{"vcCategory":vc_category.id}}, upsert=True)
        if vc_nomic is not None:
            collection.update_one(query, {"$set":{"vcNoMic":vc_nomic.id}}, upsert=True)
        if star_channel is not None:
            collection.update_one(query, {"$set":{"starboardChannel":star_channel.id}}, upsert=True)
        if star_minimum is not None:
            collection.update_one(query, {"$set":{"starboardCountMinimum":star_minimum}}, upsert=True)

        await itx.response.send_message("Edited the settings.",ephemeral=True)

async def setup(client):
    await client.add_cog(CustomVcs(client))

import discord

from utils import * #imports 'discord import' and 'mongodb' things too
from datetime import datetime
from time import mktime # for unix time code

recently_renamed_vcs = {} # make your own vcs!
VcTable_prefix = "[T] "

class CustomVcs(commands.Cog):
    def __init__(self, client):
        global RinaDB
        self.client = client
        RinaDB = client.RinaDB
        self.blacklisted_channels = [959626329689583616, 960984256425893958, 960984642717102122, 961794293704581130]
        #  #General, #Private, #Quiet, and #Minecraft. Later, it also excludes channels starting with "〙"

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        global recently_renamed_vcs
        member: discord.Member
        before: discord.VoiceState
        after: discord.VoiceState
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
            elif before.channel.id in self.blacklisted_channels or \
                    before.channel.name.startswith('〙'):
                # new blacklisted channels: "#General" "#Quiet", "#Private" and "#Minecraft"
                pass
            elif len(before.channel.members) == 0:
                # cmdChannel = discord.utils.find(lambda r: r.name == 'no-mic', before.channel.category.text_channels)
                # await cmdChannel.send(f"{member.nick or member.name} left voice channel \"{before.channel.name}\", and was the last one in it, so it was deleted. ({member.id})",delete_after=32, allowed_mentions = discord.AllowedMentions.none())
                try:
                    del recently_renamed_vcs[before.channel.id]
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

            elif len(before.channel.overwrites) > len(before.channel.category.overwrites):  # if VcTable, reset ownership; and all owners leave: reset all perms
                reset_vctable = True #check if no owners left --> all members in the voice channel aren't owner
                for target in before.channel.overwrites:
                    if target not in before.channel.members:
                        continue
                    if before.channel.overwrites[target].speak:
                        reset_vctable = False
                        break
                if reset_vctable:
                    await before.channel.edit(overwrites=before.channel.category.overwrites) #reset overrides
                    await before.channel.send("This channel was converted from a VcTable back to a normal CustomVC because all the owners left")
                    # remove channel's name prefix (seperately from the overwrites due to things like ratelimiting)
                    if before.channel.name.startswith(VcTable_prefix):
                        new_channel_name = before.channel.name[len(VcTable_prefix):]
                        if before.channel.id not in recently_renamed_vcs:
                            recently_renamed_vcs[before.channel.id] = []
                        recently_renamed_vcs[before.channel.id].append(int(mktime(datetime.now().timetuple())))
                        await before.channel.edit(name=new_channel_name)
        if after.channel is not None:
            if after.channel.id == vcHub:
                default_name = "Untitled voice chat"
                warning = ""
                vcCategory_for_vc = after.channel.category
                vcCategory_for_vc.id = vcCategory
                try:
                    vc = await vcCategory_for_vc.create_voice_channel(default_name,position=after.channel.position+1)
                except discord.errors.HTTPException:
                    nomicChannel = member.guild.get_channel(vcNoMic)
                    await nomicChannel.send(f"COULDN'T CREATE CUSTOM VOICE CHANNEL: TOO MANY", allowed_mentions=discord.AllowedMentions.none())
                    logChannel = member.guild.get_channel(vcLog)
                    await logChannel.send(f"WARNING: COULDN'T CREATE CUSTOM VOICE CHANNEL: TOO MANY (max 50?)", allowed_mentions=discord.AllowedMentions.none())
                    raise
                try:
                    await member.move_to(vc,reason=f"Opened a new voice channel through the vc hub thing.")
                    for customVC in vcCategory_for_vc.voice_channels:
                        if customVC.id == vcHub or customVC.id == vc.id:
                            continue
                        await customVC.edit(position=customVC.position+1)
                except Exception as ex:
                    warning = str(ex)+": User clicked the vcHub too fast, and it couldn't move them to their new channel\n"
                    try:
                        await member.move_to(None, reason=f"Couldn't create a new Custom voice channel so kicked them from their current vc to prevent them staying in the main customvc hub")
                        # no need to delete vc if they are kicked out of the channel, cause then the next event will notice that they left the channel.
                    except:
                        await vc.delete()
                    await self.client.logChannel.send(content=warning,allowed_mentions=discord.AllowedMentions.none())
                    raise
                    # pass
                nomicChannel = member.guild.get_channel(vcNoMic)
                cmd_mention = self.client.getCommandMention("editvc")
                await nomicChannel.send(f"Voice channel <#{vc.id}> ({vc.id}) created by <@{member.id}> ({member.id}). Use {cmd_mention} to edit the name/user limit.", delete_after=120, allowed_mentions=discord.AllowedMentions.none())
                await self.client.logChannel.send(content=warning+f"{member.nick or member.name} ({member.id}) created and joined voice channel {vc.id} (with the default name).", allowed_mentions=discord.AllowedMentions.none())


    @app_commands.command(name="editvc",description="Edit your voice channel name or user limit")
    @app_commands.describe(name="Give your voice channel a name!",
                           limit="Give your voice channel a user limit!")
    async def editVc(self, itx: discord.Interaction, name: str = None, limit: int = None):
        global recently_renamed_vcs
        if not isVerified(itx):
            await itx.response.send_message("You can't edit voice channels because you aren't verified yet!",ephemeral=True)
            return
        collection = RinaDB["guildInfo"]
        query = {"guild_id": itx.guild_id}
        guild = collection.find_one(query)
        if guild is None:
            cmd_mention = self.client.getCommandMention("editguildinfo")
            await itx.response.send_message(f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention}!",ephemeral=True)
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
                    channel_id = discord.ui.TextInput(label='Channel Id', placeholder="Which channel do you want to edit")#, required=True)
                    name = discord.ui.TextInput(label='Name', placeholder="Give your voice channel a name", required=False)
                    limit = discord.ui.TextInput(label='Limit', placeholder="Give your voice channel a user limit", required=False)

                    async def on_submit(self, itx: discord.Interaction):
                        name = str(self.name)
                        if name == "":
                            name = None

                        try:
                            # limit = self.limit
                            channel_id = int(str(self.channel_id))
                        except ValueError:
                            await itx.response.send_message("Your channel id has to be .. number-able. It contains a non-integer character. In other words, there's something other than a number in your Channel Id box", ephemeral=True)
                            return

                        try:
                            # limit = self.limit
                            if str(self.limit) != "":
                                limit = int(str(self.limit))
                            else:
                                limit = None
                        except ValueError:
                            await itx.response.send_message("I can only set the limit to a whole number...", ephemeral=True)
                            return

                        try:
                            channel = itx.guild.get_channel(channel_id)
                            if type(channel) is not discord.VoiceChannel:
                                await itx.response.send_message("This isn't a voice channel. You can't edit this channel.", ephemeral=True)
                        except discord.errors.HTTPException:
                            await itx.response.send_message("Retrieving this channel failed. Perhaps a connection issue?", ephemeral=True)
                            return
                        except Exception:
                            await itx.response.send_message("Sorry, I couldn't find that channel. Are you sure you have the correct **voice** channel id?",ephemeral=True)
                            raise

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

                        if channel.id in recently_renamed_vcs:
                            # if you have made 2 renames in the past 10 minutes already
                            if len(recently_renamed_vcs[channel.id]) < 3:
                                #ignore but still continue the command
                                pass
                            elif recently_renamed_vcs[channel.id][0]+600 > mktime(datetime.now().timetuple()):
                                await itx.response.send_message(f"You can't edit channels more than twice in 10 minutes. Discord API limits queue the edit instead.\n" +
                                                                f"I have queued your previous renaming edit. You can rename it again <t:{recently_renamed_vcs[channel.id][0] + 600}:R> (<t:{recently_renamed_vcs[channel.id][0] + 600}:t>).", ephemeral=True)
                                # ignore entirely, don't continue command
                                return
                            else:
                                # clear and continue command
                                recently_renamed_vcs[channel.id] = []
                        else:
                            # create and continue command
                            recently_renamed_vcs[channel.id] = []
                        limit_info = ""
                        logChannel = itx.guild.get_channel(vcLog)
                        old_name = channel.name
                        old_limit = channel.user_limit
                        try:
                            if limit is None:
                                if name is None:
                                    await itx.response.send_message("You can edit a channel with this command. Set a value for the name or the maximum user limit.", ephemeral=True)
                                else:
                                    await channel.edit(reason=f"Staff: Voice channel renamed from \"{channel.name}\" to \"{name}\"{limit_info}", name=name)
                                    await logChannel.send(f"Staff: Voice channel ({channel.id}) renamed from \"{old_name}\" to \"{name}\" (by {itx.user.nick or itx.user.name}, {itx.user.id})", allowed_mentions=discord.AllowedMentions.none())
                                    await itx.response.send_message(warning+f"Staff: Voice channel successfully renamed to \"{name}\"", ephemeral=True)#allowed_mentions=discord.AllowedMentions.none())
                                recently_renamed_vcs[channel.id].append(int(mktime(datetime.now().timetuple())))
                            else:
                                if name is None:
                                    await channel.edit(reason=f"Staff: Voice channel limit edited from \"{old_limit}\" to \"{limit}\"", user_limit=limit)
                                    await logChannel.send(f"Staff: Voice channel \"{old_name}\" ({channel.id}) edited the user limit from  \"{old_limit}\" to \"{limit}\" (by {itx.user.nick or itx.user.name}, {itx.user.id}){limit_info}", allowed_mentions=discord.AllowedMentions.none())
                                    await itx.response.send_message(warning+f"Staff: Voice channel user limit for \"{old_name}\" successfully edited from \"{old_limit}\" to \"{limit}\"", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                                else:
                                    await channel.edit(reason=f"Staff: Voice channel edited from name: \"{channel.name}\" to \"{name}\" and user limit from: \"{limit}\" to \"{old_limit}\"", user_limit=limit,name=name)
                                    await logChannel.send(f"Staff: {itx.user.nick or itx.user.name} ({itx.user.id}) changed VC ({channel.id}) name \"{old_name}\" to \"{name}\" and user limit from \"{old_limit}\" to \"{limit}\"{limit_info}", allowed_mentions=discord.AllowedMentions.none())
                                    await itx.response.send_message(warning+f"Staff: Voice channel name and user limit successfully edited.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                                    recently_renamed_vcs[channel.id].append(int(mktime(datetime.now().timetuple())))
                        except discord.errors.HTTPException as ex:
                            ex_message = repr(ex).split("(", 1)[1][1:-2]
                            await logChannel.send("Staff: Warning! >> "+ex_message+f" << {itx.user.nick or itx.user.name} ({itx.user.id}) tried to change {old_name} ({channel.id}) to {name}, but wasn't allowed to by discord, probably because it's in a banned word list for discord's discovery <@262913789375021056>")

                await itx.response.send_modal(CustomVcStaffEditor())
                return
            # debug(f"{itx.user} tried to make a new vc channel but isn't connected to a voice channel",color="yellow")
            await itx.response.send_message("You must be connected to a voice channel to use this command",ephemeral=True)
            return
        channel = itx.user.voice.channel
        if channel.category.id not in [vcCategory] or \
                channel.id == vcHub or \
                channel.id in self.blacklisted_channels or \
                channel.name.startswith("〙"):
            await itx.response.send_message("You can't change that voice channel's name!",ephemeral=True)
            return
        if name is not None:
            if len(name) < 4:
                await itx.response.send_message("Your voice channel name needs to be at least 4 letters long!",ephemeral=True)
                return
            if len(name) > 35:
                await itx.response.send_message("Please don't make your voice channel name more than 35 letters long! (gets cut off/unreadable)",ephemeral=True)
                return
            if name.startswith("〙"):
                await itx.response.send_message("Due to the current layout, you can't change your channel to something starting with '〙'. Sorry for the inconvenience", ephemeral=True)
                return
            if name == "Untitled voice chat":
                warning += "Are you really going to change it to that..\n"
            if len(itx.user.voice.channel.overwrites) > len(itx.user.voice.channel.category.overwrites): # if VcTable, add prefix
                name = VcTable_prefix + name
        if limit is not None:
            if limit < 2 and limit != 0:
                await itx.response.send_message("The user limit of your channel must be a positive amount of people... (at least 2; or 0)",ephemeral=True)
                return
            if limit > 99:
                await itx.response.send_message("I don't think you need to prepare for that many people... (max 99, or 0 for infinite)\nIf you need to, message Mia to change the limit",ephemeral=True)
                return

        if channel.id in recently_renamed_vcs:
            # if you have made 2 renames in the past 10 minutes already
            if name is None:
                # don't add cooldown if you only change the limit, not the name
                pass
            elif len(recently_renamed_vcs[channel.id]) < 2:
                #ignore but still continue the command
                pass
            elif recently_renamed_vcs[channel.id][0]+600 > mktime(datetime.now().timetuple()):
                await itx.response.send_message(f"You can't edit your channel more than twice in 10 minutes! (bcuz discord :P)\n" +
                                                f"You can rename it again <t:{recently_renamed_vcs[channel.id][0] + 600}:R> (<t:{recently_renamed_vcs[channel.id][0] + 600}:t>).", ephemeral=True)
                # ignore entirely, don't continue command
                return
            else:
                # clear and continue command
                recently_renamed_vcs[channel.id] = []
        else:
            # create and continue command
            recently_renamed_vcs[channel.id] = []
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
                recently_renamed_vcs[channel.id].append(int(mktime(datetime.now().timetuple())))
            else:
                if name is None:
                    await channel.edit(reason=f"Voice channel limit edited from \"{oldLimit}\" to \"{limit}\"", user_limit=limit)
                    await logChannel.send(f"Voice channel \"{oldName}\" ({channel.id}) edited the user limit from  \"{oldLimit}\" to \"{limit}\" (by {itx.user.nick or itx.user.name}, {itx.user.id}){limitInfo}", allowed_mentions=discord.AllowedMentions.none())
                    await itx.response.send_message(warning+f"Voice channel user limit for \"{oldName}\" successfully edited from \"{oldLimit}\" to \"{limit}\"", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                else:
                    await channel.edit(reason=f"Voice channel edited from name: \"{channel.name}\" to \"{name}\" and user limit from: \"{limit}\" to \"{oldLimit}\"", user_limit=limit,name=name)
                    await logChannel.send(f"{itx.user.nick or itx.user.name} ({itx.user.id}) changed VC ({channel.id}) name \"{oldName}\" to \"{name}\" and user limit from \"{oldLimit}\" to \"{limit}\"{limitInfo}", allowed_mentions=discord.AllowedMentions.none())
                    await itx.response.send_message(warning+f"Voice channel name and user limit successfully edited.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                    recently_renamed_vcs[channel.id].append(int(mktime(datetime.now().timetuple())))
        except discord.errors.HTTPException as ex:
            ex_message = repr(ex).split("(", 1)[1][1:-2]
            await logChannel.send("Warning! >> "+ex_message+f" << {itx.user.nick or itx.user.name} ({itx.user.id}) tried to change {oldName} ({channel.id}) to {name}, but wasn't allowed to by discord, probably because it's in a banned word list for discord's discovery <@262913789375021056>")
        # await channel.edit(reason=f"Voice channel renamed from \"{channel.name}\" to \"{name}\"{limitInfo}", user_limit=limit,name=name) #todo
        # await logChannel.send(f"Voice channel ({channel.id}) renamed from \"{oldName}\" to \"{name}\" (by {itx.user.nick or itx.user.name}, {itx.user.id}){limitInfo}", allowed_mentions=discord.AllowedMentions.none())
        # await itx.response.send_message(warning+f"Voice channel successfully renamed from \"{oldName}\" to \"{name}\""+limitInfo, ephemeral=True)#allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="editguildinfo",description="Edit guild settings (staff only)")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='VC Hub (which channel makes new Custom-VCs?)', value=1),
        discord.app_commands.Choice(name="Log (which channel logs Rina's messages?)", value=2),
        discord.app_commands.Choice(name='VC category (Where do these new channels get created?)', value=3),
        discord.app_commands.Choice(name='No-mic (Which channel to use for Custom VC no-mic messages?', value=4),
        discord.app_commands.Choice(name='Starboard channel (where are starboard messages sent?)', value=5),
        discord.app_commands.Choice(name='Star minimum (How many stars should a message get before starboarded', value=6),
    ])
    @app_commands.describe(mode="What mode do you want to use?",
                           value="Fill in the value/channel-id of the thing/channel you want to edit")
    async def editGuildInfo(self, itx: discord.Interaction, mode: int, value: str):
        if not isAdmin(itx):
            await itx.response.send_message("You don't have the right role to be able to execute this command! (sorrryyy)",ephemeral=True) #todo
            return

        query = {"guild_id": itx.guild_id}
        collection = RinaDB["guildInfo"]

        modes = [
            "", #0
            "vc hub", #1
            "log", #2
            "vc category", #3
            "no-mic", #4
            "star channel", #5
            "star minimum" #6
        ]
        mode = modes[mode]

        async def to_int(value, error_msg):
            try:
                return int(value)
            except ValueError:
                await itx.response.send_message(error_msg, ephemeral=True)
                return None

        if mode == "vc hub":
            if value is not None:
                value = await to_int(value, "You have to give a numerical ID for the channel you want to use!")
                if value is None:
                    return
                ch = self.client.get_channel(value)
                if type(ch) is not discord.VoiceChannel:
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking for! (Need <class 'discord.VoiceChannel'>, got {type(ch)})", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {"vcHub": ch.id}}, upsert=True)
        elif mode == "log":
            if value is not None:
                value = await to_int(value, "You have to give a numerical ID for the channel you want to use!")
                if value is None:
                    return
                ch = self.client.get_channel(value)
                if type(ch) is not discord.TextChannel:
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking for! (Need <class 'discord.TextChannel'>, got {type(ch)})", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {"vcLog": ch.id}}, upsert=True)
        elif mode == "vc category":
            if value is not None:
                value = await to_int(value, "You have to give a numerical ID for the category you want to use!")
                if value is None:
                    return
                ch = self.client.get_channel(value)
                if type(ch) is not discord.CategoryChannel:
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking for! (Need <class 'discord.CategoryChannel'>, got {type(ch)})", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {"vcCategory": ch.id}}, upsert=True)
        elif mode == "no-mic":
            if value is not None:
                value = await to_int(value, "You have to give a numerical ID for the channel you want to use!")
                if value is None:
                    return
                ch = self.client.get_channel(value)
                if type(ch) is not discord.TextChannel:
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking for! (Need <class 'discord.TextChannel'>, got {type(ch)})", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {"vcNoMic": ch.id}}, upsert=True)
        elif mode == "star channel":
            if value is not None:
                value = await to_int(value, "You have to give a numerical ID for the channel you want to use!")
                if value is None:
                    return
                ch = self.client.get_channel(value)
                if type(ch) is not discord.TextChannel:
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking for! (Need <class 'discord.TextChannel'>, got {type(ch)})", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {"starboardChannel": ch.id}}, upsert=True)
        elif mode == "star minimum":
            if value is not None:
                value = await to_int(value, "You need to give an integer value for your new minimum amount!")
                if value is None:
                    return
                if value < 1:
                    await itx.response.send_message("Your new value has to be at least 1!", ephemeral=True)
                collection.update_one(query, {"$set": {"starboardCountMinimum": value}}, upsert=True)

        await itx.response.send_message(f"Edited value of '{mode}' successfully.",ephemeral=True)

    vctable = app_commands.Group(name='vctable', description='Make your voice channels advanced!')
    # Owner   = Speaking perms
    # Muted   = No speaking perms
    # Speaker = Connection perms

    async def get_current_channel(self, itx: discord.Interaction, action: str, from_event: bool = None):
        collection = RinaDB["guildInfo"]
        query = {"guild_id": itx.guild_id}
        guild = collection.find_one(query)
        if guild is None:
            if from_event:
                return
            cmd_mention = self.client.getCommandMention("editguildinfo")
            await itx.response.send_message(f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention}!", ephemeral=True)
            return

        vcHub = guild["vcHub"]
        vcCategory = guild["vcCategory"]
        try:
            channel = itx.user.voice.channel
        except AttributeError:
            if from_event:
                return
            await itx.response.send_message(f"Couldn't {action}: You aren't connected to a voice channel!", ephemeral=True)
            return

        if channel.category.id not in [vcCategory] or \
                channel.id == vcHub or \
                channel.id in self.blacklisted_channels or \
                channel.name.startswith("〙"):
            if from_event:
                return
            await itx.response.send_message(f"Couldn't {action}: This voice channel is not compatible with VcTables!", ephemeral=True)
            return
        return channel

    async def get_channel_if_owner(self, itx: discord.Interaction | discord.Member, action: str, from_event: bool = False):
        channel = await self.get_current_channel(itx, action, from_event)
        if channel is None:
            return
        try:  # Check if executor is the VcTable owner
            if not channel.overwrites[itx.user].speak:
                raise KeyError("Not owner.")
        except KeyError:
            if from_event:
                return
            cmd_mention = self.client.getCommandMention('vctable create')
            await itx.response.send_message(f"Invalid permissions: You are not an owner of this VcTable! (Perhaps this isn't a VcTable yet: use {cmd_mention} to make it one!)", ephemeral=True)
            return
        return channel

    @vctable.command(name="create", description="Turn your custom vc into a cool vc")
    @app_commands.describe(owners="A list of extra owners for your VcTable. Separate with comma")
    async def create_vctable(self, itx: discord.Interaction, owners: str = ""):
        warning = ""
        owners = owners.split(",")
        cmd_mention = self.client.getCommandMention("vctable add_owner")
        added_owners = []
        for mention in owners:
            if mention == "":
                continue
            mention: str = mention.strip()
            if not (mention[0:2] == "<@" and mention[-1] == ">"):
                warning = f"Note: You didn't give a good list of VcTable owners, so I only added you. To make more people owner, use {cmd_mention}."
                added_owners = [itx.user.id]
                break
            for char in mention[2:-1]:
                if char not in "0123456789":
                    warning = f"Note: You didn't give a good list of VcTable owners, so I only added you. To make more people owner, use {cmd_mention}."
                    added_owners = [itx.user.id]
                    break
            added_owners.append(mention)
        else:
            added_owners = [itx.user.id] + [int(mention.strip()[2:-1]) for mention in added_owners]
        channel = await self.get_current_channel(itx, "create VcTable")
        if channel is None:
            return
        if itx.user.voice.channel.id in recently_renamed_vcs:
            # if the channel has been renamed 2 times in the past 10 minutes already
            if len(recently_renamed_vcs[channel.id]) >= 2:
                if recently_renamed_vcs[channel.id][0]+600 > mktime(datetime.now().timetuple()):
                    await itx.response.send_message(f"This channel has been renamed too often in the past 10 minutes! (bcuz discord :P)\n" +
                                                    f"You can turn this into a VcTable in <t:{recently_renamed_vcs[channel.id][0] + 600}:R> (<t:{recently_renamed_vcs[channel.id][0] + 600}:t>).", ephemeral=True)
                    # ignore entirely, don't continue command
                    return
                else:
                    recently_renamed_vcs[channel.id] = []
            else:
                recently_renamed_vcs[channel.id] = []
        else:
            recently_renamed_vcs[channel.id] = []

        await itx.response.defer(ephemeral=True)
        owner_present = False
        for target in channel.overwrites:
            if channel.overwrites[target].speak and target not in channel.category.overwrites:
                owner_present = True
        if owner_present:
            cmd_mention = self.client.getCommandMention("vctable owner")
            await itx.followup.send(f"This channel is already a VcTable! Use {cmd_mention}` mode:Check owners` to see who the owners of this table are!", ephemeral=True)
            return
        for owner_id in added_owners:
            owner = itx.guild.get_member(int(owner_id))
            await channel.set_permissions(owner, speak=True, reason="VcTable created: set as owner")
        owner_taglist = ', '.join([f'<@{id}>' for id in added_owners])
        await channel.send("CustomVC converted to VcTable\n"
                           f"Made {owner_taglist} a VcTable Owner",allowed_mentions=discord.AllowedMentions.none())
        await logMsg(itx.guild, f"{itx.user.mention} ({itx.user.id}) turned a CustomVC ({channel.id}) into a VcTable")
        recently_renamed_vcs[channel.id].append(int(mktime(datetime.now().timetuple())))
        await channel.edit(name=VcTable_prefix+channel.name)
        await itx.followup.send("Successfully converted channel to VcTable and set you as owner.\n"+warning,ephemeral=True)

    @vctable.command(name="owner", description="Manage the owners of your VcTable")
    @app_commands.describe(user="Who to add/remove as a VcTable owner (ignore if 'Check')")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Add owner', value=1),
        discord.app_commands.Choice(name='Remove owner', value=2),
        discord.app_commands.Choice(name='Check owners', value=3)
    ])
    async def edit_vctable_owners(self, itx: discord.Interaction, mode: int, user: discord.Member):
        if itx.user == user and mode != 3:
            if mode == 1:
                await itx.response.send_message("You can't set yourself as owner!", ephemeral=True)
            elif mode == 2:
                cmd_mention = self.client.getCommandMention("vctable owner")
                await itx.response.send_message("You can't remove your ownership of this VcTable!\n"
                                                f"You can make more people owner with {cmd_mention}` user:<user>` though...",
                                                ephemeral=True)
            return

        if mode == 1:  # add
            warning = ""
            channel = await self.get_channel_if_owner(itx, "add owner")
            if channel is None:
                return
            try:
                if channel.overwrites[user].speak:
                    await itx.response.send_message(f"This user is already an owner!", ephemeral=True)
                    return
            except KeyError:
                pass
            try:
                if channel.overwrites[user].speak is False:
                    warning = "\nThis user was muted. Making this person an owner caused their speaking permissions to be allowed!"
            except KeyError:
                pass
            await channel.set_permissions(user, speak=True, reason="VcTable edited: set as owner")
            await channel.send(f"{itx.user.mention} added {user.mention} as VcTable owner", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully added {user.mention} as owner." + warning, ephemeral=True)

        if mode == 2:  # remove
            channel = await self.get_channel_if_owner(itx, "remove owner")
            if channel is None:
                return
            try:
                if channel.overwrites[user].speak is not True: # if False or None
                    await itx.response.send_message("This user wasn't an owner yet.. Try taking someone else's ownership away.", ephemeral=True)
                    return
            except KeyError:
                pass
            await channel.set_permissions(user, speak=None, reason="VcTable edited: removed as owner")
            await channel.send(f"{itx.user.mention} removed {user.mention} as VcTable owner", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully removed {user.mention} as owner.", ephemeral=True)

        if mode == 3:  # check
            channel = await self.get_current_channel(itx, "check owners")
            if channel is None:
                return
            owners = []
            for target in channel.overwrites:  # key in dictionary
                if channel.overwrites[target].speak:
                    if isinstance(target, discord.Member):
                        owners.append(target.mention)
            await itx.response.send_message("Here is a list of this VcTable's owners:\n  "+', '.join(owners), ephemeral=True)

    @vctable.command(name="speaker", description="Allow users to talk (when authorized_speakers_only is on)")
    @app_commands.describe(user="Who to add/remove as a VcTable speaker (ignore if 'Check')")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Add speaker', value=1),
        discord.app_commands.Choice(name='Remove speaker', value=2),
        discord.app_commands.Choice(name='Check speakers', value=3)
    ])
    async def edit_vctable_speakers(self, itx: discord.Interaction, mode: int, user: discord.Member):
        if itx.user == user and mode != 3:
            await itx.response.send_message("You can't edit your own speaking permissions!", ephemeral=True)
            return

        if mode == 1:  # add
            channel = await self.get_channel_if_owner(itx, "add speaker")
            if channel is None:
                return
            warning = ""
            try:
                if channel.overwrites[user].connect:
                    await itx.response.send_message(f"This user is already a speaker!", ephemeral=True)
                    return
            except KeyError:
                pass
            try:
                if channel.overwrites[itx.guild.default_role].speak is False: # No IDE, this expression can't be simplified.
                    cmd_mention = self.client.getCommandMention("vctable make_authorized_only")
                    warning = f"\nThis has no purpose until you enable 'authorized-only' using {cmd_mention}"
            except KeyError:
                pass
            await channel.set_permissions(user, connect=True, reason="VcTable edited: set as speaker")
            await channel.send(f"{itx.user.mention} made {user.mention} a speaker", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully made {user.mention} a speaker."+warning, ephemeral=True)

        if mode == 2:  # remove
            channel = await self.get_channel_if_owner(itx, "remove speaker")
            if channel is None:
                return
            try:
                if not channel.overwrites[user].connect:
                    await itx.response.send_message(f"This user is not a speaker! You can't unspeech a non-speaker!", ephemeral=True)
                    return
            except KeyError:
                await itx.response.send_message(f"This user is not a speaker! You can't unspeech a non-speaker!", ephemeral=True)
                return
            warning = ""
            try:
                if channel.overwrites[itx.guild.default_role].speak is False:  # No IDE, this expression can't be simplified.
                    cmd_mention = self.client.getCommandMention("vctable make_authorized_only")
                    warning = f"\nThis has no purpose until you enable 'authorized-only' using {cmd_mention}"
            except KeyError:
                pass
            await channel.set_permissions(user, connect=None, reason="VcTable edited: removed as speaker")
            await channel.send(f"{itx.user.mention} removed {user.mention} as speaker", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully made {user.mention} a speaker."+warning, ephemeral=True)

        if mode == 3:  # check
            channel = await self.get_current_channel(itx, "check speakers")
            if channel is None:
                return
            speakers = []
            for target in channel.overwrites:  # key in dictionary
                if channel.overwrites[target].connect:
                    if isinstance(target, discord.Member):
                        speakers.append(target.mention)
            await itx.response.send_message("Here is a list of this VcTable's speakers:\n  " + ', '.join(speakers), ephemeral=True)

    @vctable.command(name="mute", description="Deny users to talk in your VcTable")
    @app_commands.describe(user="Who to mute/unmute (ignore if 'Check')")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Mute participant', value=1),
        discord.app_commands.Choice(name='Unmute participant', value=2),
        discord.app_commands.Choice(name='Check muted participants', value=3)
    ])
    async def edit_vctable_muted_participants(self, itx: discord.Interaction, mode: int, user: discord.Member):
        if itx.user == user and mode != 3:
            await itx.response.send_message("You can't " + "un"*(mode == 2) + "mute yourself!", ephemeral=True)
            return

        if mode == 1:  # mute
            channel = await self.get_channel_if_owner(itx, "mute participant")
            if channel is None:
                return
            try:
                if channel.overwrites[user].speak is False:
                    await itx.response.send_message(f"This user is already muted!", ephemeral=True)
                    return
            except KeyError:
                pass
            try:
                if channel.overwrites[user].speak:
                    await itx.response.send_message(f"This user is an owner! You can't mute a VcTable owner!", ephemeral=True)
                    return
            except KeyError:
                pass
            try:
                warning = "\nThis user was a speaker before. Muting them overwrote this permissions and removed their speaker permissions" if channel.overwrites[user].speak else ""
            except KeyError:
                warning = ""

            class Interaction:
                def __init__(self,guild, user):
                    self.user = user
                    self.guild = guild
            if isStaff(Interaction(itx.guild, user)):
                await itx.response.send_message("You can't mute staff members! If you have an issue with staff, make a ticket or DM an admin!",ephemeral=True)
                return
            await channel.set_permissions(user, speak=False, reason="VcTable edited: muted participant")
            await channel.send(f"{itx.user.mention} muted {user.mention}", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully muted {user.mention}."+warning, ephemeral=True)
            if user in channel.members:
                await user.move_to(channel)

        if mode == 2:  # remove
            channel = await self.get_channel_if_owner(itx, "unmute participant")
            if channel is None:
                return
            try:
                if channel.overwrites[user].speak is not False: # if True or None
                    await itx.response.send_message(f"This user is already unmuted! Let people be silent if they wanna be >:(", ephemeral=True)
                    return
            except KeyError:
                await itx.response.send_message(f"This user is already unmuted! Let people be silent if they wanna be >:(", ephemeral=True)
                return
            try:
                if channel.overwrites[user].speak:
                    await itx.response.send_message("This user is an owner. Unmuting this person would reset their speaking permissions! (Cancelled!)", ephemeral=True)
                    return
            except KeyError:
                pass
            await channel.set_permissions(user, speak=None, reason="VcTable edited: unmuted participant")
            await channel.send(f"{itx.user.mention} unmuted {user.mention}", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully unmuted {user.mention}.", ephemeral=True)
            if user in channel.members:
                await user.move_to(channel)

        if mode == 3:  # check
            channel = await self.get_current_channel(itx, "check muted participants")
            if channel is None:
                return
            muted = []
            for target in channel.overwrites:  # key in dictionary
                if channel.overwrites[target].speak is False: # if they have no speaking perms = muted
                    # NOTE: expression CAN'T be simplified: it can return None and "not None" returns True as well.
                    # we only want it to execute this code if speaking perms = False. And not if it is None/unset (rip IDE)
                    if isinstance(target, discord.Member):
                        muted.append(target.mention)
            await itx.response.send_message("Here is a list of this VcTable's muted participants:\n  " + ', '.join(muted), ephemeral=True)

    @vctable.command(name="make_authorized_only", description="Only let users speak if they are whitelisted by the owner")
    async def vctable_authorized_only(self, itx: discord.Interaction):
        channel = await self.get_channel_if_owner(itx, "enable authorized-only")
        if channel is None:
            return

        # if authorized-only is enabled -> (the role overwrite is not nonexistant and is False):
        if channel.overwrites.get(itx.guild.default_role, False):
            if channel.overwrites[itx.guild.default_role].speak is False:
                await channel.set_permissions(itx.guild.default_role, speak=None, reason="VcTable edited: disaled authorized-only for speaking")
                await channel.send(f"{itx.user.mention} disabled whitelist for speaking", allowed_mentions=discord.AllowedMentions.none())
                await itx.response.send_message(f"Successfully disabled whitelist.", ephemeral=True)
                return

        class Confirm(discord.ui.View):
            def __init__(self, timeout=None):
                super().__init__()
                self.value = None
                self.timeout = timeout

            # When the confirm button is pressed, set the inner value to `True` and
            # stop the View from listening to more input.
            # We also send the user an ephemeral message that we're confirming their choice.
            @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
            async def confirm(self, _itx: discord.Interaction, _button: discord.ui.Button):
                self.value = 1
                self.stop()

            @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
            async def cancel(self, _itx: discord.Interaction, _button: discord.ui.Button):
                self.value = 0
                self.stop()

        # if authorized-only is disabled:
        view = Confirm()
        cmd_mention = self.client.getCommandMention("vctable speaker")
        await itx.response.send_message(f"Enabling authorized-only (a whitelist) will make only owners and speakers (people that have been whitelisted) able to talk\n"
                                        f"Please make sure everyone is aware of this change."
                                        f"To whitelist someone, use {cmd_mention}`mode:Add user:<user>`, (and they might have to rejoin to update their permissions)",
                                        ephemeral=True,
                                        view=view)
        await view.wait()
        if view.value == 1:
            await channel.set_permissions(itx.guild.default_role, speak=False, reason="VcTable edited: enabled authorized-only for speaking")
            await channel.send(f"{itx.user.mention} enabled whitelist for speaking", allowed_mentions=discord.AllowedMentions.none())
            for member in channel.members: # member has no owner or speaking perms, move to same vc?
                if member in channel.overwrites:
                    if channel.overwrites[member].speak or channel.overwrites[member].connect:
                        continue
                await member.move_to(channel)
            cmd_mention = self.client.getCommandMention("vctable speaker")
            await itx.edit_original_response(content= f"Successfully enabled whitelist. Use {cmd_mention}` user:<user>` to let more people speak.",
                                             view   = None)
        else:
            await itx.edit_original_response(content="Cancelling...", view=None)



    @vctable.command(name="about", description="Get information about this CustomVC add-on feature")
    async def vctable_help(self, itx: discord.Interaction):
        embed1 = discord.Embed(
            color       = discord.Colour.from_rgb(r=255, g=153, b=204),
            title       = 'Custom VC Tables',
            description = "Tables are a system to help keep a focused voice channel on-topic. For example, a watch "
                          "party or a group gaming session might welcome people joining to participate but not "
                          "want people to derail/disrupt it. VcTables allow you to have a bit more control "
                          "over your vc by letting you mute disruptive people or make speaking permissions whitelist-only")
        embed2 = discord.Embed(
            color       = discord.Colour.from_rgb(r=255, g=153, b=204),
            title       = 'Command documentation and explanation',
            description = f"Words in brackets [like so] mean they are optional for the command.\n"
                          f"Most commands are for owners only, like muting, adding/removing permissions. Normal participants can check who's owner, speaker, or muted though.\n"
                          f"{self.client.getCommandMention('vctable about')}: See this help page\n"
                          f"{self.client.getCommandMention('vctable create')}` [owners:]`: Turns your CustomVC into a VcTable and makes you (and any additional mentioned user(s)) the owner\n"
                          f"{self.client.getCommandMention('vctable owner')}` mode:  user:`: Add/Remove an owner to your table. If you want to check the owners, then it doesn't matter what you fill in for 'user'\n"
                          f"{self.client.getCommandMention('vctable mute')}` mode:  user:`: Mute/Unmute a user in your table. If you want to check the muted participants, see ^ (same as for checking owners)\n"
                          f"{self.client.getCommandMention('vctable make_authorized_only')}: Toggle the whitelist for speaking (requires rejoining to update permissions)\n"
                          f"{self.client.getCommandMention('vctable speaker')}` mode:  user:`: Add/Remove a speaker to your table. This user gets whitelisted to speak when authorized-only is enabled. Checking speakers works the same as checking owners and muted participants\n")
        await itx.response.send_message(embeds=[embed1,embed2], ephemeral=True)

async def setup(client):
    await client.add_cog(CustomVcs(client))

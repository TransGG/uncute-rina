import discord, discord.ext.commands as commands, discord.app_commands as app_commands
from resources.utils.utils import log_to_guild # to log custom vc changes
from resources.utils.permissions import is_verified, is_staff, is_admin # to check permissions for staff commands
from resources.customs.bot import Bot
from resources.modals.customvcs import CustomVcStaffEditorModal, clear_vc_rename_log, try_store_vc_rename
from resources.views.generics import GenericTwoButtonView


def voice_channel_is_custom(
        voice_channel: discord.VoiceChannel, 
        customvc_category_id: int, 
        customvc_hub_id: int, 
        customvc_channel_blacklist: list[int]
) -> bool:
    """Check if a voice channel is custom-made by Rina through the customvc Hub.

    Parameters
    -----------
    voice_channel: :class:`discord.VoiceChannel`:
        The voice channel to test for customness
    customvc_category_id: :class:`int`
        The category id where custom voice channels are allowed to be created.
    customvc_hub_id: :class:`int`
        The voice channel id of the channel members should join to create a custom voice channel.
    customvc_channel_blacklist: :class:`int`
        A list of voice channel ids that may definitely not be removed when the last person leaves.

    Returns
    --------
    :class:`bool`:
        Whether the channel is a custom voice channel or not.
    """
    return (
        voice_channel.category.id in [customvc_category_id] and
        voice_channel.id != customvc_hub_id and # avoid deleting the hub channel
        voice_channel.id not in customvc_channel_blacklist and
        not voice_channel.name.startswith('〙') # new blacklisted channels: "#General" "#Quiet", "#Private" and "#Minecraft"
    )

async def reset_voice_channel_permissions_if_vctable(vctable_prefix: str, voice_channel: discord.VoiceChannel):
    """
    Reset a voice channel's permission overrides if the 'owners' of the voice channel 
    table are no longer present/connected to the channel.

    Parameters
    -----------
    vctable_prefix: :class:`str`
        The prefix of voice channel tables, to remove/rename it if the vctable owners left.

    Regards
    --------
    This function does not check if the channel is actually a custom voice channel.
    """
    if len(voice_channel.overwrites) > len(voice_channel.category.overwrites):  # if VcTable, reset ownership; and all owners leave: reset all perms
        reset_vctable = True #check if no owners left --> all members in the voice channel aren't owner
        for target in voice_channel.overwrites:
            if target not in voice_channel.members:
                continue
            if voice_channel.overwrites[target].connect:
                reset_vctable = False
                break
        if not reset_vctable:
            return
        
        try:
            await voice_channel.edit(overwrites=voice_channel.category.overwrites) #reset overrides; error caught in try-except
            #update every user's permissions
            for user in voice_channel.members:
                await user.move_to(voice_channel)
            await voice_channel.send("This channel was converted from a VcTable back to a normal CustomVC because all the owners left")
            # remove channel's name prefix (seperately from the overwrites due to things like ratelimiting)
            if voice_channel.name.startswith(vctable_prefix):
                new_channel_name = voice_channel.name[len(vctable_prefix):]
                try_store_vc_rename(voice_channel.id, max_rename_limit=3)
                # same as `/vctable disband`
                # allow max 3 renamed: if a staff queued a rename due to rules, it'd be queued at 3.
                # it would be bad to have it be renamed back to the bad name right after.
                await voice_channel.edit(name=new_channel_name) # error caught in try-except
        except discord.errors.NotFound: # catch two possible voice_channel.edit() exceptions
            pass # event triggers after vc could be deleted already

async def handle_delete_custom_vc(client: Bot, member: discord.Member, voice_channel: discord.VoiceChannel):
    """
    Handle the deletion of a custom voice channel (and error handling)

    Parameters
    -----------
    client: :class:`Bot`
        The bot instance to log to guild with.
    member: :class:`discord.Member`
        The member to log as last in vc.
    voice_channel: :class:`discord.VoiceChannel`
        The voice channel to remove.
    """
    # cmdChannel = discord.utils.find(lambda r: r.name == 'no-mic', before.channel.category.text_channels)
    # await cmdChannel.send(f"{member.nick or member.name} left voice channel \"{before.channel.name}\", and was the last one in it, so it was deleted. ({member.id})",delete_after=32, allowed_mentions = discord.AllowedMentions.none())
    clear_vc_rename_log(voice_channel.id)
    try:
        await voice_channel.delete()
    except discord.errors.NotFound:
        await log_to_guild(client, member.guild, 
                           f":warning: **WARNING!! Couldn't delete CustomVC channel** {member.nick or member.name} ({member.id}) left voice "
                           f"channel \"{voice_channel.name}\" ({voice_channel.id}), and was the last one in it, but it **could not be deleted**!")
        raise
    await log_to_guild(client, member.guild, f"{member.nick or member.name} ({member.id}) left voice channel \"{voice_channel.name}\" ({voice_channel.id}), and was the last one in it, so it was deleted.")

async def handle_custom_voice_channel_leave_events(client: Bot, member: discord.Member, voice_channel: discord.VoiceChannel):
    """
    A helper function to handle the custom voice channel events when a user leaves a channel.
    This includes: channel deletion, vctable disbanding.

    Parameters
    -----------
    client: :class:`Bot):`
        The client to send logs with, and for the vctable prefix.
    member: :class:`discord.Member`
        The member to trigger the leave event.
    voice_channel: :class:`discord.VoiceChannel`
        The voice channel that the member left from.
    """
    # The following events should only apply to custom voice channels:

    if len(voice_channel.members) == 0:
        await handle_delete_custom_vc(client, member, voice_channel)

    await reset_voice_channel_permissions_if_vctable(client.custom_ids["vctable_prefix"], voice_channel)

async def create_new_custom_vc(client: Bot, member: discord.Member, voice_channel: discord.VoiceChannel, customvc_category_id: int, customvc_hub_id: int):
    """
    A helper function to create a new custom voice channel

    Args:
        client (Bot): The Bot class to use for logging.
        member (discord.Member): The member that triggered the event/function.
        voice_channel (discord.VoiceChannel): The voice channel the user joined to trigger this function (the customvc hub)
        customvc_category_id (int): The category id to create the custom voice channel in.
        customvc_hub_id (int): The custom voice channel hub channel id.
    """
    
    default_name = "Untitled voice chat"
    warning = ""
    vcCategory_for_vc = voice_channel.category
    vcCategory_for_vc.id = customvc_category_id
    cmd_mention = client.get_command_mention("editvc")

    try:
        vc = await vcCategory_for_vc.create_voice_channel(default_name,position=voice_channel.position+1)
    except discord.errors.HTTPException:
        await log_to_guild(client, member.guild, f"WARNING: COULDN'T CREATE CUSTOM VOICE CHANNEL: TOO MANY (max 50?)")
        raise

    try:
        await member.move_to(vc,reason=f"Opened a new voice channel through the vc hub thing.") 
        await vc.send(f"Voice channel <#{vc.id}> ({vc.id}) created by <@{member.id}> ({member.id}). Use {cmd_mention} to edit the name/user limit.", allowed_mentions=discord.AllowedMentions.none())
        for custom_vc in vcCategory_for_vc.voice_channels:
            if custom_vc.id == customvc_hub_id or custom_vc.id == vc.id:
                continue
            await custom_vc.edit(position=custom_vc.position+1)
    except Exception as ex:
        warning = str(ex)+": User clicked the vcHub too fast, and it couldn't move them to their new channel\n"
        try:
            await member.move_to(None, reason=f"Couldn't create a new Custom voice channel so kicked them from their current vc to prevent them staying in the main customvc hub")
            # no need to delete vc if they are kicked out of the channel, cause then the next event will notice that they left the channel.
        except:
            await vc.delete()
        await client.log_channel.send(content=warning, allowed_mentions=discord.AllowedMentions.none())
        raise
    # nomicChannel = member.guild.get_channel(vcNoMic)
    await log_to_guild(client, member.guild, warning+f"{member.nick or member.name} ({member.id}) created and joined voice channel {vc.id} (with the default name).")


class CustomVcs(commands.Cog):
    def __init__(self, client: Bot):
        global RinaDB
        self.client = client
        RinaDB = client.RinaDB
        self.blacklisted_channels = [959626329689583616, 960984256425893958, 960984642717102122, 961794293704581130]
        #  #General, #Private, #Quiet, and #Minecraft. Later, it also excludes channels starting with "〙"

    @commands.Cog.listener()
    async def on_voice_state_update(self, member:discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.guild.id == self.client.custom_ids["staff_server_id"]:
            return
        customvc_hub_id, customvc_category_id = await self.client.get_guild_info(member.guild, "vcHub", "vcCategory")
        if before.channel is not None and before.channel in before.channel.guild.voice_channels:
            if voice_channel_is_custom(before.channel, customvc_category_id, customvc_hub_id, self.blacklisted_channels):
                # only run if this voice state regards a custom voice channel
                await handle_custom_voice_channel_leave_events(self.client, member, before.channel)
        
        if after.channel is not None:
            if after.channel.id == customvc_hub_id:
                await create_new_custom_vc(self.client, member, after.channel, customvc_category_id, customvc_hub_id)

    @app_commands.command(name="editvc",description="Edit your voice channel name or user limit")
    @app_commands.describe(name="Give your voice channel a name!",
                           limit="Give your voice channel a user limit!")
    async def editVc(self, itx: discord.Interaction, 
                     name: app_commands.Range[str, 3, 35] | None = None, 
                     limit: app_commands.Range[int, 0, 99] | None = None):
        if not is_verified(itx.guild, itx.user):
            await itx.response.send_message("You can't edit voice channels because you aren't verified yet!",ephemeral=True)
            return
        
        
        cmd_mention = self.client.get_command_mention("editguildinfo")
        log = [itx, f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention} `mode:21`, `mode:22` or `mode:23`!"]
        vcHub, vcLog, vcCategory = await self.client.get_guild_info(itx.guild, "vcHub", "vcLog", "vcCategory", log=log)
        warning = ""

        if itx.user.voice is None:
            if is_staff(itx.guild, itx.user):
                await itx.response.send_modal(CustomVcStaffEditorModal(vcHub, vcLog, vcCategory))
                return
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
            if name.startswith("〙"):
                await itx.response.send_message("Due to the current layout, you can't change your channel to something starting with '〙'. Sorry for the inconvenience", ephemeral=True)
                return
            if name == "Untitled voice chat":
                warning += "Are you really going to change it to that..\n"
            if len(itx.user.voice.channel.overwrites) > len(itx.user.voice.channel.category.overwrites): # if VcTable, add prefix
                name = self.client.custom_ids["vctable_prefix"] + name

        if name is not None:
            # don't add cooldown if you only change the limit, not the name
            first_rename_time = try_store_vc_rename(channel.id)
            if first_rename_time:
                await itx.response.send_message(f"You can't edit your channel more than twice in 10 minutes! (bcuz discord :P)\n" +
                                                f"You can rename it again <t:{first_rename_time + 600}:R> (<t:{first_rename_time + 600}:t>).", ephemeral=True)
                return
        
        limitInfo = ""
        oldName = channel.name
        oldLimit = channel.user_limit
        try:
            if not limit and not name:
                await itx.response.send_message("You can edit your channel with this command. Set a value for the name or the maximum user limit.", ephemeral=True)
            if not limit and name:
                await channel.edit(reason=f"Voice channel renamed from \"{channel.name}\" to \"{name}\"{limitInfo}", name=name)
                await log_to_guild(self.client, itx.guild, f"Voice channel ({channel.id}) renamed from \"{oldName}\" to \"{name}\" (by {itx.user.nick or itx.user.name}, {itx.user.id})")
                await itx.response.send_message(warning+f"Voice channel successfully renamed to \"{name}\"", ephemeral=True)#allowed_mentions=discord.AllowedMentions.none())
            if limit and not name:
                await channel.edit(reason=f"Voice channel limit edited from \"{oldLimit}\" to \"{limit}\"", user_limit=limit)
                await log_to_guild(self.client, itx.guild, f"Voice channel \"{oldName}\" ({channel.id}) edited the user limit from  \"{oldLimit}\" to \"{limit}\" (by {itx.user.nick or itx.user.name}, {itx.user.id}){limitInfo}")
                await itx.response.send_message(warning+f"Voice channel user limit for \"{oldName}\" successfully edited from \"{oldLimit}\" to \"{limit}\"", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
            if limit and name:
                await channel.edit(reason=f"Voice channel edited from name: \"{channel.name}\" to \"{name}\" and user limit from: \"{limit}\" to \"{oldLimit}\"", user_limit=limit,name=name)
                await log_to_guild(self.client, itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) changed VC ({channel.id}) name \"{oldName}\" to \"{name}\" and user limit from \"{oldLimit}\" to \"{limit}\"{limitInfo}")
                await itx.response.send_message(warning+f"Voice channel name and user limit successfully edited.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        except discord.errors.HTTPException as ex:
            ex_message = repr(ex).split("(", 1)[1][1:-2]
            await log_to_guild(self.client, itx.guild, f"Warning! >> "+ex_message+f" << {itx.user.nick or itx.user.name} ({itx.user.id}) tried to change {oldName} ({channel.id}) to {name}, but wasn't allowed to by discord, probably because it's in a banned word list for discord's discovery <@262913789375021056>")

    async def edit_guild_info_autocomplete(self, itx: discord.Interaction, current: str):
        if not is_admin(itx.guild, itx.user):
            return [app_commands.Choice(name="Only admins can use this command!", value="No permission")]

        if current.startswith("1") or current.startswith("2") or current.startswith("3") or current.startswith("4") or current.startswith("5"):
            options = [
                ["Help: Main server settings",           "01"],
                ["Help: Custom Voice Channels",          "02"],
                ["Help: Starboard settings",             "03"],
                ["Help: Bumping-related settings",       "04"],
                ["Help: Additional settings",            "05"],

                ["Logging channel",                      "11"],
                ["Poll reactions blacklist",             "12"],

                ["CustomVC Hub",                         "21"],
                ["CustomVC creation Category",           "22"],
                ["CustomVC No-mic channel",              "23"],

                ["Starboard emoji",                      "31"],
                ["Starboard channel",                    "32"],
                ["Minimum required stars for starboard", "33"],
                ["Starboard blacklisted channels",       "34"],
                ["Starboard downvote initiation value",  "35"],

                ["ID of the bump bot / DISBOARD bot",    "41"],
                ["Channel that DISBOARD bumps in",       "42"],
                ["Role to ping when sending reminder",   "43"],

                ["Vc Activity Logs channel",             "51"],
            ]
            return [
                app_commands.Choice(name=option[0], value=option[1])
                for option in options if option[1].startswith(current)
            ][:15]
        else:
            options = [
                ["Main server settings",     "01"],
                ["Custom Voice Channels",    "02"],
                ["Starboard settings",       "03"],
                ["Bumping-related settings", "04"],
            ]
            return [
                app_commands.Choice(name=option[0], value=option[1])
                for option in options if current.lower() in option[0]
            ][:15]

    @app_commands.command(name="editguildinfo",description="Edit guild settings (staff only)")
    @app_commands.describe(mode="Do you want to edit, or just see the values of the guild settings?",
                           option="What value do you want to edit?",
                           value="Edit what value? (ignore this if viewing a value)")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='View guild settings', value=1),
        discord.app_commands.Choice(name='Edit guild settings', value=2),
    ])
    @app_commands.autocomplete(option=edit_guild_info_autocomplete)
    async def edit_guild_info(self, itx: discord.Interaction, mode: int, option: str, value: str):
        if not is_admin(itx.guild, itx.user):
            await itx.response.send_message("You don't have sufficient permissions to execute this command! (don't want you to break the bot ofc.)",ephemeral=True)
            return
        
        options = {
            "01" : "Help: Main server settings",
            "02" : "Help: Custom Voice Channels",
            "03" : "Help: Starboard settings",
            "04" : "Help: Bumping-related settings",
            "05" : "Help: Additional settings",

            "11" : "vcLog",
            "12" : "pollReactionsBlacklist",

            "21" : "vcHub",
            "22" : "vcCategory",
            "23" : "vcNoMic",

            "31" : "starboardEmoji",
            "32" : "starboardChannel",
            "33" : "starboardCountMinimum",
            "34" : "starboardBlacklistedChannels",
            "35" : "starboardDownvoteInitValue",

            "41" : "bumpBot",
            "42" : "bumpChannel",
            "43" : "bumpRole",

            "51" : "vcActivityLogChannel"
        }

        if option not in options:
            await itx.response.send_message("Your mode has to be a number. Type one of the autocomplete suggestions to " +
                                            "figure out which number/ID you need.", ephemeral=True)
            return
        if option.startswith("0"):
            if option == "01":
                await itx.response.send_message("Main server settings:\n" +
                                                "`11`: Log (What channel does Rina log to?). This includes the following:\n" +
                                                "        Starting Rina\n"+
                                                "        Custom voice channel creations/deletions, renames and user-limiting on these, and /vctable,\n" +
                                                "        Starboard creations, deletions (both manual ('delete message') and automatic ('score:-1'))\n" +
                                                "        Staff actions (dictionary commands, /say, public anonymous /tag commands, /delete_week_selfies, \n" +
                                                "        Warnings (starboard ':x:' used on a deleted message, adding a reaction to someone that blocked rina)\n" +
                                                "        Errors (crashes in a command, missing guild_info data, etc.)\n" +
                                                "`12`: Poll reactions blacklist (Which channels can /add_poll_reactions not be used in?)", ephemeral=True)
            elif option == "02":
                await itx.response.send_message("Custom Voice Channels:\n" +
                                                "`21`: VC Hub (Which channel should people join to create a new Custom voice channel (CustomVC)?)\n" +
                                                "`22`: VC category (Which category are Custom voice channels created in?)\n" +
                                                "`23`: VC no-mic (Which channel should custom new)", ephemeral=True)
            elif option == "03":
                await itx.response.send_message("Starboard settings:\n" +
                                                "`31`: Starboard emoji (what emoji can people add to add something to the starboard?)\n"
                                                "`32`: Starboard channel (which channel are starboard messages sent in?)\n" +
                                                "`33`: Star minimum (how many stars does a message need before it's added to the starboard?)\n"
                                                "`34`: Starboard blacklist (what channels' messages can't be starboarded? (list))\n"
                                                "`35`: Starboard downvote initiation value (how many total (up/down)votes must a message have before a negative score can cause it to be deleted?)", ephemeral=True)
            elif option == "04":
                await itx.response.send_message("Bumping-related settings:\n" +
                                                "`41`: Bump bot: DISBOARD.org (Whose messages should I check for bump messages with embeds?)\n" +
                                                "`42`: Bump channel (Which channel should be checked for messages by the DISBOARD bot?)\n" +
                                                "`43`: Bump role (Which role should be pinged when 2 hours have passed?)", ephemeral=True)
            elif option == "05":
                await itx.response.send_message("Additional settings:\n" +
                                                "`51`: Voice channel activity channel (What channel logs people joining/leaving/moving VCs?) (assumes Logger#6088 bot)" +
                                                "", ephemeral=True)
            return

        if mode == 1:
            try:
                value = await self.client.get_guild_info(itx.guild, options[option])
            except KeyError:
                await itx.response.send_message("This server does not yet have a value for this option!", ephemeral=True)
                return
            await itx.response.send_message("Here is the value for " + options[option] + " in this guild (" + str(itx.guild.id) + "):\n\n" +
                                            str(value), ephemeral=True)
        if mode == 2:
            query = {"guild_id": itx.guild_id}
            collection = RinaDB["guildInfo"]
            
            async def to_int(value, error_msg):
                try:
                    return int(value)
                except ValueError:
                    await itx.response.send_message(error_msg, ephemeral=True)
                    return None

            if option == "11":
                value = await to_int(value, "You have to give a numerical ID for the channel you want to use!")
                if value is None:
                    return
                ch = itx.client.get_channel(value)
                if not isinstance(ch, discord.abc.Messageable):
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking for! (Needs to be a channel I can message in; got {type(ch)})", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: ch.id}}, upsert=True)
            elif option == "12":
                channel_ids = value.split(",")
                blacklist = []
                for channel_id in channel_ids:
                    channel = await to_int(channel_id.strip(), "You need to give a list of integers, separated by a comma, for this new blacklist!")
                    if channel is None:
                        return
                    blacklist.append(channel)
                collection.update_one(query, {"$set": {options[option]: blacklist}}, upsert=True)
            elif option == "21":
                value = await to_int(value, "You have to give a numerical ID for the channel you want to use!")
                if value is None:
                    return
                ch = itx.client.get_channel(value)
                if type(ch) is not discord.VoiceChannel:
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking for! (Need <class 'discord.VoiceChannel'>, got {type(ch)})", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: ch.id}}, upsert=True)
            elif option == "22":
                value = await to_int(value, "You have to give a numerical ID for the category you want to use!")
                if value is None:
                    return
                ch = itx.client.get_channel(value)
                if type(ch) is not discord.CategoryChannel:
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking for! (Need <class 'discord.CategoryChannel'>, got {type(ch)})", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: ch.id}}, upsert=True)
            elif option == "23":
                value = await to_int(value, "You have to give a numerical ID for the channel you want to use!")
                if value is None:
                    return
                ch = itx.client.get_channel(value)
                if type(ch) is not discord.TextChannel:
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking for! (Need <class 'discord.TextChannel'>, got {type(ch)})", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: ch.id}}, upsert=True)
            elif option == "31":
                value = await to_int(value, "You have to give a numerical ID for the emoji you want to use!")
                if value is None:
                    return
                emoji = itx.client.get_emoji(value)
                print(emoji)
                if type(emoji) is not discord.Emoji:
                    await itx.response.send_message(f"The ID you gave wasn't an emoji! (i think) (or not one I can use)", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: emoji.id}}, upsert=True)
            elif option == "32":
                value = await to_int(value, "You have to give a numerical ID for the channel you want to use!")
                if value is None:
                    return
                ch = itx.client.get_channel(value)
                if not isinstance(ch, discord.TextChannel):
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking for! (Need <class 'discord.TextChannel'>; got {type(ch)})", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: ch.id}}, upsert=True)
            elif option == "33":
                value = await to_int(value, "You need to give an integer value for your new minimum amount!")
                if value is None:
                    return
                if value < 1:
                    await itx.response.send_message("Your new value has to be at least 1!", ephemeral=True)
                collection.update_one(query, {"$set": {options[option]: value}}, upsert=True)
            elif option == "34":
                channel_ids = value.split(",")
                blacklist = []
                for channel_id in channel_ids:
                    channel = await to_int(channel_id.strip(), "You need to give a list of integers, separated by a comma, for this new blacklist!")
                    if channel is None:
                        return
                    blacklist.append(channel)
                collection.update_one(query, {"$set": {options[option]: blacklist}}, upsert=True)
            elif option == "35":
                value = await to_int(value, "You need to give an integer value for your new minimum amount!")
                if value is None:
                    return
                if value < 1:
                    await itx.response.send_message("Your new value has to be at least 1!", ephemeral=True)
                collection.update_one(query, {"$set": {options[option]: value}}, upsert=True)
            elif option == "41":
                value = await to_int(value, "You need to give a numerical ID for the bot id you want to use!")
                if value is None:
                    return
                user = itx.client.get_user(value)
                if not isinstance(user, discord.User):
                    await itx.response.send_message("The ID you gave wasn't for a valid user!", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: user.id}}, upsert=True)
            elif option == "42":
                value = await to_int(value, "You need to give a numerical ID for the channel you want to use!")
                if value is None:
                    return
                ch = itx.client.get_channel(value)
                if not isinstance(ch, discord.abc.Messageable):
                    await itx.response.send_message("The ID you gave wasn't for the type of channel I was looking for!", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: ch.id}}, upsert=True)
            elif option == "43":
                value = await to_int(value, "You need to give a numerical ID for the role you want to use!")
                if value is None:
                    return
                ch = itx.guild.get_role(value)
                if not isinstance(ch, discord.Role):
                    await itx.response.send_message("The ID you gave wasn't a role!", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: ch.id}}, upsert=True)
            elif option == "51":
                value = await to_int(value, "You need to give the numerical ID for the channel you want to use!")
                if value is None:
                    return
                ch = itx.client.get_channel(value)
                if not isinstance(ch, discord.abc.Messageable):
                    await itx.response.send_message("The ID you gave wasn't for the type of channel I was looking for!", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: ch.id}}, upsert=True)
            
            await itx.response.send_message(f"Edited value of '{options[option]}' successfully.",ephemeral=True)


    # region Custom VcTables
    vctable = app_commands.Group(name='vctable', description='Make your voice channels advanced!')
    # Owner       = Connection perms (and speaking perms)
    # Speaker     = Speaking perms
    # Muted       = No speaking perms (or stream(video) perms)
    # Participant = Channel view perms (and message history perms)

    async def get_current_channel(self, itx: discord.Interaction, action: str, from_event: bool = None):
        """Gets the voice channel of the command executer if it's a custom voice channel.

        Parameters
        -----------
        itx: :class:`discord.Interaction`
            The interaction from the original command.
        action: :class:`str`
            The action to note in the error message.
        from_event: :class:`bool`, optional
            Whether this event was executes from a non-command context. Default: None.

        Returns
        --------
        :class:`discord.VoiceChannel`
            The custom voice channel that the executer is in.
        :class:`None`
            If the user is not in a custom voice channel.
        """
        log = None
        if not from_event:
            cmd_mention = self.client.get_command_mention("editguildinfo")
            log = [itx, f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention} `mode:21` or `mode:22`!"]
        vcHub, vcCategory = await self.client.get_guild_info(itx.guild, "vcHub", "vcCategory", log=log)

        try:
            channel = itx.user.voice.channel
        except AttributeError:
            if from_event:
                return
            await itx.response.send_message(f"Couldn't {action}: You aren't connected to a voice channel!", ephemeral=True)
            return

        if not voice_channel_is_custom(channel, vcCategory, vcHub, self.blacklisted_channels):
            if from_event:
                return
            await itx.response.send_message(f"Couldn't {action}: This voice channel is not compatible with VcTables!", ephemeral=True)
            return
        
        return channel

    async def get_channel_if_owner(self, itx: discord.Interaction | discord.Member, action: str, from_event: bool = False):
        """
        Gets the voice channel of the command executer if they are in a custom voice channel that has 
        turned into a vctable AND they are the owner of that table.

        Parameters
        -----------
        itx: :class:`discord.Interaction` | :class:`discord.Member`
            The interaction from the original command.
        action: :class:`str`
            The action to note in the error message.
        from_event: :class:`bool`, optional
            Whether this event executes from a non-command context. Default: False.

        Returns
        --------
        :class:`discord.VoiceChannel`
            The vctable that the executer is in.
        :class:`None`
            If the user is not in a custom voice channel, or is not owner of the vctable channel.
        """
        channel = await self.get_current_channel(itx, action, from_event)
        if channel is None:
            return
        try:  # Check if executer is the VcTable owner
            if not channel.overwrites[itx.user].connect:
                raise KeyError("Not owner.")
        except KeyError:
            if from_event:
                return
            cmd_mention = self.client.get_command_mention('vctable create')
            await itx.response.send_message(f"Invalid permissions: You are not an owner of this VcTable! (Perhaps this isn't a VcTable yet: use {cmd_mention} to make it one!)", ephemeral=True)
            return
        return channel

    @vctable.command(name="create", description="Turn your custom vc into a cool vc")
    @app_commands.describe(owners="A list of extra owners for your VcTable. Separate with comma",
                           name="Give the channel a different name (api efficiency)")
    async def create_vctable(self, itx: discord.Interaction, owners: str = "", name: app_commands.Range[str,3,35] | None = None):
        warning = ""

        owners = owners.split(",")
        cmd_mention = self.client.get_command_mention("vctable add_owner")
        added_owners = []
        for mention in owners:
            if mention == "":
                continue
            mention: str = mention.strip()
            if not (mention[0:2] == "<@" and mention[-1] == ">"):
                warning = f"Note: You didn't give a good list of VcTable owners, so I only added you. To make more people owner, use {cmd_mention}.\n"
                added_owners = [str(itx.user.id)]
                break
            for char in mention[2:-1]:
                if char not in "0123456789":
                    warning = f"Note: You didn't give a good list of VcTable owners, so I only added you. To make more people owner, use {cmd_mention}.\n"
                    added_owners = [str(itx.user.id)]
                    break
            added_owners.append(mention)
        else:
            owner_list = [str(itx.user.id)] + [int(mention.strip()[2:-1]) for mention in added_owners]
            added_owners = []
            for owner_id in owner_list:
                if owner_id not in added_owners:
                    added_owners.append(owner_id)
        
        channel = await self.get_current_channel(itx, "create VcTable")
        if channel is None:
            return
        
        if name == channel.name:
            warning += ("Info: VcTables get a prefix, so the channel name is edited to include it. "
                        "Bots can only edit a channel's name twice every 10 minutes. If you wanted to also "
                        "change the channel name, you would need to run /editvc again, adding to that 2-rename limit. "
                        "For efficiency, you can provide a name here to do both of the edits at once (prefix and rename).\n"
                        "That means you don't have to give exactly the same name as the one the channel already had.")
        elif name == None:
            name = channel.name

        await itx.response.defer(ephemeral=True)
        # if owner present: already VcTable -> stop
        for target in channel.overwrites:
            if channel.overwrites[target].connect and target not in channel.category.overwrites:
                cmd_mention = self.client.get_command_mention("vctable owner")
                await itx.followup.send(f"This channel is already a VcTable! Use {cmd_mention} `mode:Check owners` to see who the owners of this table are!", ephemeral=True)
                return
        
        first_rename_time = try_store_vc_rename(itx.user.voice.channel.id)
        if first_rename_time:
            await itx.followup.send(f"This channel has been renamed too often in the past 10 minutes! (bcuz discord :P)\n" +
                                    f"You can turn this into a VcTable in <t:{first_rename_time + 600}:R> (<t:{first_rename_time + 600}:t>).", ephemeral=True)
            return
        
        for owner_id in added_owners: # TODO: put all overwrites into 1 api call with channel.edit(overwrites=...)
            owner = itx.guild.get_member(int(owner_id))
            await channel.set_permissions(
                owner,
                overwrite=discord.PermissionOverwrite(
                    connect=True,
                    speak=True,
                    view_channel=True,
                    read_message_history=True
                ),
                reason="VcTable created: set as owner"
            )
        
        await channel.set_permissions( # make sure the bot can still see the channel for vc events, even if /vctable lock
            self.client.user,
            overwrite=discord.PermissionOverwrite(
                view_channel=True
            ),
            reason="VcTable created: auto-set as participent"
        )

        owner_taglist = ', '.join([f'<@{id}>' for id in added_owners])
        cmd_mention = self.client.get_command_mention("vctable about")
        await channel.send(f"CustomVC converted to VcTable\n"
                           f"Use {cmd_mention} to learn more!\n"
                           f"Made {owner_taglist} a VcTable Owner\n"
                           f"**:warning: If someone is breaking the rules, TELL A MOD** (don't try to moderate a vc yourself)",allowed_mentions=discord.AllowedMentions.none())
        await log_to_guild(self.client, itx.guild, f"{itx.user.mention} ({itx.user.id}) turned a CustomVC ({channel.id}) into a VcTable")

        try:
            await channel.edit(name = self.client.custom_ids["vctable_prefix"] + name)
            await itx.followup.send("Successfully converted channel to VcTable and set you as owner.\n"+warning,ephemeral=True)
        except discord.errors.NotFound:
            await itx.followup.send("I was unable to name your VcTable, but I managed to set the permissions for it.")

    @vctable.command(name="owner", description="Manage the owners of your VcTable")
    @app_commands.describe(user="Who to add/remove as a VcTable owner (ignore if 'Check')")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Add owner', value=1),
        discord.app_commands.Choice(name='Remove owner', value=2),
        discord.app_commands.Choice(name='Check owners', value=3)
    ])
    async def edit_vctable_owners(self, itx: discord.Interaction, mode: int, user: discord.Member | None = None):
        if itx.user == user and mode != 3:
            if mode == 1:
                await itx.response.send_message("You can't set yourself as owner!", ephemeral=True)
            elif mode == 2:
                cmd_mention = self.client.get_command_mention("vctable owner")
                cmd_mention1 = self.client.get_command_mention("vctable disband")
                await itx.response.send_message("You can't remove your ownership of this VcTable!\n"
                                                f"You can make more people owner with {cmd_mention} `user: ` though..."
                                                f"If you want to delete the VcTable, you can use {cmd_mention1}",
                                                ephemeral=True)
            return

        if mode == 1:  # add
            warning = ""
            channel = await self.get_channel_if_owner(itx, "add owner")
            if channel is None:
                return
            if user is None:
                cmd_mention = self.client.get_command_mention("vctable make_authorized_only")
                await itx.response.send_message(f"You can add an owner to your VcTable using this command. Owners "
                                                f"have the ability to add speakers, mute, add other owners, disband "
                                                f"a vctable, or whitelist connecting and speaking. Give this to "
                                                f"people you believe can help you with this.",ephemeral=True)
                return
            try:
                if channel.overwrites[user].connect:
                    await itx.response.send_message(f"This user is already an owner!", ephemeral=True)
                    return
            except KeyError:
                pass
            perms_override = channel.overwrites[user].update(connect=True, speak=True, view_channel=True, read_message_history=True)
            await channel.set_permissions(user, overwrite=perms_override, reason="VcTable edited: set as owner (+speaker)")
            await channel.send(f"{itx.user.mention} added {user.mention} as VcTable owner.", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully added {user.mention} as owner." + warning, ephemeral=True)
            if user in channel.members:
                await user.move_to(channel)

        if mode == 2:  # remove
            channel = await self.get_channel_if_owner(itx, "remove owner")
            if channel is None:
                return
            if user is None:
                cmd_mention = self.client.get_command_mention("vctable owner")
                await itx.response.send_message(f"Removing owners is usually a bad sign.. Do not hesitate to make a "
                                                f"ticket for staff if there's something wrong.\n"
                                                f"Anyway. You can check current owners with {cmd_mention} `mode:Check`. "
                                                f"Then mention a user you want to delete in the `user: ` argument.", ephemeral=True)
                return
            try:
                if channel.overwrites[user].connect is not True: # if False or None
                    await itx.response.send_message("This user wasn't an owner yet.. Try taking someone else's ownership away.", ephemeral=True)
                    return
            except KeyError:
                pass
            perms_override = channel.overwrites[user].update(connect=None)
            await channel.set_permissions(user, overwrite=perms_override, reason="VcTable edited: removed as owner")
            await channel.send(f"{itx.user.mention} removed {user.mention} as VcTable owner", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully removed {user.mention} as owner. Keep in mind they are still a `speaker` and a `participant`.", ephemeral=True)

        if mode == 3:  # check
            channel = await self.get_current_channel(itx, "check owners")
            if channel is None:
                return
            owners = []
            for target in channel.overwrites:  # key in dictionary
                if channel.overwrites[target].connect:
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
    async def edit_vctable_speakers(self, itx: discord.Interaction, mode: int, user: discord.Member | None = None):
        if itx.user == user and mode != 3:
            await itx.response.send_message("You can't edit your own speaking permissions!", ephemeral=True)
            return

        if mode == 1:  # add
            channel = await self.get_channel_if_owner(itx, "add speaker")
            if channel is None:
                return
            if user is None:
                cmd_mention = self.client.get_command_mention("vctable make_authorized_only")
                await itx.response.send_message(f"You can add a speaker to your VcTable using this command."
                                                f"Using {cmd_mention}, you can let only those you've selected "
                                                f"be able to talk in your voice channel. This can be useful if "
                                                f"you want an on-topic convo or podcast with a select group of "
                                                f"people :)",ephemeral=True)
                return
            try:
                warning = "\nThis user was muted before. Making them a speaker removed their mute." if channel.overwrites[user].speak is False else ""
                if channel.overwrites[user].speak:
                    await itx.response.send_message(f"This user is already a speaker!", ephemeral=True)
                    return
            except KeyError:
                warning = ""
            try:
                if channel.overwrites[itx.guild.default_role].speak is not False:
                    cmd_mention = self.client.get_command_mention("vctable make_authorized_only")
                    warning += f"\nThis has no purpose until you enable 'authorized-only' using {cmd_mention}."
            except KeyError:
                pass
            perms_override = channel.overwrites[user].update(speak=True)
            await channel.set_permissions(user, overwrite=perms_override, reason="VcTable edited: set as speaker")
            await channel.send(f"{itx.user.mention} made {user.mention} a speaker.", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully made {user.mention} a speaker."+warning, ephemeral=True)
            if user in channel.members:
                await user.move_to(channel)

        if mode == 2:  # remove
            channel = await self.get_channel_if_owner(itx, "remove speaker")
            if channel is None:
                return
            if user is None:
                cmd_mention = self.client.get_command_mention("vctable owner")
                cmd_mention2 = self.client.get_command_mention("vctable speaker")
                await itx.response.send_message(f"You can remove speakers with this command. This only works if "
                                                f"the user you're trying to remove is not already a VcTable owner "
                                                f"(you'll need to use {cmd_mention} `mode:Remove owner` first).\n"
                                                f"To see current VcTable speakers, use {cmd_mention2} `mode:Check`.", ephemeral=True)
                return
            try:
                if channel.overwrites[user].speak is not True:
                    await itx.response.send_message(f"This user is not a speaker! You can't unspeech a non-speaker!", ephemeral=True)
                    return
                if channel.overwrites[user].connect:
                    await itx.response.send_message(f"This user is an owner of this VcTable! If you want to reset their speaking permissions, un-owner them first!", ephemeral=True)
                    return
            except KeyError:
                await itx.response.send_message(f"This user is not a speaker! You can't unspeech a non-speaker!", ephemeral=True)
                return
            warning = ""
            try:
                if channel.overwrites[itx.guild.default_role].speak is False:
                    cmd_mention = self.client.get_command_mention("vctable make_authorized_only")
                    warning = f"\nThis has no purpose until you enable 'authorized-only' using {cmd_mention}."
            except KeyError:
                pass
            perms_override = channel.overwrites[user].update(speak=None)
            await channel.set_permissions(user, overwrite=perms_override, reason="VcTable edited: removed as speaker")
            await channel.send(f"{itx.user.mention} removed {user.mention} as speaker.", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully removed {user.mention} as speaker."+warning, ephemeral=True)
            if user in channel.members:
                await user.move_to(channel)

        if mode == 3:  # check
            channel = await self.get_current_channel(itx, "check speakers")
            if channel is None:
                return
            speakers = []
            for target in channel.overwrites:  # key in dictionary
                if channel.overwrites[target].speak:
                    if isinstance(target, discord.Member):
                        speakers.append(target.mention)
            await itx.response.send_message("Here is a list of this VcTable's speakers:\n  " + ', '.join(speakers), ephemeral=True)

    @vctable.command(name="participant", description="Allow users to see channel (if '/vctable lock' is enabled)")
    @app_commands.describe(user="Who to add/remove as a VcTable participant (ignore if 'Check')")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Add participant', value=1),
        discord.app_commands.Choice(name='Remove participant', value=2),
        discord.app_commands.Choice(name='Check participants', value=3)
    ])
    async def edit_vctable_participants(self, itx: discord.Interaction, mode: int, user: discord.Member | None = None):
        if itx.user == user and mode != 3:
            await itx.response.send_message("You can't edit your own participation permissions!", ephemeral=True)
            return

        if mode == 1:  # add
            channel = await self.get_channel_if_owner(itx, "add participant")
            if channel is None:
                return
            if user is None:
                cmd_mention = self.client.get_command_mention("vctable lock")
                await itx.response.send_message(f"You can add a participant to your VcTable using this command."
                                                f"Using {cmd_mention}, you can let only those you've selected "
                                                f"be able to see your voice channel and read its messages. This "
                                                f"can be useful if you want an on-topic convo or private meeting "
                                                f"with a select group of people :)\n"
                                                f"Note: Staff can still view and join your voice channel.",ephemeral=True)
                return
            try:
                if channel.overwrites[user].view_channel:
                    await itx.response.send_message(f"This user is already a participant!", ephemeral=True)
                    return
            except KeyError:
                warning = ""
            try:
                if channel.overwrites[itx.guild.default_role].view_channel is not False:
                    cmd_mention = self.client.get_command_mention("vctable lock")
                    warning += f"\nThis has no purpose until you activate the 'lock' using {cmd_mention}."
            except KeyError:
                pass
            perms_override = channel.overwrites[user].update(view_channel=True, read_message_history=True)
            await channel.set_permissions(user, overwrite=perms_override, reason="VcTable edited: set as participant")
            await channel.send(f"{itx.user.mention} made {user.mention} a participant.", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully made {user.mention} a participant."+warning, ephemeral=True)
            # if user in channel.members:
            #     await user.move_to(channel)
            # # should be unnecessary for viewing permissions.

        if mode == 2:  # remove
            channel = await self.get_channel_if_owner(itx, "remove participant")
            if channel is None:
                return
            if user is None:
                cmd_mention = self.client.get_command_mention("vctable owner")
                cmd_mention2 = self.client.get_command_mention("vctable participant")
                await itx.response.send_message(f"You can remove participants with this command. This only works if "
                                                f"the user you're trying to remove is not already a VcTable owner "
                                                f"(you'll need to use {cmd_mention} `mode:Remove owner` first).\n"
                                                f"To see current VcTable participants, use {cmd_mention2} `mode:Check`.", ephemeral=True)
                return
            try:
                if channel.overwrites[user].view_channel is not True:
                    await itx.response.send_message("This user is not a participant! You can't remove the participation permissions they don't have!", ephemeral=True)
                    return
                if channel.overwrites[user].connect:
                    await itx.response.send_message("This user is an owner of this VcTable! If you want to reset their participation permissions, un-owner them first!", ephemeral=True)
                    return
                if user.id == self.client.user.id:
                    await itx.response.send_message(":warning: You are trying to hide this channel from the bot that manages this system!\n"
                                                    "Your command has been interrupted. Removing this user's viewing permissions would "
                                                    "make it unable to edit the voice channel or reapond to voice channel events (join/leave).",
                                                    ephemeral=True)
                    return
            except KeyError:
                await itx.response.send_message(f"This user is not a participant! You can't remove the participation permissions they don't have!", ephemeral=True)
                return
            warning = ""
            try:
                if channel.overwrites[itx.guild.default_role].view_channel is False:
                    cmd_mention = self.client.get_command_mention("vctable lock")
                    warning = f"\nThis has no purpose until you activate the 'lock' using {cmd_mention}."
            except KeyError:
                pass
            perms_override = channel.overwrites[user].update(view_channel=None, read_message_history=None)
            await channel.set_permissions(user, overwrite=perms_override, reason="VcTable edited: removed as participant")
            await channel.send(f"{itx.user.mention} removed {user.mention} as participant.", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully removed {user.mention} as participant."+warning, ephemeral=True)
            if user in channel.members:
                await user.move_to(channel)

        if mode == 3:  # check
            channel = await self.get_current_channel(itx, "check speakers")
            if channel is None:
                return
            participants = []
            for target in channel.overwrites:  # key in dictionary
                if channel.overwrites[target].view_channel:
                    if isinstance(target, discord.Member):
                        participants.append(target.mention)
            await itx.response.send_message("Here is a list of this VcTable's participants:\n  " + ', '.join(participants), ephemeral=True)

    @vctable.command(name="mute", description="Deny users to talk in your VcTable")
    @app_commands.describe(user="Who to mute/unmute (ignore if 'Check')")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Mute participant', value=1),
        discord.app_commands.Choice(name='Unmute participant', value=2),
        discord.app_commands.Choice(name='Check muted participants', value=3)
    ])
    async def edit_vctable_muted_participants(self, itx: discord.Interaction, mode: int, user: discord.Member | None = None):
        if itx.user == user and mode != 3:
            await itx.response.send_message("You can't " + "un"*(mode == 2) + "mute yourself!", ephemeral=True)
            return

        if mode == 1:  # mute
            channel = await self.get_channel_if_owner(itx, "mute participant")
            if channel is None:
                return
            if user is None:
                await itx.response.send_message("Muting someone is usually a bad sign... Don't hesitate to open "
                                                "a ticket with staff if there's something going on.\n"
                                                "Anyway. Mention a user in the `user: ` argument to mute that person.", ephemeral=True)
                return
            try:
                warning = "\nThis user was a speaker before. Muting them overwrote this permissions and removed their speaker permissions" if channel.overwrites[user].speak else ""
                if channel.overwrites[user].speak is False:
                    await itx.response.send_message(f"This user is already muted!", ephemeral=True)
                    return
                if channel.overwrites[user].connect:
                    await itx.response.send_message(f"This user is an owner of this VcTable! If you want to mute them, un-owner them first!", ephemeral=True)
                    return
            except KeyError:
                warning = ""

            if is_staff(itx.guild, user):
                await itx.response.send_message("You can't mute staff members! If you have an issue with staff, make a ticket or DM an admin!",ephemeral=True)
                return
            perms_override = channel.overwrites[user].update(speak=False, stream=False)
            await channel.set_permissions(user, overwrite=perms_override, reason="VcTable edited: muted participant")
            await channel.send(f"{itx.user.mention} muted {user.mention}.", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully muted {user.mention}."+warning, ephemeral=True)
            if user in channel.members:
                await user.move_to(channel)

        if mode == 2:  # unmute
            channel = await self.get_channel_if_owner(itx, "unmute user")
            if channel is None:
                return
            if user is None:
                cmd_mention = self.client.get_command_mention("vctable mute")
                await itx.response.send_message(f"This command lets you unmute a previously-muted person. "
                                                f"To see which people are muted, use {cmd_mention} `mode:Check`\n"
                                                f"Then simply mention this user in the `user: ` argument.", ephemeral=True)
                return
            try:
                if channel.overwrites[user].speak is not False: # if True or None
                    await itx.response.send_message(f"This user is already unmuted! Let people be silent if they wanna be >:(", ephemeral=True)
                    return
            except KeyError:
                await itx.response.send_message(f"This user is already unmuted! Let people be silent if they wanna be >:(", ephemeral=True)
                return
            perms_override = channel.overwrites[user].update(speak=None, stream=None)
            await channel.set_permissions(user, overwrite=perms_override, reason="VcTable edited: unmuted participant")
            await channel.send(f"{itx.user.mention} unmuted {user.mention}.", allowed_mentions=discord.AllowedMentions.none())
            await itx.response.send_message(f"Successfully unmuted {user.mention}.", ephemeral=True)
            if user in channel.members:
                await user.move_to(channel)

        if mode == 3:  # check
            channel = await self.get_current_channel(itx, "check muted users")
            if channel is None:
                return
            muted = []
            for target in channel.overwrites:  # key in dictionary
                if channel.overwrites[target].speak is False: # if they have no speaking perms = muted
                    if isinstance(target, discord.Member):
                        muted.append(target.mention)
            await itx.response.send_message("Here is a list of this VcTable's muted users:\n  " + ', '.join(muted), ephemeral=True)

    @vctable.command(name="make_authorized_only", description="Only let users speak if they are whitelisted by the owner")
    async def vctable_authorized_only(self, itx: discord.Interaction):
        channel = await self.get_channel_if_owner(itx, "enable authorized-only")
        if channel is None:
            return

        # if authorized-only is enabled -> (the role overwrite is not nonexistant and is False):
        if channel.overwrites.get(itx.guild.default_role, False):
            if channel.overwrites[itx.guild.default_role].speak is False:
                perms_override = channel.overwrites[itx.guild.default_role].update(speak=None)
                await channel.set_permissions(itx.guild.default_role, overwrite=perms_override, reason="VcTable edited: disaled authorized-only for speaking")
                await channel.send(f"{itx.user.mention} disabled whitelist for speaking.", allowed_mentions=discord.AllowedMentions.none())
                await itx.response.send_message(f"Successfully disabled speaking whitelist.", ephemeral=True)
                return

        # if authorized-only is disabled:
        view = GenericTwoButtonView(("Confirm", discord.ButtonStyle.green), ("Cancel", discord.ButtonStyle.red))
        cmd_mention = self.client.get_command_mention("vctable speaker")
        await itx.response.send_message(f"Enabling authorized-only (a whitelist) will make only owners and speakers (people that have been whitelisted) able to talk.\n"
                                        f"Please make sure everyone is aware of this change. "
                                        f"To whitelist someone, use {cmd_mention} `mode:Add` `user: `.",
                                        ephemeral=True,
                                        view=view)
        await view.wait()
        if view.value:
            perms_override = channel.overwrites[itx.guild.default_role].update(speak=False)
            await channel.set_permissions(itx.guild.default_role, overwrite=perms_override, reason="VcTable edited: enabled authorized-only for speaking")
            await channel.send(f"{itx.user.mention} enabled whitelist for speaking.", allowed_mentions=discord.AllowedMentions.none())
            for member in channel.members: # member has no owner or speaking perms, move to same vc?
                if member in channel.overwrites:
                    if channel.overwrites[member].speak or channel.overwrites[member].connect:
                        continue
                await member.move_to(channel)
            cmd_mention = self.client.get_command_mention("vctable speaker")
            await itx.edit_original_response(content= f"Successfully enabled whitelist. Use {cmd_mention} `user: ` to let more people speak.",
                                             view   = None)
        else:
            await itx.edit_original_response(content="Cancelling...", view=None)

    @vctable.command(name="lock", description="Only let users view vc if they are whitelisted by the owner")
    async def vctable_lock(self, itx: discord.Interaction):
        channel = await self.get_channel_if_owner(itx, "enable vctable lock")
        if channel is None:
            return

        # if lock is enabled -> (the role overwrite is not nonexistant and is False):
        if channel.overwrites.get(itx.guild.default_role, False):
            if channel.overwrites[itx.guild.default_role].view_channel is False:
                perms_override = channel.overwrites[itx.guild.default_role].update(view_channel=None, read_message_history=None)
                await channel.set_permissions(itx.guild.default_role, overwrite=perms_override, reason="VcTable edited: disabled viewing lock")
                await channel.send(f"{itx.user.mention} disabled whitelist for viewing this channel.", allowed_mentions=discord.AllowedMentions.none())
                await itx.response.send_message(f"Successfully disabled viewing whitelist.", ephemeral=True)
                return

        # if lock is disabled:
        view = GenericTwoButtonView(("Confirm", discord.ButtonStyle.green), ("Cancel", discord.ButtonStyle.red))
        cmd_mention = self.client.get_command_mention("vctable participant")
        await itx.response.send_message(f"Enabling the lock (a whitelist) will make only owners and participants (people that "
                                        f"have been whitelisted) able to see this server and message history.\n"
                                        f"Please make sure everyone is aware of this change. "
                                        f"To whitelist someone, use {cmd_mention} `mode:Add` `user: `.",
                                        ephemeral=True,
                                        view=view)
        await view.wait()
        if view.value:
            perms_override = channel.overwrites[itx.guild.default_role].update(view_channel=False, read_message_history=False)
            await channel.set_permissions(itx.guild.default_role, overwrite=perms_override, reason="VcTable edited: enabled viewing lock")
            await channel.send(f"{itx.user.mention} enabled whitelist for viewing the voice channel.", allowed_mentions=discord.AllowedMentions.none())
            # for member in channel.members: # member has no owner or viewing perms, move to same vc?
            #     if member in channel.overwrites:
            #         if channel.overwrites[member].view_channel or channel.overwrites[member].connect:
            #             continue
            #     await member.move_to(channel)
            cmd_mention = self.client.get_command_mention("vctable participant")
            await itx.edit_original_response(content= f"Successfully enabled whitelist. Use {cmd_mention} `user: ` to let more people speak.",
                                             view   = None)
        else:
            await itx.edit_original_response(content="Cancelling...", view=None)


    @vctable.command(name="disband", description="reset permissions and convert vctable back to customvc")
    async def vctable_disband(self, itx: discord.Interaction):
        channel = await self.get_channel_if_owner(itx, "disband VcTable")
        if channel is None:
            return

        await channel.edit(overwrites=channel.category.overwrites)  # reset overrides
        # update every user's permissions
        for user in channel.members:
            await user.move_to(channel)
        await channel.send(
            f"{itx.user.mention} disbanded the VcTable and turned it back to a normal CustomVC",allowed_mentions=discord.AllowedMentions.none())
        # remove channel's name prefix (seperately from the overwrites due to things like ratelimiting)
        await itx.response.send_message("Successfully disbanded VcTable.", ephemeral=True)
        if channel.name.startswith(self.client.custom_ids["vctable_prefix"]):
            new_channel_name = channel.name[len(self.client.custom_ids["vctable_prefix"]):]
            try_store_vc_rename(channel.id, max_rename_limit=3)
            # same as on_voice_state_update:
            # allow max 3 renamed: if a staff queued a rename due to rules, it'd be queued at 3.
            # it would be bad to have it be renamed back to the bad name right after.
            try:
                await channel.edit(name=new_channel_name)
            except discord.errors.NotFound:
                pass

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
                          f"{self.client.get_command_mention('vctable about')}: See this help page\n"
                          f"{self.client.get_command_mention('vctable create')} `[owners: ]`: Turns your CustomVC into a VcTable and makes you (and any additional mentioned user(s)) the owner\n"
                          f"{self.client.get_command_mention('vctable owner')} `mode: ` `user: `: Add/Remove an owner to your table. If you want to check the owners, then it doesn't matter what you fill in for 'user'\n"
                          f"{self.client.get_command_mention('vctable mute')} `mode: ` `user: `: Mute/Unmute a user in your table. If you want to check the muted participants, see ^ (same as for checking owners)\n"
                          f"{self.client.get_command_mention('vctable make_authorized_only')}: Toggle the whitelist for speaking\n"
                          f"{self.client.get_command_mention('vctable speaker')} `mode: ` `user: `: Add/Remove a speaker to your table. This user gets whitelisted to speak when authorized-only is enabled. Checking speakers works the same as checking owners and muted users\n"
                          f"{self.client.get_command_mention('vctable lock')}: Similar to make-authorized-only, but for viewing the voice channel and its message history.\n"
                          f"{self.client.get_command_mention('vctable participant')} `mode: ` `user: `: Add/Remove a participant to your table. This user gets whitelisted to view the channel and message history when the 'lock' is activated.\n")
        await itx.response.send_message(embeds=[embed1,embed2], ephemeral=True)
    # endregion Custom VcTables

async def setup(client):
    await client.add_cog(CustomVcs(client))

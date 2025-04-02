import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.settings.objects import ModuleKeys, AttributeKeys
from resources.customs.bot import Bot
from resources.checks.permissions import is_staff  # to let staff rename other people's custom vcs
from resources.checks import is_admin_check, module_enabled_check, MissingAttributesCheckFailure
from resources.utils.utils import log_to_guild  # to log custom vc changes

from extensions.customvcs.channel_rename_tracker import clear_vc_rename_log, try_store_vc_rename
from extensions.customvcs.modals import CustomVcStaffEditorModal
from extensions.customvcs.utils import is_vc_custom, BLACKLISTED_CHANNELS


async def _reset_voice_channel_permissions_if_vctable(vctable_prefix: str, voice_channel: discord.VoiceChannel):
    """
    Reset a voice channel's permission overrides if the 'owners' of the voice channel
    table are no longer present/connected to the channel.

    :param vctable_prefix: The prefix of voice channel tables, to remove/rename it if the vctable owners left.
    :param voice_channel: The channel to reset permissions for.

    .. note::

        This function does not check if the channel is actually a custom voice channel.
    """
    if len(voice_channel.overwrites) > len(
            voice_channel.category.overwrites):  # if VcTable, reset ownership; and all owners leave: reset all perms
        reset_vctable = True  # check if no owners left --> all members in the voice channel aren't owner
        for target in voice_channel.overwrites:
            if target not in voice_channel.members:
                continue
            if voice_channel.overwrites[target].connect:
                reset_vctable = False
                break
        if not reset_vctable:
            return

        try:
            await voice_channel.edit(
                overwrites=voice_channel.category.overwrites)  # reset overrides; error caught in try-except
            # update every user's permissions
            for user in voice_channel.members:
                await user.move_to(voice_channel)
            await voice_channel.send(
                "This channel was converted from a VcTable back to a normal CustomVC because all the owners left")
            # remove channel's name prefix (seperately from the overwrites due to things like ratelimiting)
            if voice_channel.name.startswith(vctable_prefix):
                new_channel_name = voice_channel.name[len(vctable_prefix):]
                try_store_vc_rename(voice_channel.id, max_rename_limit=3)
                # same as `/vctable disband`
                # allow max 3 renamed: if a staff queued a rename due to rules, it'd be queued at 3.
                # it would be bad to have it be renamed back to the bad name right after.
                await voice_channel.edit(name=new_channel_name)  # error caught in try-except
        except discord.errors.NotFound:  # catch two possible voice_channel.edit() exceptions
            pass  # event triggers after vc could be deleted already


async def _create_new_custom_vc(
        client: Bot,
        member: discord.Member,
        voice_channel: discord.VoiceChannel,
        customvc_category: discord.CategoryChannel,
        customvc_hub: discord.VoiceChannel,
):
    """
    A helper function to create a new custom voice channel

    :param client: The Bot class to use for logging.
    :param member: The member that triggered the event/function.
    :param voice_channel: The voice channel the user joined to trigger this function (the customvc hub)
    :param customvc_category: The category to create the custom voice channel in.
    :param customvc_hub: The custom voice channel hub channel.
    """

    default_name = "Untitled voice chat"
    warning = ""
    cmd_mention = client.get_command_mention("editvc")

    try:
        vc = await customvc_category.create_voice_channel(default_name, position=voice_channel.position + 1)
    except discord.errors.HTTPException:
        await log_to_guild(client, member.guild, "WARNING: COULDN'T CREATE CUSTOM VOICE CHANNEL: TOO MANY (max 50?)")
        raise

    try:
        await member.move_to(vc, reason="Opened a new voice channel through the vc hub thing.")
        await vc.send(
            f"Voice channel <#{vc.id}> ({vc.id}) created by <@{member.id}> ({member.id}). "
            f"Use {cmd_mention} to edit the name/user limit.",
            allowed_mentions=discord.AllowedMentions.none())
        for custom_vc in customvc_category.voice_channels:
            if custom_vc.id == customvc_hub or custom_vc.id == vc.id:
                continue
            await custom_vc.edit(position=custom_vc.position + 1)
    except discord.HTTPException as ex:
        warning = str(ex) + ": User clicked the vcHub too fast, and it couldn't move them to their new channel\n"
        try:
            await member.move_to(None,
                                 reason="Couldn't create a new Custom voice channel so kicked them from their "
                                        "current vc to prevent them staying in the main customvc hub")
            # no need to delete vc if they are kicked out of the channel, cause then the next event will
            # notice that they left the channel.
        except discord.HTTPException:
            await vc.delete()
        await client.log_channel.send(content=warning, allowed_mentions=discord.AllowedMentions.none())
        raise

    await log_to_guild(client, member.guild,
                       warning + f"{member.nick or member.name} ({member.id}) created and joined "
                                 f"voice channel {vc.id} (with the default name).")


async def _handle_delete_custom_vc(client: Bot, member: discord.Member, voice_channel: discord.VoiceChannel):
    """
    Handle the deletion of a custom voice channel (and error handling)

    :param client: The bot instance to log to guild with.
    :param member: The member to log as last in vc.
    :param voice_channel: The voice channel to remove.
    """
    clear_vc_rename_log(voice_channel.id)
    try:
        await voice_channel.delete()
    except discord.errors.NotFound:
        await log_to_guild(client, member.guild,
                           f":warning: **WARNING!! Couldn't delete CustomVC channel** {member.nick or member.name} "
                           f"({member.id}) left voice channel \"{voice_channel.name}\" ({voice_channel.id}), and "
                           f"was the last one in it, but it **could not be deleted**!")
        raise
    await log_to_guild(client, member.guild,
                       f"{member.nick or member.name} ({member.id}) left voice channel \"{voice_channel.name}\" "
                       f"({voice_channel.id}), and was the last one in it, so it was deleted.")


async def _handle_custom_voice_channel_leave_events(
        client: Bot, member: discord.Member, voice_channel: discord.VoiceChannel
):
    """
    A helper function to handle the custom voice channel events when a user leaves a channel.
    This includes: channel deletion, vctable disbanding.

    :param client: The client to send logs with, and for the vctable prefix.
    :param member: The member to trigger the leave event.
    :param voice_channel: The voice channel that the member left from.
    """
    # The following events should only apply to custom voice channels:

    if len(voice_channel.members) == 0:
        await _handle_delete_custom_vc(client, member, voice_channel)

    await _reset_voice_channel_permissions_if_vctable(client.custom_ids["vctable_prefix"], voice_channel)


@app_commands.check(is_admin_check)
async def _edit_guild_info_autocomplete(_: discord.Interaction, current: str) -> list[app_commands.Choice]:
    if current.startswith("1") or current.startswith("2") or current.startswith("3") or current.startswith(
            "4") or current.startswith("5"):
        options = [
            ["Help: Main server settings", "01"],
            ["Help: Custom Voice Channels", "02"],
            ["Help: Starboard settings", "03"],
            ["Help: Bumping-related settings", "04"],
            ["Help: Additional settings", "05"],

            ["Logging channel", "11"],
            ["Poll reactions blacklist", "12"],

            ["CustomVC Hub", "21"],
            ["CustomVC creation Category", "22"],
            ["CustomVC No-mic channel", "23"],

            ["Starboard emoji", "31"],
            ["Starboard channel", "32"],
            ["Minimum required stars for starboard", "33"],
            ["Starboard blacklisted channels", "34"],
            ["Starboard downvote initiation value", "35"],

            ["ID of the bump bot / DISBOARD bot", "41"],
            ["Channel that DISBOARD bumps in", "42"],
            ["Role to ping when sending reminder", "43"],

            ["Vc Activity Logs channel", "51"],
        ]
        return [
                   app_commands.Choice(name=option[0], value=option[1])
                   for option in options if option[1].startswith(current)
               ][:15]
    else:
        options = [
            ["Main server settings", "01"],
            ["Custom Voice Channels", "02"],
            ["Starboard settings", "03"],
            ["Bumping-related settings", "04"],
            ["Additional settings", "05"],
        ]
        return [
                   app_commands.Choice(name=option[0], value=option[1])
                   for option in options if current.lower() in option[0]
               ][:15]


class CustomVcs(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        self.blacklisted_channels = BLACKLISTED_CHANNELS
        #  # General, #Private, #Quiet, and #Minecraft. Later, it also excludes channels starting with "〙"

    @commands.Cog.listener()
    async def on_voice_state_update(
            self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        if not self.client.is_module_enabled(member.guild, ModuleKeys.custom_vcs):
            return

        customvc_hub: discord.VoiceChannel | None
        customvc_category: discord.CategoryChannel | None
        customvc_hub, customvc_category = self.client.get_guild_attribute(
            member.guild, AttributeKeys.custom_vc_create_channel, AttributeKeys.custom_vc_category)
        if customvc_hub is None or customvc_category is None:
            return  # todo: confirm if I should just return here or try to send to a log channel?

        if before.channel is not None and before.channel in before.channel.guild.voice_channels:
            if is_vc_custom(before.channel, customvc_category, customvc_hub, self.blacklisted_channels):
                # only run if this voice state regards a custom voice channel
                await _handle_custom_voice_channel_leave_events(self.client, member, before.channel)

        if after.channel is not None:
            if after.channel.id == customvc_hub:
                await _create_new_custom_vc(self.client, member, after.channel, customvc_category, customvc_hub)

    @app_commands.command(name="editvc", description="Edit your voice channel name or user limit")
    @app_commands.describe(name="Give your voice channel a name!",
                           limit="Give your voice channel a user limit!")
    @module_enabled_check(ModuleKeys.custom_vcs)
    async def edit_custom_vc(
            self, itx: discord.Interaction,
            name: app_commands.Range[str, 3, 35] | None = None,
            limit: app_commands.Range[int, 0, 99] | None = None
    ):
        vc_hub, vc_log, vc_category = await itx.client.get_guild_info(
            itx.guild,
            AttributeKeys.custom_vc_create_channel,
            AttributeKeys.log_channel,
            AttributeKeys.custom_vc_category
        )

        if None in (vc_hub, vc_log, vc_category):
            raise MissingAttributesCheckFailure(*[i for i in (vc_hub, vc_log, vc_category) if i is None])

        warning = ""

        if itx.user.voice is None:
            if is_staff(itx, itx.user):
                await itx.response.send_modal(CustomVcStaffEditorModal(itx.client, vc_hub, vc_log, vc_category))
                return
            await itx.response.send_message("You must be connected to a voice channel to use this command",
                                            ephemeral=True)
            return
        channel = itx.user.voice.channel
        if (channel.category.id not in [vc_category] or
                channel.id == vc_hub or
                channel.id in self.blacklisted_channels or
                channel.name.startswith("〙")):
            await itx.response.send_message("You can't change that voice channel's name!", ephemeral=True)
            return
        if name is not None:
            if name.startswith("〙"):  # todo attribute: make this character a ServerAttribute too.
                await itx.response.send_message("Due to the current layout, you can't change your channel to "
                                                "something starting with '〙'. Sorry for the inconvenience",
                                                ephemeral=True)
                return
            if name == "Untitled voice chat":
                warning += "Are you really going to change it to that..\n"
            if len(itx.user.voice.channel.overwrites) > len(
                    itx.user.voice.channel.category.overwrites):  # if VcTable, add prefix
                name = itx.client.custom_ids["vctable_prefix"] + name

        if name is not None:
            # don't add cooldown if you only change the limit, not the name
            first_rename_time = try_store_vc_rename(channel.id)
            if first_rename_time:
                await itx.response.send_message(
                    f"You can't edit your channel more than twice in 10 minutes! (bcuz discord :P)\n"
                    f"You can rename it again <t:{first_rename_time + 600}:R> (<t:{first_rename_time + 600}:t>).",
                    ephemeral=True)
                return

        limit_info = ""
        old_name = channel.name
        old_limit = channel.user_limit
        try:
            if not limit and not name:
                await itx.response.send_message(
                    "You can edit your channel with this command. Set a value for the name or the maximum user limit.",
                    ephemeral=True)
            if not limit and name:
                await channel.edit(reason=f"Voice channel renamed from \"{channel.name}\" to \"{name}\"{limit_info}",
                                   name=name)
                await log_to_guild(itx.client, itx.guild,
                                   f"Voice channel ({channel.id}) renamed from \"{old_name}\" to \"{name}\" "
                                   f"(by {itx.user.nick or itx.user.name}, {itx.user.id})")
                await itx.response.send_message(warning + f"Voice channel successfully renamed to \"{name}\"",
                                                ephemeral=True)  # allowed_mentions=discord.AllowedMentions.none())
            if limit and not name:
                await channel.edit(reason=f"Voice channel limit edited from \"{old_limit}\" to \"{limit}\"",
                                   user_limit=limit)
                await log_to_guild(itx.client, itx.guild,
                                   f"Voice channel \"{old_name}\" ({channel.id}) edited the user limit "
                                   f"from \"{old_limit}\" to \"{limit}\" "
                                   f"(by {itx.user.nick or itx.user.name}, {itx.user.id}){limit_info}")
                await itx.response.send_message(
                    warning + f"Voice channel user limit for \"{old_name}\" successfully edited "
                              f"from \"{old_limit}\" to \"{limit}\"",
                    ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
            if limit and name:
                await channel.edit(
                    reason=f"Voice channel edited from name: \"{channel.name}\" to \"{name}\" and user limit "
                           f"from \"{limit}\" to \"{old_limit}\"",
                    user_limit=limit, name=name)
                await log_to_guild(itx.client, itx.guild,
                                   f"{itx.user.nick or itx.user.name} ({itx.user.id}) changed VC ({channel.id}) "
                                   f"name \"{old_name}\" to \"{name}\" and "
                                   f"user limit from \"{old_limit}\" to \"{limit}\"{limit_info}")
                await itx.response.send_message(warning + "Voice channel name and user limit successfully edited.",
                                                ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        except discord.errors.HTTPException as ex:
            ex_message = repr(ex).split("(", 1)[1][1:-2]
            await log_to_guild(itx.client, itx.guild,
                               f"Warning! >> {ex_message} << {itx.user.nick or itx.user.name} ({itx.user.id}) "
                               f"tried to change {old_name} ({channel.id}) to {name}, but wasn't allowed to by "
                               f"discord, probably because it's in a banned word list for discord's "
                               f"discovery <@262913789375021056>")

    @app_commands.check(is_admin_check)
    @app_commands.command(name="editguildinfo", description="Edit guild settings (staff only)")
    @app_commands.describe(mode="Do you want to edit, or just see the values of the guild settings?",
                           option="What value do you want to edit?",
                           value="Edit what value? (ignore this if viewing a value)")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='View guild settings', value=1),
        discord.app_commands.Choice(name='Edit guild settings', value=2),
    ])
    @app_commands.autocomplete(option=_edit_guild_info_autocomplete)
    async def edit_guild_info(self, itx: discord.Interaction, mode: int, option: str, value: str):
        # todo: delete command
        options = {
            "01": "Help: Main server settings",
            "02": "Help: Custom Voice Channels",
            "03": "Help: Starboard settings",
            "04": "Help: Bumping-related settings",
            "05": "Help: Additional settings",

            "11": "vcLog",
            "12": "pollReactionsBlacklist",

            "21": "vcHub",
            "22": "vcCategory",
            "23": "vcNoMic",

            "31": "starboardEmoji",
            "32": "starboardChannel",
            "33": "starboardCountMinimum",
            "34": "starboardBlacklistedChannels",
            "35": "starboardDownvoteInitValue",

            "41": "bumpBot",
            "42": "bumpChannel",
            "43": "bumpRole",

            "51": "vcActivityLogChannel"
        }

        if option not in options:
            await itx.response.send_message(
                "Your mode has to be a number. Type one of the autocomplete suggestions to "
                "figure out which number/ID you need.", ephemeral=True)
            return
        if option.startswith("0"):
            if option == "01":
                await itx.response.send_message(
                    "Main server settings:\n"
                    "`11`: Log (What channel does Rina log to?). This includes the following:\n" +
                    "        Starting Rina\n"
                    "        Custom voice channel creations/deletions, renames and user-limiting on these, "
                    "and /vctable,\n"
                    "        Starboard creations, deletions (both manual ('delete message') and automatic "
                    "('score:-1'))\n"
                    "        Staff actions (dictionary commands, /say, public anonymous /tag commands, "
                    "/delete_week_selfies, \n"
                    "        Warnings (starboard ':x:' used on a deleted message, adding a reaction to "
                    "someone that blocked rina)\n"
                    "        Errors (crashes in a command, missing guild_info data, etc.)\n"
                    "`12`: Poll reactions blacklist (Which channels can /add_poll_reactions not be used in?)",
                    ephemeral=True)
            elif option == "02":
                await itx.response.send_message(
                    "Custom Voice Channels:\n"
                    "`21`: VC Hub (Which channel should people join to create a new Custom voice channel (CustomVC)?)\n"
                    "`22`: VC category (Which category are Custom voice channels created in?)\n"
                    "`23`: VC no-mic (Which channel should custom new)", ephemeral=True)
            elif option == "03":
                await itx.response.send_message(
                    "Starboard settings:\n"
                    "`31`: Starboard emoji (what emoji can people add to add something to the starboard?)\n"
                    "`32`: Starboard channel (which channel are starboard messages sent in?)\n"
                    "`33`: Star minimum (how many stars does a message need before it's added to the starboard?)\n"
                    "`34`: Starboard blacklist (what channels' messages can't be starboarded? (list))\n"
                    "`35`: Starboard downvote initiation value (how many total (up/down)votes must a message have "
                    "before a negative score can cause it to be deleted?)",
                    ephemeral=True)
            elif option == "04":
                await itx.response.send_message(
                    "Bumping-related settings:\n"
                    "`41`: Bump bot: DISBOARD.org (Whose messages should I check for bump messages with embeds?)\n"
                    "`42`: Bump channel (Which channel should be checked for messages by the DISBOARD bot?)\n"
                    "`43`: Bump role (Which role should be pinged when 2 hours have passed?)",
                    ephemeral=True)
            elif option == "05":
                await itx.response.send_message(
                    "Additional settings:\n"
                    "`51`: Voice channel activity channel (What channel logs people joining/leaving/moving VCs?) "
                    "(assumes Logger#6088 bot)", ephemeral=True)  # todo: confirm this is still the case
            return

        if mode == 1:
            try:
                value = await itx.client.get_guild_info(itx.guild, options[option])
            except KeyError:
                await itx.response.send_message("This server does not yet have a value for this option!",
                                                ephemeral=True)
                return
            await itx.response.send_message(
                "Here is the value for " + options[option] + " in this guild (" + str(itx.guild.id) + "):\n\n" +
                str(value), ephemeral=True)
        if mode == 2:
            query = {"guild_id": itx.guild_id}
            collection = itx.client.rina_db["guildInfo"]

            async def to_int(non_int, error_msg):
                try:
                    return int(non_int)
                except ValueError:
                    await itx.response.send_message(error_msg, ephemeral=True)
                    return None

            if option == "11":
                value = await to_int(value, "You have to give a numerical ID for the channel you want to use!")
                if value is None:
                    return
                ch = itx.client.get_channel(value)
                if not isinstance(ch, discord.abc.Messageable):
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking "
                                                    f"for! (Needs to be a channel I can message in; got {type(ch)})",
                                                    ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: ch.id}}, upsert=True)
            elif option == "12":
                channel_ids = value.split(",")
                blacklist: list[int] = []
                for channel_id in channel_ids:
                    channel = await to_int(channel_id.strip(), "You need to give a list of integers, separated "
                                                               "by a comma, for this new blacklist!")
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
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking "
                                                    f"for! (Need <class 'discord.VoiceChannel'>, got {type(ch)})",
                                                    ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: ch.id}}, upsert=True)
            elif option == "22":
                value = await to_int(value, "You have to give a numerical ID for the category you want to use!")
                if value is None:
                    return
                ch = itx.client.get_channel(value)
                if type(ch) is not discord.CategoryChannel:
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking "
                                                    f"for! (Need <class 'discord.CategoryChannel'>, got {type(ch)})",
                                                    ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: ch.id}}, upsert=True)
            elif option == "23":
                value = await to_int(value, "You have to give a numerical ID for the channel you want to use!")
                if value is None:
                    return
                ch = itx.client.get_channel(value)
                if type(ch) is not discord.TextChannel:
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking "
                                                    f"for! (Need <class 'discord.TextChannel'>, got {type(ch)})",
                                                    ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: ch.id}}, upsert=True)
            elif option == "31":
                value = await to_int(value, "You have to give a numerical ID for the emoji you want to use!")
                if value is None:
                    return
                emoji = itx.client.get_emoji(value)
                print(emoji)
                if type(emoji) is not discord.Emoji:
                    await itx.response.send_message(
                        "The ID you gave wasn't an emoji! (i think) (or not one I can use)", ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: emoji.id}}, upsert=True)
            elif option == "32":
                value = await to_int(value, "You have to give a numerical ID for the channel you want to use!")
                if value is None:
                    return
                ch = itx.client.get_channel(value)
                if not isinstance(ch, discord.TextChannel):
                    await itx.response.send_message(f"The ID you gave wasn't for the type of channel I was looking "
                                                    f"for! (Need <class 'discord.TextChannel'>; got {type(ch)})",
                                                    ephemeral=True)
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
                    channel = await to_int(channel_id.strip(), "You need to give a list of integers, separated "
                                                               "by a comma, for this new blacklist!")
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
                    await itx.response.send_message("The ID you gave wasn't for the type of channel I was looking "
                                                    "for! (Needs Messageable (TextChannel or Thread)",
                                                    ephemeral=True)
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
                    await itx.response.send_message("The ID you gave wasn't for the type of channel I was looking for!",
                                                    ephemeral=True)
                    return
                collection.update_one(query, {"$set": {options[option]: ch.id}}, upsert=True)

            await itx.response.send_message(f"Edited value of '{options[option]}' successfully.", ephemeral=True)

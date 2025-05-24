import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.settings.objects import ModuleKeys, AttributeKeys
from resources.customs import Bot
from resources.checks.permissions import is_staff
# ^ to let staff rename other people's custom vcs
from resources.checks import (
    module_enabled_check, MissingAttributesCheckFailure
)
from resources.utils.utils import log_to_guild  # to log custom vc changes

from extensions.customvcs.channel_rename_tracker import (
    clear_vc_rename_log,
    try_store_vc_rename
)
from extensions.customvcs.modals import CustomVcStaffEditorModal
from extensions.customvcs.utils import is_vc_custom


async def _reset_voice_channel_permissions_if_vctable(
        vctable_prefix: str,
        voice_channel: discord.VoiceChannel
):
    """
    Reset a voice channel's permission overrides if the 'owners' of the
    voice channel table are no longer present/connected to the channel.

    :param vctable_prefix: The prefix of voice channel tables, to
     remove/rename it if the vctable owners left.
    :param voice_channel: The channel to reset permissions for.

    .. note::

        This function does not check if the channel is actually a
        custom voice channel.
    """
    if len(voice_channel.overwrites) > len(  # todo: invert if-statement
            voice_channel.category.overwrites):
        # if VcTable, reset ownership; and all owners leave:
        #  reset all perms
        reset_vctable = True
        # check if no owners left --> all members in the voice channel
        #  aren't owner.
        for target in voice_channel.overwrites:
            if target not in voice_channel.members:
                continue
            if voice_channel.overwrites[target].connect:
                reset_vctable = False
                break
        if not reset_vctable:
            return

        try:
            # reset overrides; error caught in try-except
            await voice_channel.edit(
                overwrites=voice_channel.category.overwrites)
            # update every user's permissions
            for user in voice_channel.members:
                await user.move_to(voice_channel)
            await voice_channel.send(
                "This channel was converted from a VcTable back to a normal"
                " CustomVC because all the owners left"
            )
            # remove channel's name prefix (seperately from the
            #  overwrites due to things like ratelimiting)
            if voice_channel.name.startswith(vctable_prefix):
                new_channel_name = voice_channel.name[len(vctable_prefix):]
                try_store_vc_rename(voice_channel.id, max_rename_limit=3)
                # same as `/vctable disband`
                # allow max 3 renamed: if a staff queued a rename due
                #  to rules, it'd be queued at 3. It would be bad to
                #  have it be renamed back to the bad name right after.
                await voice_channel.edit(name=new_channel_name)
                # ^ error caught in try-except
        except discord.errors.NotFound:
            # catches two possible voice_channel.edit() exceptions
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
    :param voice_channel: The voice channel the user joined to trigger
     this function (the customvc hub)
    :param customvc_category: The category to create the custom voice
     channel in.
    :param customvc_hub: The custom voice channel hub channel.
    """

    default_name = "Untitled voice chat"
    warning = ""

    try:
        vc = await customvc_category.create_voice_channel(
            default_name, position=voice_channel.position + 1)
    except discord.errors.HTTPException:
        await log_to_guild(
            client,
            member.guild,
            "WARNING: COULDN'T CREATE CUSTOM VOICE CHANNEL: TOO MANY (max 50?)"
        )
        raise

    try:
        await member.move_to(
            vc,
            reason="Opened a new voice channel through the vc hub thing."
        )
        cmd_editvc = client.get_command_mention("editvc")
        await vc.send(
            f"Voice channel <#{vc.id}> ({vc.id}) created by "
            f"<@{member.id}> ({member.id}). Use {cmd_editvc} to edit the "
            f"name/user limit.",
            allowed_mentions=discord.AllowedMentions.none()
        )
        for custom_vc in customvc_category.voice_channels:
            if custom_vc.id == customvc_hub or custom_vc.id == vc.id:
                continue
            await custom_vc.edit(position=custom_vc.position + 1)
    except discord.HTTPException as ex:
        try:
            await member.move_to(
                None,
                reason="Couldn't create a new Custom voice channel so kicked "
                       "them from their current vc to prevent them staying "
                       "in the main customvc hub"
            )
            # no need to delete vc if they are kicked out of the
            #  channel, cause then the next event
            #  (on_voice_state_update) will notice that they left
            #  the channel.
        except discord.HTTPException:
            await vc.delete()
        warning = str(ex) + (": User clicked the vcHub too fast, and it "
                             "couldn't move them to their new channel\n")
        await log_to_guild(client, member.guild, msg=warning)
        raise

    await log_to_guild(
        client,
        member.guild,
        warning + f"{member.nick or member.name} ({member.id}) created and "
                  f"joined voice channel {vc.id} (with the default name)."
    )


async def _handle_delete_custom_vc(
        client: Bot,
        member: discord.Member,
        voice_channel: discord.VoiceChannel
):
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
        await log_to_guild(
            client,
            member.guild,
            f":warning: **WARNING!! Couldn't delete CustomVC channel** "
            f"{member.nick or member.name} ({member.id}) left voice channel "
            f"\"{voice_channel.name}\" ({voice_channel.id}), and "
            f"was the last one in it, but it **could not be deleted**!"
        )
        raise
    await log_to_guild(
        client,
        member.guild,
        f"{member.nick or member.name} ({member.id}) left voice channel "
        f"\"{voice_channel.name}\" ({voice_channel.id}), and was the last one "
        f"in it, so it was deleted."
    )


async def _handle_custom_voice_channel_leave_events(
        client: Bot,
        member: discord.Member,
        voice_channel: discord.VoiceChannel,
        vctable_prefix: str
):
    """
    A helper function to handle the custom voice channel events when
    a user leaves a channel. This includes: channel deletion,
    vctable disbanding.

    :param client: The client to send logs with, and for the
     vctable prefix.
    :param member: The member to trigger the leave event.
    :param voice_channel: The voice channel that the member left from.
    """
    # The following events should only apply to custom voice channels:

    if len(voice_channel.members) == 0:
        await _handle_delete_custom_vc(client, member, voice_channel)

    # todo: move this to vctables cog
    await _reset_voice_channel_permissions_if_vctable(
        vctable_prefix, voice_channel)


class CustomVcs(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_voice_state_update(
            self,
            member: discord.Member,
            before: discord.VoiceState,
            after: discord.VoiceState
    ):
        if not self.client.is_module_enabled(
                member.guild, ModuleKeys.custom_vcs):
            return

        customvc_hub: discord.VoiceChannel | None
        customvc_category: discord.CategoryChannel | None
        vctable_prefix: str | None
        blacklisted_channels: list[discord.VoiceChannel]
        (
            customvc_hub, customvc_category, vctable_prefix,
            blacklisted_channels, vc_blacklist_prefix
        ) = self.client.get_guild_attribute(
            member.guild,
            AttributeKeys.custom_vc_create_channel,
            AttributeKeys.custom_vc_category,
            AttributeKeys.vctable_prefix,
            AttributeKeys.custom_vc_blacklisted_channels,
            AttributeKeys.custom_vc_blacklist_prefix
        )
        if None in (customvc_hub, customvc_category,
                    vctable_prefix, vc_blacklist_prefix):
            # `blacklisted_channels` can be left empty.
            missing = [key for key, value in {
                AttributeKeys.custom_vc_create_channel: customvc_hub,
                AttributeKeys.custom_vc_category: customvc_category,
                AttributeKeys.vctable_prefix: vctable_prefix,
                AttributeKeys.custom_vc_blacklist_prefix: vc_blacklist_prefix
            }.items()
                if value is None]
            raise MissingAttributesCheckFailure(
                ModuleKeys.custom_vcs, missing)

        if (before.channel is not None
                and before.channel in before.channel.guild.voice_channels):
            if is_vc_custom(before.channel, customvc_category, customvc_hub,
                            blacklisted_channels, vc_blacklist_prefix):
                # only run if this voice state regards a custom voice channel
                await _handle_custom_voice_channel_leave_events(
                    self.client, member, before.channel, vctable_prefix)

        if after.channel is not None:
            if after.channel.id == customvc_hub.id:
                await _create_new_custom_vc(
                    self.client,
                    member,
                    after.channel,
                    customvc_category,
                    customvc_hub
                )

    @app_commands.command(
        name="editvc",
        description="Edit your voice channel name or user limit"
    )
    @app_commands.describe(name="Give your voice channel a name!",
                           limit="Give your voice channel a user limit!")
    @module_enabled_check(ModuleKeys.custom_vcs)
    async def edit_custom_vc(
            self, itx: discord.Interaction[Bot],
            name: app_commands.Range[str, 3, 35] | None = None,
            limit: app_commands.Range[int, 0, 99] | None = None
    ):
        (vc_hub, vc_log, vc_category, vctable_prefix, vc_blacklist_prefix,
         vc_blacklisted_channels) = itx.client.get_guild_attribute(
            itx.guild,
            AttributeKeys.custom_vc_create_channel,
            AttributeKeys.log_channel,
            AttributeKeys.custom_vc_category,
            AttributeKeys.vctable_prefix,
            AttributeKeys.custom_vc_blacklist_prefix,
            AttributeKeys.custom_vc_blacklisted_channels,
        )
        assert type(vc_blacklisted_channels) is list

        if None in (vc_hub, vc_log, vc_category, vctable_prefix,
                    vc_blacklist_prefix):
            missing = [key for key, value in {
                AttributeKeys.custom_vc_create_channel: vc_hub,
                AttributeKeys.log_channel: vc_log,
                AttributeKeys.custom_vc_category: vc_category,
                AttributeKeys.vctable_prefix: vctable_prefix,
                AttributeKeys.custom_vc_blacklist_prefix: vc_blacklist_prefix
            }.items()
                if value is None]
            raise MissingAttributesCheckFailure(
                ModuleKeys.custom_vcs, missing)

        warning = ""

        if itx.user.voice is None:
            if is_staff(itx, itx.user):
                staff_modal = CustomVcStaffEditorModal(
                    vc_hub, vc_log, vc_category, vctable_prefix)
                await itx.response.send_modal(staff_modal)
                return
            await itx.response.send_message(
                "You must be connected to a voice channel to use this command",
                ephemeral=True
            )
            return
        channel = itx.user.voice.channel
        if (channel.category != vc_category
                or channel.id == vc_hub
                or channel in vc_blacklisted_channels
                or channel.name.startswith(vc_blacklist_prefix)):
            await itx.response.send_message(
                "You can't change that voice channel's name!",
                ephemeral=True
            )
            return
        if name is not None:
            if name.startswith(vc_blacklist_prefix):
                await itx.response.send_message(
                    "The name you provided starts with this server's custom "
                    "voice channel blacklist prefix. Channels with this name "
                    "don't get seen as a custom voice channel. Unfortunately, "
                    "you will have to pick a different name (or at least have "
                    "it start with different letters) to rename your custom "
                    "voice channel.",
                    ephemeral=True)
                return
            if name == "Untitled voice chat":
                warning += "Are you really going to change it to that..\n"
            if len(itx.user.voice.channel.overwrites) > len(
                    itx.user.voice.channel.category.overwrites):
                # if VcTable, add prefix
                name = vctable_prefix + name

        if name is not None:
            # don't add cooldown if you only change the limit, not the name
            first_rename_time = try_store_vc_rename(channel.id)
            if first_rename_time:
                await itx.response.send_message(
                    f"You can't edit your channel more than twice in 10 "
                    f"minutes! (bcuz discord :P)\n"
                    f"You can rename it again <t:{first_rename_time + 600}:R> "
                    f"(<t:{first_rename_time + 600}:t>).",
                    ephemeral=True)
                return

        limit_info = ""
        old_name = channel.name
        old_limit = channel.user_limit
        try:
            if not limit and not name:
                await itx.response.send_message(
                    "You can edit your channel with this command. Set a value "
                    "for the name or the maximum user limit.",
                    ephemeral=True)
            if not limit and name:
                await channel.edit(
                    reason=f"Voice channel renamed from \"{channel.name}\" "
                           f"to \"{name}\"{limit_info}",
                    name=name
                )
                username = getattr(itx.user, 'nick', None) or itx.user.name
                await log_to_guild(
                    itx.client,
                    itx.guild,
                    f"Voice channel ({channel.id}) renamed from "
                    f"\"{old_name}\" to \"{name}\" (by "
                    f"{username}, {itx.user.id})"
                )
                await itx.response.send_message(
                    warning + f"Voice channel successfully renamed "
                              f"to \"{name}\"",
                    ephemeral=True,
                    allowed_mentions=discord.AllowedMentions.none()
                )
            if limit and not name:
                await channel.edit(
                    reason=f"Voice channel limit edited from \"{old_limit}\" "
                           f"to \"{limit}\"",
                    user_limit=limit
                )
                await log_to_guild(
                    itx.client,
                    itx.guild,
                    f"Voice channel \"{old_name}\" ({channel.id}) edited the "
                    f"user limit from \"{old_limit}\" to \"{limit}\" "
                    f"(by {itx.user.nick or itx.user.name}, {itx.user.id})"
                    f"{limit_info}"
                )
                await itx.response.send_message(
                    warning + f"Voice channel user limit for \"{old_name}\" "
                              f"successfully edited from \"{old_limit}\" to "
                              f"\"{limit}\"",
                    ephemeral=True,
                    allowed_mentions=discord.AllowedMentions.none()
                )
            if limit and name:
                await channel.edit(
                    reason=f"Voice channel edited from name: "
                           f"\"{channel.name}\" to \"{name}\" and user limit "
                           f"from \"{limit}\" to \"{old_limit}\"",
                    user_limit=limit,
                    name=name
                )
                username = getattr(itx.user, 'nick', None) or itx.user.name
                await log_to_guild(
                    itx.client,
                    itx.guild,
                    f"{username} ({itx.user.id}) "
                    f"changed VC ({channel.id}) name \"{old_name}\" to "
                    f"\"{name}\" and user limit from \"{old_limit}\" to "
                    f"\"{limit}\"{limit_info}"
                )
                await itx.response.send_message(
                    warning + "Voice channel name and user limit "
                              "successfully edited.",
                    ephemeral=True,
                    allowed_mentions=discord.AllowedMentions.none()
                )
        except discord.errors.HTTPException as ex:
            ex_message = repr(ex).split("(", 1)[1][1:-2]
            await log_to_guild(
                itx.client,
                itx.guild,
                f"Warning! >> {ex_message} << "
                f"{itx.user.nick or itx.user.name} ({itx.user.id}) "
                f"tried to change {old_name} ({channel.id}) to {name}, but "
                f"wasn't allowed to by discord, probably because it's in a "
                f"banned word list for discord's discovery "
                f"<@262913789375021056>"
            )

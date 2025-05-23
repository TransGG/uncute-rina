from typing import Callable

import discord
import discord.ext.commands as commands
import discord.app_commands as app_commands

from extensions.settings.objects import ModuleKeys, AttributeKeys
from resources.checks import (
    module_enabled_check,
    MissingAttributesCheckFailure,
)
from resources.views.generics import GenericTwoButtonView
from resources.checks.permissions import is_staff
# ^ to prevent people in vc-tables from muting staff.
from resources.utils.utils import log_to_guild
# ^ to log custom vc changes
from resources.customs import Bot

from extensions.customvcs.channel_rename_tracker import try_store_vc_rename
from extensions.customvcs.utils import (
    is_vc_custom,
    edit_permissionoverwrite,
)


# Owner       = Connection perms (and speaking perms)
# Speaker     = Speaking perms
# Muted       = No speaking perms (or stream(video) perms)
# Participant = Channel view perms (and message history perms)

# region Permission checks
def _is_vc_table_owner(
        channel: discord.VoiceChannel,
        target: discord.Role | discord.Member
) -> bool:
    if target not in channel.overwrites:
        return False
    return channel.overwrites[target].connect


def _is_vctable_speaker(
        channel: discord.VoiceChannel,
        target: discord.Role | discord.Member
) -> bool:
    if target not in channel.overwrites:
        return False
    return channel.overwrites[target].speak is True


def _is_vctable_muted(
        channel: discord.VoiceChannel,
        target: discord.Role | discord.Member
) -> bool:
    if target not in channel.overwrites:
        return False
    return channel.overwrites[target].speak is False


def _is_vctable_participant(
        channel: discord.VoiceChannel,
        target: discord.Role | discord.Member
) -> bool:
    if target not in channel.overwrites:
        return False
    return channel.overwrites[target].view_channel is True


def _is_vctable_authorized(
        channel: discord.VoiceChannel,
        guild: discord.Guild
) -> bool:
    if guild.default_role not in channel.overwrites:
        return False
    return channel.overwrites[guild.default_role].speak is False


def _is_vctable_locked(
        channel: discord.VoiceChannel,
        guild: discord.Guild
) -> bool:
    if guild.default_role not in channel.overwrites:
        return False
    return channel.overwrites[guild.default_role].view_channel is False

# endregion Permission checks


def _get_vctable_members_with_predicate(
        channel: discord.VoiceChannel,
        predicate: Callable[
            [discord.VoiceChannel, discord.Member | discord.Role
             | discord.Object], bool]
):
    outputs = []
    for target in channel.overwrites:
        if predicate(channel, target) and isinstance(target, discord.Member):
            outputs.append(target.mention)
    return outputs


async def _get_current_voice_channel(
        itx: discord.Interaction[Bot],
        action: str,
        from_event: bool = None
):
    """Gets the voice channel of the command executor if it's
    a custom voice channel.

    :param itx: The interaction from the original command.
    :param action: The action to note in the error message.
    :param from_event: Whether this event was executes from a
     non-command context.

    :return: The custom voice channel that the executor is in, or
     ``None`` if the user is not in a custom voice channel.
    :raise MissingAttributesCheckFailure: If any guild attributes
     are missing.
    """
    vc_hub: discord.VoiceChannel | None
    vc_category: discord.CategoryChannel | None
    blacklisted_channels: list[discord.VoiceChannel]
    vc_blacklist_prefix: str | None
    vc_hub, vc_category, blacklisted_channels, vc_blacklist_prefix = \
        itx.client.get_guild_attribute(
            itx.guild,
            AttributeKeys.custom_vc_create_channel,
            AttributeKeys.custom_vc_category,
            AttributeKeys.custom_vc_blacklisted_channels,
            AttributeKeys.custom_vc_blacklist_prefix
        )
    if None in (vc_hub, vc_category, vc_blacklist_prefix):
        missing = [key for key, value in {
            AttributeKeys.custom_vc_create_channel: vc_hub,
            AttributeKeys.custom_vc_category: vc_category,
            AttributeKeys.custom_vc_blacklist_prefix: vc_blacklist_prefix
        }.items()
            if value is None]
        raise MissingAttributesCheckFailure(ModuleKeys.vc_tables, missing)

    if itx.user.voice is None or itx.user.voice.channel is None:
        if not from_event:
            await itx.response.send_message(
                f"Couldn't {action}: You aren't connected to a voice channel!",
                ephemeral=True,
            )
        return
    channel = itx.user.voice.channel

    if not is_vc_custom(channel, vc_category, vc_hub,
                        blacklisted_channels, vc_blacklist_prefix):
        if not from_event:
            await itx.response.send_message(
                f"Couldn't {action}: This voice channel is not compatible "
                f"with VcTables!",
                ephemeral=True,
            )
        return

    return channel


async def _get_channel_if_owner(
        itx: discord.Interaction[Bot] | discord.Member,
        action: str,
        from_event: bool = False
):
    """
    Gets the voice channel of the command executor if they are in a
    custom voice channel that has turned into a vctable AND they are the
    owner of that table.

    :param itx: The interaction from the original command.
    :param action: The action to note in the error message.
    :param from_event: Whether this event executes from a non-command
     context. Default: False.

    :return: The vctable that the executor is in, or None if the user
     is not in a custom voice channel or is not owner of the vctable
     channel.
    :raise MissingAttributesCheckFailure: If any guild attributes are
     missing. (carried from :py:meth:`_is_vc_table_owner`)
    """
    channel = await _get_current_voice_channel(itx, action, from_event)
    if channel is None:
        return

    if not _is_vc_table_owner(channel, itx.user):
        if not from_event:
            cmd_create = itx.client.get_command_mention('vctable create')
            await itx.response.send_message(
                f"Invalid permissions: You are not an owner of this VcTable! "
                f"(Perhaps this isn't a VcTable yet: use {cmd_create} to "
                f"make it one!)",
                ephemeral=True,
            )
        return
    return channel


class VcTables(
        commands.GroupCog,
        name="vctable",
        description="Make your voice channels advanced!"
):
    def __init__(self):
        pass

    # region Commands
    # region Other commands
    @app_commands.command(name="create",
                          description="Turn your custom vc into a cool vc")
    @app_commands.describe(
        owners="A list of extra owners for your VcTable. Separate with comma",
        name="Give the channel a different name (api efficiency)"
    )
    @module_enabled_check(ModuleKeys.vc_tables)
    async def vctable_create(
            self,
            itx: discord.Interaction[Bot],
            owners: str = "",
            name: app_commands.Range[str, 3, 35] | None = None
    ):
        vctable_prefix: str | None = itx.client.get_guild_attribute(
            itx.guild, AttributeKeys.vctable_prefix)
        if vctable_prefix is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.vc_tables, [AttributeKeys.vctable_prefix])

        warning = ""

        owners = owners.split(",")
        if itx.user.guild is None:
            await itx.response.send_message(
                "You don't seem to be in this guild, so I can't give you "
                "permissions for this voice channel... Maybe ask @mysticmia "
                "about this?",
                ephemeral=True,
            )

        cmd_owner = itx.client.get_command_mention_with_args(
            "vctable owner", mode="Add", user=" ")
        # region Parse vctable owners
        added_owners = [itx.user]
        added_owner_ids = []
        for mention in owners:
            if mention == "":
                continue
            mention: str = mention.strip()
            if not (mention[0:2] == "<@" and mention[-1] == ">"):
                warning = (
                    f"Note: You didn't give a good list of VcTable owners, "
                    f"so I only added the ones prior. To make more people "
                    f"owner, use {cmd_owner}.\n"
                )
                break
            mention = mention[2:-1]
            for char in mention:
                if char not in "0123456789":
                    warning = (
                        f"Note: You didn't give a good list of VcTable "
                        f"owners, so I only added the ones prior. To make "
                        f"more people owner, use {cmd_owner}.\n"
                    )
                    break

            if not mention.isdecimal():
                warning = (
                    f"Note: You didn't give a good list of VcTable owners, "
                    f"so I only added the ones prior. To make more people "
                    f"owner, use {cmd_owner}.\n"
                )
                break
            mention_id = int(mention)
            added_owner_ids.append(mention_id)
        else:
            owner_list = [int(mention) for mention in added_owner_ids]
            for owner_id in owner_list:
                owner = itx.guild.get_member(owner_id)
                if owner is None:
                    warning = (
                        f"Note: The list of owners you provided contained an "
                        f"unknown server member ({owner_id}), so I only added "
                        f"the ones prior. To make more people owner, "
                        f"use {cmd_owner}."
                    )
                    break

                if owner not in added_owners:
                    added_owners.append(owner)
        # endregion Parse vctable owners

        # region Set warnings and manage odd cases
        user_vc = await _get_current_voice_channel(itx, "create VcTable")
        if user_vc is None:
            return

        if name == user_vc.name:
            warning += (
                "Info: VcTables get a prefix, so the channel name is edited "
                "to include it. Bots can only edit a channel's name twice "
                "every 10 minutes. If you wanted to also change the channel "
                "name, you would need to run /editvc again, adding to that "
                "2-rename limit. For efficiency, you can provide a name here "
                "to do both of the edits at once (prefix and rename).\n"
                "That means you don't have to give exactly the same name as "
                "the one the channel already had."
            )
        elif name is None:
            name = user_vc.name

        await itx.response.defer(ephemeral=True)
        # if owner present: already VcTable -> stop
        for target in user_vc.overwrites:
            if (_is_vc_table_owner(user_vc, target)
                    and target not in user_vc.category.overwrites):
                cmd_owner = itx.client.get_command_mention("vctable owner")
                await itx.followup.send(
                    f"This channel is already a VcTable! Use {cmd_owner} "
                    f"`mode:Check owners` to see who the owners of this "
                    f"table are!",
                    ephemeral=True)
                return

        first_rename_time = try_store_vc_rename(itx.user.voice.channel.id)
        if first_rename_time:
            await itx.followup.send(
                f"This channel has been renamed too often in the past "
                f"10 minutes! (bcuz discord :P)\n"
                f"You can turn this into a VcTable in "
                f"<t:{first_rename_time + 600}:R> "
                f"(<t:{first_rename_time + 600}:t>).",
                ephemeral=True,
            )
            return
        # endregion Set warnings and manage odd cases

        # region Apply permission overwrites for vctable owners
        new_overwrites = user_vc.overwrites
        for owner in added_owners:
            perms = discord.PermissionOverwrite()
            if owner in user_vc.overwrites:
                perms = user_vc.overwrites[owner]
            # elif owner in user_vc.category.overwrites:
            #     perms = user_vc.category.overwrites[owner]
            new_overwrites[owner] = edit_permissionoverwrite(perms, {
                "connect": True,
                "speak": True,
                "view_channel": True,
                "read_message_history": True,
            })
        # make sure the bot can still see the channel for vc events,
        #  even if /vctable lock.
        bot_overwrites = user_vc.overwrites.get(
            itx.guild.me, discord.PermissionOverwrite())
        new_overwrites[itx.guild.me] = edit_permissionoverwrite(
            bot_overwrites, {"view_channel": True})
        await user_vc.edit(overwrites=new_overwrites)

        # endregion Apply permission overwrites for vctable owners

        owner_taglist = ', '.join([f'<@{user_id}>'
                                   for user_id in added_owners])
        cmd_owner = itx.client.get_command_mention("vctable about")
        await user_vc.send(
            f"CustomVC converted to VcTable\n"
            f"Use {cmd_owner} to learn more!\n"
            f"Made {owner_taglist} a VcTable Owner\n"
            f"**:warning: If someone is breaking the rules, TELL A MOD** "
            f"(don't try to moderate a vc yourself)",
            allowed_mentions=discord.AllowedMentions.none()
        )
        await log_to_guild(
            itx.client,
            itx.guild,
            f"{itx.user.mention} ({itx.user.id}) turned a CustomVC "
            f"({user_vc.id}) into a VcTable"
        )

        try:
            await user_vc.edit(name=vctable_prefix + name)
            await itx.followup.send(
                "Successfully converted channel to VcTable and set you "
                "as owner.\n"
                + warning,
                ephemeral=True
            )
        except discord.errors.NotFound:
            await itx.followup.send(
                "I was unable to name your VcTable, but I managed to set "
                "the permissions for it.",
                ephemeral=True
            )

    @module_enabled_check(ModuleKeys.vc_tables)
    @app_commands.command(
        name="disband",
        description="reset permissions and convert vctable back to customvc"
    )
    async def vctable_disband(self, itx: discord.Interaction[Bot]):
        vctable_prefix: str | None = itx.client.get_guild_attribute(
            itx.guild, AttributeKeys.vctable_prefix)
        if vctable_prefix is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.vc_tables, [AttributeKeys.vctable_prefix])

        channel = await _get_channel_if_owner(itx, "disband VcTable")
        if channel is None:
            return
        # reset overrides
        await channel.edit(overwrites=channel.category.overwrites)
        # update every user's permissions
        for user in channel.members:
            await user.move_to(channel)
        await channel.send(
            f"{itx.user.mention} disbanded the VcTable and turned "
            f"it back to a normal CustomVC",
            allowed_mentions=discord.AllowedMentions.none()
        )
        # remove channel's name prefix (separately from the overwrites
        #  due to things like ratelimiting)
        await itx.response.send_message(
            "Successfully disbanded VcTable.",
            ephemeral=True
        )
        if channel.name.startswith(vctable_prefix):
            new_channel_name = channel.name[len(vctable_prefix):]
            try_store_vc_rename(channel.id, max_rename_limit=3)
            # same as on_voice_state_update:
            # allow max 3 renamed: if a staff queued a rename due to
            #  rules, it'd be queued at 3. It would be bad to have it
            #  be renamed back to the bad name right after.
            try:
                await channel.edit(name=new_channel_name)
            except discord.errors.NotFound:
                pass

    @app_commands.command(
        name="about",
        description="Get information about this CustomVC add-on feature"
    )
    @module_enabled_check(ModuleKeys.vc_tables)
    async def vctable_help(self, itx: discord.Interaction[Bot]):
        embed1 = discord.Embed(
            color=discord.Colour.from_rgb(r=255, g=153, b=204),
            title='Custom VC Tables',
            description="Tables are a system to help keep a focused voice "
                        "channel on-topic. For example, a watch party or a "
                        "group gaming session might welcome people joining to "
                        "participate but not want people to derail/disrupt "
                        "it. VcTables allow you to have a bit more control "
                        "over your vc by letting you mute disruptive people "
                        "or make speaking permissions whitelist-only"
        )

        cmd_about = itx.client.get_command_mention('vctable about')
        cmd_create = itx.client.get_command_mention_with_args(
            'vctable create', owners=" ")
        cmd_owner = itx.client.get_command_mention_with_args(
            'vctable owner', mode=" ", user=" ")
        cmd_mute = itx.client.get_command_mention_with_args(
            'vctable mute', mode=" ", user=" ")
        cmd_authorized = itx.client.get_command_mention(
            'vctable make_authorized_only')
        cmd_speaker = itx.client.get_command_mention_with_args(
            'vctable speaker', mode=" ", user=" ")
        cmd_lock = itx.client.get_command_mention('vctable lock')
        cmd_participant = itx.client.get_command_mention_with_args(
            'vctable participant', mode=" ", user=" ")

        embed2 = discord.Embed(
            color=discord.Colour.from_rgb(r=255, g=153, b=204),
            title='Command documentation and explanation',
            description=f"Words in brackets [like so] mean they are optional "
                        f"for the command.\n"
                        f"Most commands are for owners only, like muting, "
                        f"adding/removing permissions. Normal participants "
                        f"can check who's owner, speaker, or muted though.\n"
                        f"{cmd_about}: See this help page\n"
                        f"{cmd_create}: Turns your CustomVC into a VcTable "
                        f"and makes you (and any additional mentioned "
                        f"user(s)) the owner\n"
                        f"{cmd_owner}: Add/Remove an owner to your "
                        f"table. If you want to check the owners, then it "
                        f"doesn't matter what you fill in for 'user'\n"
                        f"{cmd_mute}: Mute/Unmute a user in your "
                        f"table. If you want to check the muted participants, "
                        f"see ^ (same as for checking owners)\n"
                        f"{cmd_authorized}: Toggle the whitelist for "
                        f"speaking\n"
                        f"{cmd_speaker}: Add/Remove a speaker to your "
                        f"table. This user gets whitelisted to speak when "
                        f"authorized-only is enabled. Checking speakers works "
                        f"the same as checking owners and muted users\n"
                        f"{cmd_lock}: Similar to make-authorized-only, but "
                        f"for viewing the voice channel and its message "
                        f"history.\n"
                        f"{cmd_participant}: Add/Remove a participant to your "
                        f"table. This user gets whitelisted to view the "
                        f"channel and message history when the 'lock' is "
                        f"activated.\n"
        )  # todo: move to use /help page instead
        await itx.response.send_message(
            embeds=[embed1, embed2],
            ephemeral=True
        )

    # endregion Other commands

    # region Edit user permissions
    @app_commands.command(name="owner",
                          description="Manage the owners of your VcTable")
    @app_commands.describe(
        user="Who to add/remove as a VcTable owner (ignore if 'Check')"
    )
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Add owner', value=1),
        discord.app_commands.Choice(name='Remove owner', value=2),
        discord.app_commands.Choice(name='Check owners', value=3)
    ])
    @module_enabled_check(ModuleKeys.vc_tables)
    async def edit_vctable_owners(
            self,
            itx: discord.Interaction[Bot],
            mode: int,
            user: discord.Member | None = None
    ):
        # todo: make mode use Enum
        if itx.user == user and mode != 3:
            if mode == 1:
                await itx.response.send_message(
                    "You can't set yourself as owner!",
                    ephemeral=True,
                )
            elif mode == 2:
                cmd_owner = itx.client.get_command_mention_with_args(
                    "vctable owner", user=" ")
                cmd_disband = itx.client.get_command_mention(
                    "vctable disband")
                await itx.response.send_message(
                    "You can't remove your ownership of this VcTable!\n"
                    f"You can make more people owner with {cmd_owner} "
                    f"though... If you want to delete the VcTable, you can "
                    f"use {cmd_disband}.",
                    ephemeral=True,
                )
            return

        if mode == 1:  # add
            warning = ""
            channel = await _get_channel_if_owner(itx, "add owner")
            if channel is None:
                return
            if user is None:
                await itx.response.send_message(
                    "You can add an owner to your VcTable using this command. "
                    "Owners have the ability to add speakers, mute, add other "
                    "owners, disband a vctable, or whitelist connecting and "
                    "speaking. Give this to people you believe can help you "
                    "with this.",
                    ephemeral=True,
                )
                return
            if _is_vc_table_owner(channel, user):
                await itx.response.send_message(
                    "This user is already an owner!",
                    ephemeral=True
                )
                return
            await channel.set_permissions(
                user,
                connect=True,
                speak=True,
                view_channel=True,
                read_message_history=True,
                reason="VcTable edited: set as owner (+speaker)",
            )
            await channel.send(
                f"{itx.user.mention} added {user.mention} as VcTable owner.",
                allowed_mentions=discord.AllowedMentions.none()
            )
            await itx.response.send_message(
                f"Successfully added {user.mention} as owner."
                + warning,
                ephemeral=True,
            )
            if user in channel.members:
                await user.move_to(channel)

        if mode == 2:  # remove
            channel = await _get_channel_if_owner(itx, "remove owner")
            if channel is None:
                return
            if user is None:
                cmd_owner = itx.client.get_command_mention("vctable owner")
                await itx.response.send_message(
                    f"Removing owners is usually a bad sign.. Do not hesitate "
                    f"to make a ticket for staff if there's something wrong.\n"
                    f"Anyway. You can check current owners with {cmd_owner} "
                    f"`mode:Check`. Then mention a user you want to delete in "
                    f"the `user: ` argument.",
                    ephemeral=True,
                )
                return
            if not _is_vc_table_owner(channel, user):
                await itx.response.send_message(
                    "This user wasn't an owner yet.. Try taking someone "
                    "else's ownership away.",
                    ephemeral=True
                )
                return
            await channel.set_permissions(
                user,
                connect=None,
                reason="VcTable edited: removed as owner"
            )
            await channel.send(
                f"{itx.user.mention} removed {user.mention} as VcTable owner",
                allowed_mentions=discord.AllowedMentions.none()
            )
            await itx.response.send_message(
                f"Successfully removed {user.mention} as owner. Keep in mind "
                f"they are still a `speaker` and a `participant`.",
                ephemeral=True
            )

        if mode == 3:  # check
            channel = await _get_current_voice_channel(itx, "check owners")
            if channel is None:
                return
            owners = _get_vctable_members_with_predicate(
                channel, _is_vc_table_owner)
            await itx.response.send_message(
                "Here is a list of this VcTable's owners:\n  "
                + ', '.join(owners),
                ephemeral=True
            )

    @app_commands.command(
        name="speaker",
        description="Allow users to talk (when authorized_speakers_only is on)"
    )
    @app_commands.describe(
        user="Who to add/remove as a VcTable speaker (ignore if 'Check')"
    )
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Add speaker', value=1),
        discord.app_commands.Choice(name='Remove speaker', value=2),
        discord.app_commands.Choice(name='Check speakers', value=3)
    ])
    @module_enabled_check(ModuleKeys.vc_tables)
    async def edit_vctable_speakers(
            self,
            itx: discord.Interaction[Bot],
            mode: int,
            user: discord.Member | None = None
    ):
        if itx.user == user and mode != 3:
            await itx.response.send_message(
                "You can't edit your own speaking permissions!",
                ephemeral=True
            )
            return

        if mode == 1:  # add
            channel = await _get_channel_if_owner(itx, "add speaker")
            if channel is None:
                return
            if user is None:
                cmd_owner = itx.client.get_command_mention(
                    "vctable make_authorized_only")
                await itx.response.send_message(
                    f"You can add a speaker to your VcTable using this "
                    f"command. Using {cmd_owner}, you can let only those "
                    f"you've selected be able to talk in your voice channel. "
                    f"This can be useful if you want an on-topic convo or "
                    f"podcast with a select group of people :)",
                    ephemeral=True,
                )
                return
            warning = (
                "\nThis user was muted before. Making them a speaker removed "
                "their mute." if _is_vctable_muted(channel, user)
                else ""
            )
            if _is_vctable_speaker(channel, user):
                await itx.response.send_message(
                    "This user is already a speaker!",
                    ephemeral=True,
                )
                return
            if not _is_vctable_authorized(channel, itx.guild):
                cmd_owner = itx.client.get_command_mention(
                    "vctable make_authorized_only")
                warning += (f"\nThis has no purpose until you enable "
                            f"'authorized-only' using {cmd_owner}.")
            await channel.set_permissions(
                user,
                speak=True,
                reason="VcTable edited: set as speaker",
            )
            await channel.send(
                f"{itx.user.mention} made {user.mention} a speaker.",
                allowed_mentions=discord.AllowedMentions.none()
            )
            await itx.response.send_message(
                f"Successfully made {user.mention} a speaker."
                + warning,
                ephemeral=True,
            )
            if user in channel.members:
                await user.move_to(channel)

        if mode == 2:  # remove
            channel = await _get_channel_if_owner(itx, "remove speaker")
            if channel is None:
                return
            if user is None:
                cmd_owner = itx.client.get_command_mention_with_args(
                    "vctable owner", mode="Remove owner")
                cmd_speaker = itx.client.get_command_mention_with_args(
                    "vctable speaker", mode="Check")
                await itx.response.send_message(
                    f"You can remove speakers with this command. This only "
                    f"works if the user you're trying to remove is not "
                    f"already a VcTable owner (you'll need to use "
                    f"{cmd_owner} first).\n"
                    f"To see current VcTable speakers, use {cmd_speaker}.",
                    ephemeral=True,
                )
                return
            if _is_vc_table_owner(channel, user):
                await itx.response.send_message(
                    "This user is an owner of this VcTable! If you want to "
                    "reset their speaking permissions, un-owner them first!",
                    ephemeral=True,
                )
                return
            if not _is_vctable_speaker(channel, user):
                await itx.response.send_message(
                    "This user is not a speaker! You can't unspeech a "
                    "non-speaker!",
                    ephemeral=True,
                )
                return
            warning = ""
            if not _is_vctable_authorized(channel, itx.guild):
                cmd_owner = itx.client.get_command_mention(
                    "vctable make_authorized_only")
                warning = (f"\nThis has no purpose until you enable "
                           f"'authorized-only' using {cmd_owner}.")
            await channel.set_permissions(
                user,
                speak=None,
                reason="VcTable edited: removed as speaker",
            )
            await channel.send(
                f"{itx.user.mention} removed {user.mention} as speaker.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            await itx.response.send_message(
                f"Successfully removed {user.mention} as speaker."
                + warning,
                ephemeral=True
            )
            if user in channel.members:
                await user.move_to(channel)

        if mode == 3:  # check
            channel = await _get_current_voice_channel(itx, "check speakers")
            if channel is None:
                return
            speakers = _get_vctable_members_with_predicate(
                channel, _is_vctable_speaker)
            await itx.response.send_message(
                "Here is a list of this VcTable's speakers:\n  "
                + ', '.join(speakers),
                ephemeral=True,
            )

    @app_commands.command(
        name="participant",
        description="Allow users to see channel (if '/vctable lock' "
                    "is enabled)"
    )
    @app_commands.describe(
        user="Who to add/remove as a VcTable participant (ignore if 'Check')"
    )
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Add participant', value=1),
        discord.app_commands.Choice(name='Remove participant', value=2),
        discord.app_commands.Choice(name='Check participants', value=3)
    ])
    @module_enabled_check(ModuleKeys.vc_tables)
    async def edit_vctable_participants(
            self,
            itx: discord.Interaction[Bot],
            mode: int,
            user: discord.Member | None = None
    ):
        if itx.user == user and mode != 3:
            await itx.response.send_message(
                "You can't edit your own participation permissions!",
                ephemeral=True
            )
            return

        if mode == 1:  # add
            channel = await _get_channel_if_owner(itx, "add participant")
            if channel is None:
                return
            if user is None:
                cmd_owner = itx.client.get_command_mention("vctable lock")
                await itx.response.send_message(
                    f"You can add a participant to your VcTable using this "
                    f"command. Using {cmd_owner}, you can let only those "
                    f"you've selected be able to see your voice channel and "
                    f"read its messages. This can be useful if you want an "
                    f"on-topic convo or private meeting with a select group "
                    f"of people :)\n"
                    f"Note: Staff can still view and join your voice channel.",
                    ephemeral=True
                )
                return
            if _is_vctable_participant(channel, user):
                await itx.response.send_message(
                    "This user is already a participant!",
                    ephemeral=True
                )
                return
            warning = ""
            if not _is_vctable_locked(channel, itx.guild):
                cmd_owner = itx.client.get_command_mention("vctable lock")
                warning += (f"\nThis has no purpose until you activate the "
                            f"'lock' using {cmd_owner}.")
            await channel.set_permissions(
                user,
                view_channel=True,
                read_message_history=True,
                reason="VcTable edited: set as participant",
            )
            await channel.send(
                f"{itx.user.mention} made {user.mention} a participant.",
                allowed_mentions=discord.AllowedMentions.none()
            )
            await itx.response.send_message(
                f"Successfully made {user.mention} a participant."
                + warning,
                ephemeral=True
            )

        if mode == 2:  # remove
            channel = await _get_channel_if_owner(itx, "remove participant")
            if channel is None:
                return
            if user is None:
                cmd_owner = itx.client.get_command_mention_with_args(
                    "vctable owner", mode="Remove owner")
                cmd_participant = itx.client.get_command_mention_with_args(
                    "vctable participant", mode="Check")
                await itx.response.send_message(
                    f"You can remove participants with this command. This "
                    f"only works if the user you're trying to remove is not "
                    f"already a VcTable owner (you'll need to use {cmd_owner} "
                    f"first).\n"
                    f"To see current VcTable participants, use "
                    f"{cmd_participant}.",
                    ephemeral=True,
                )
                return
            if not _is_vctable_participant(channel, user):
                await itx.response.send_message(
                    "This user is not a participant! You can't remove the "
                    "participation permissions they don't have!",
                    ephemeral=True,
                )
                return
            if _is_vc_table_owner(channel, user):
                await itx.response.send_message(
                    "This user is an owner of this VcTable! If you want to "
                    "reset their participation permissions, un-owner them "
                    "first!",
                    ephemeral=True,
                )
                return
            if itx.client.is_me(user):
                await itx.response.send_message(
                    ":warning: You are trying to hide this channel from the "
                    "bot that manages this system!\n"
                    "Your command has been interrupted. Removing this user's "
                    "viewing permissions would make it unable to edit the "
                    "voice channel or respond to voice channel events "
                    "(join/leave).",
                    ephemeral=True,
                )
                return
            warning = ""
            if _is_vctable_locked(channel, itx.guild):
                cmd_owner = itx.client.get_command_mention("vctable lock")
                warning = (f"\nThis has no purpose until you activate the "
                           f"'lock' using {cmd_owner}.")
            await channel.set_permissions(
                user,
                view_channel=None,
                read_message_history=None,
                reason="VcTable edited: removed as participant",
            )
            await channel.send(
                f"{itx.user.mention} removed {user.mention} as participant.",
                allowed_mentions=discord.AllowedMentions.none()
            )
            await itx.response.send_message(
                f"Successfully removed {user.mention} as participant."
                + warning,
                ephemeral=True
            )
            if user in channel.members:
                await user.move_to(channel)

        if mode == 3:  # check
            channel = await _get_current_voice_channel(itx, "check speakers")
            if channel is None:
                return
            participants = _get_vctable_members_with_predicate(
                channel, _is_vctable_participant)
            await itx.response.send_message(
                "Here is a list of this VcTable's participants:\n  "
                + ', '.join(participants),
                ephemeral=True,
            )

    @app_commands.command(name="mute",
                          description="Deny users to talk in your VcTable")
    @app_commands.describe(user="Who to mute/unmute (ignore if 'Check')")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Mute participant', value=1),
        discord.app_commands.Choice(name='Unmute participant', value=2),
        discord.app_commands.Choice(name='Check muted participants', value=3)
    ])
    @module_enabled_check(ModuleKeys.vc_tables)
    async def edit_vctable_muted_participants(
            self,
            itx: discord.Interaction[Bot],
            mode: int,
            user: discord.Member | None = None
    ):
        if itx.user == user and mode != 3:
            await itx.response.send_message(
                "You can't "
                + "un" * (mode == 2)
                + "mute yourself!",
                ephemeral=True,
            )
            return

        if mode == 1:  # mute
            channel = await _get_channel_if_owner(itx, "mute participant")
            if channel is None:
                return
            if user is None:
                await itx.response.send_message(
                    "Muting someone is usually a bad sign... Don't hesitate "
                    "to open a ticket with staff if there's something going "
                    "on.\n"
                    "Anyway. Mention a user in the `user: ` argument to mute "
                    "that person.",
                    ephemeral=True,
                )
                return
            warning = (
                "\nThis user was a speaker before. Muting them "
                "overwrote this permissions and removed their speaker "
                "permissions" if _is_vctable_speaker(channel, user)
                else ""
            )
            if _is_vctable_muted(channel, user):
                await itx.response.send_message(
                    "This user is already muted!",
                    ephemeral=True
                )
                return
            if _is_vc_table_owner(channel, user):
                await itx.response.send_message(
                    "This user is an owner of this VcTable! If you want to "
                    "mute them, un-owner them first!",
                    ephemeral=True)
                return

            if is_staff(itx, user):
                await itx.response.send_message(
                    "You can't mute staff members! If you have an issue "
                    "with staff, make a ticket or DM an admin!",
                    ephemeral=True)
                return
            await channel.set_permissions(
                user,
                speak=False,
                stream=False,
                reason="VcTable edited: muted participant"
            )
            await channel.send(
                f"{itx.user.mention} muted {user.mention}.",
                allowed_mentions=discord.AllowedMentions.none()
            )
            await itx.response.send_message(
                f"Successfully muted {user.mention}."
                + warning,
                ephemeral=True
            )
            if user in channel.members:
                await user.move_to(channel)

        if mode == 2:  # unmute
            channel = await _get_channel_if_owner(itx, "unmute user")
            if channel is None:
                return
            if user is None:
                cmd_check = itx.client.get_command_mention_with_args(
                    "vctable mute", mode="Check")
                cmd_mute = itx.client.get_command_mention_with_args(
                    "vctable mute", mode="Mute", user=" ")
                await itx.response.send_message(
                    f"This command lets you unmute a previously-muted person. "
                    f"To see which people are muted, use {cmd_check}\n"
                    f"Then, use {cmd_mute}\n",
                    ephemeral=True,
                )
                return
            if not _is_vctable_muted(channel, user):
                await itx.response.send_message(
                    "This user is already unmuted! Let people be silent "
                    "if they wanna be >:(",
                    ephemeral=True
                )
                return
            await channel.set_permissions(
                user,
                speak=None,
                stream=None,
                reason="VcTable edited: unmuted participant",
            )
            await channel.send(
                f"{itx.user.mention} unmuted {user.mention}.",
                allowed_mentions=discord.AllowedMentions.none()
            )
            await itx.response.send_message(
                f"Successfully unmuted {user.mention}.",
                ephemeral=True,
            )
            if user in channel.members:
                await user.move_to(channel)

        if mode == 3:  # check
            channel = await _get_current_voice_channel(
                itx, "check muted users")
            if channel is None:
                return
            muted = _get_vctable_members_with_predicate(
                channel, _is_vctable_muted)
            await itx.response.send_message(
                "Here is a list of this VcTable's muted users:\n  "
                + ', '.join(muted),
                ephemeral=True,
            )

    # endregion Edit user permissions

    # region Edit default role permissions
    @app_commands.command(name="make_authorized_only",
                          description="Only let users speak if they are "
                                      "whitelisted by the owner")
    @module_enabled_check(ModuleKeys.vc_tables)
    async def vctable_authorized_only(self, itx: discord.Interaction[Bot]):
        channel = await _get_channel_if_owner(itx, "enable authorized-only")
        if channel is None:
            return

        if _is_vctable_authorized(channel, itx.guild):
            await channel.set_permissions(
                itx.guild.default_role,
                speak=None,
                reason="VcTable edited: disaled authorized-only for speaking",
            )
            await channel.send(
                f"{itx.user.mention} disabled whitelist for speaking.",
                allowed_mentions=discord.AllowedMentions.none(),
            )
            await itx.response.send_message(
                "Successfully disabled speaking whitelist.",
                ephemeral=True,
            )
            return

        # if authorized-only is disabled:
        view = GenericTwoButtonView(
            ("Confirm", discord.ButtonStyle.green),
            ("Cancel", discord.ButtonStyle.red)
        )
        cmd_speaker = itx.client.get_command_mention_with_args(
            "vctable speaker", mode="Add", user=" ")
        await itx.response.send_message(
            f"Enabling authorized-only (a whitelist) will make only owners "
            f"and speakers (people that have been whitelisted) able to talk.\n"
            f"Please make sure everyone is aware of this change. To whitelist "
            f"someone, use {cmd_speaker}.",
            ephemeral=True,
            view=view,
        )
        await view.wait()
        if view.value:
            await channel.set_permissions(
                itx.guild.default_role,
                speak=False,
                reason="VcTable edited: enabled authorized-only for speaking",
            )
            await channel.send(
                f"{itx.user.mention} enabled whitelist for speaking.",
                allowed_mentions=discord.AllowedMentions.none()
            )
            for member in channel.members:
                # member has no owner or speaking perms, move to same vc?
                if member in channel.overwrites:
                    if (_is_vc_table_owner(channel, member)
                            or _is_vctable_speaker(channel, member)):
                        # todo: rename vctable/vc_table to be consistent
                        continue
                await member.move_to(channel)
            cmd_speaker = itx.client.get_command_mention("vctable speaker")
            await itx.edit_original_response(
                content=f"Successfully enabled whitelist. Use {cmd_speaker} "
                        f"`user: ` to let more people speak.",
                view=None)
        else:
            await itx.edit_original_response(
                content="Cancelling...", view=None)

    @app_commands.command(
        name="lock",
        description="Only let users view vc if they are whitelisted by "
                    "the owner"
    )
    @module_enabled_check(ModuleKeys.vc_tables)
    async def vctable_lock(self, itx: discord.Interaction[Bot]):
        channel = await _get_channel_if_owner(itx, "enable vctable lock")
        if channel is None:
            return

        # if lock is enabled -> (the role overwrite is not nonexistant
        #  and is False):
        if _is_vctable_locked(channel, itx.guild):
            await channel.set_permissions(
                itx.guild.default_role,
                view_channel=None,
                read_message_history=None,
                reason="VcTable edited: disabled viewing lock"
            )
            await channel.send(
                f"{itx.user.mention} disabled whitelist for viewing "
                f"this channel.",
                allowed_mentions=discord.AllowedMentions.none()
            )
            await itx.response.send_message(
                "Successfully disabled viewing whitelist.",
                ephemeral=True
            )
            return

        # if lock is disabled:
        view = GenericTwoButtonView(
            ("Confirm", discord.ButtonStyle.green),
            ("Cancel", discord.ButtonStyle.red)
        )
        cmd_participant = itx.client.get_command_mention_with_args(
            "vctable participant", mode="Add", user=" ")
        await itx.response.send_message(
            f"Enabling the lock (a whitelist) will make only owners and "
            f"participants (people that have been whitelisted) able to see "
            f"this server and message history.\n"
            f"Please make sure everyone is aware of this change. "
            f"To whitelist someone, use {cmd_participant}.",
            ephemeral=True,
            view=view,
        )
        await view.wait()
        if view.value:
            await channel.set_permissions(
                itx.guild.default_role,
                view_channel=False,
                read_message_history=False,
                reason="VcTable edited: enabled viewing lock"
            )
            await channel.send(
                f"{itx.user.mention} enabled whitelist for "
                f"viewing the voice channel.",
                allowed_mentions=discord.AllowedMentions.none()
            )
            cmd_participant = itx.client.get_command_mention_with_args(
                "vctable participant", user=" ")
            await itx.edit_original_response(
                content=f"Successfully enabled whitelist. Use "
                        f"{cmd_participant} to let more people speak.",
                view=None,
            )
        else:
            await itx.edit_original_response(
                content="Cancelling...", view=None)

    # endregion Edit default role permissions
    # endregion Commands

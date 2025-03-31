import discord

from resources.customs.bot import Bot
from resources.utils.utils import log_to_guild

from extensions.customvcs.channel_rename_tracker import try_store_vc_rename


class CustomVcStaffEditorModal(discord.ui.Modal, title='Edit a custom vc\'s channel'):
    def __init__(self, client: Bot, vc_hub: int, vc_log, vc_category):
        super().__init__()
        self.vcHub = vc_hub
        self.vcLog = vc_log
        self.vcCategory = vc_category

        self.channel_id = discord.ui.TextInput(label='Channel Id', placeholder="Which channel do you want to edit",
                                               required=True)
        self.name = discord.ui.TextInput(label='Name', placeholder="Give your voice channel a name", required=False,
                                         max_length=100 - len(client.custom_ids["vctable_prefix"]))
        self.limit = discord.ui.TextInput(label='Limit', placeholder="Give your voice channel a user limit",
                                          required=False)
        self.add_item(self.channel_id)
        self.add_item(self.name)
        self.add_item(self.limit)

    async def on_submit(self, itx: discord.Interaction):
        name = str(self.name)
        if name == "":
            name = None

        try:
            # limit = self.limit
            channel_id = int(str(self.channel_id))
        except ValueError:
            await itx.response.send_message(
                "Your channel id has to be .. number-able. It contains a non-integer character. In other words, "
                "there's something other than a number in your Channel Id box",
                ephemeral=True)
            return

        try:
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
                await itx.response.send_message("This isn't a voice channel. You can't edit this channel.",
                                                ephemeral=True)
                return
        except discord.errors.HTTPException:
            await itx.response.send_message("Retrieving this channel failed. Perhaps a connection issue?",
                                            ephemeral=True)
            return
        except Exception:
            await itx.response.send_message(
                "Sorry, I couldn't find that channel. Are you sure you have the correct **voice** channel id?",
                ephemeral=True)
            raise

        warning = ""
        if getattr(channel.category, "id") not in [self.vcCategory] or channel.id == self.vcHub:
            await itx.response.send_message(
                "You can't change that voice channel's name (not with this command, at least)!", ephemeral=True)
            return

        first_rename_time = try_store_vc_rename(channel.id, max_rename_limit=4)
        if first_rename_time:
            await itx.response.send_message(
                f"You can't edit channels more than twice in 10 minutes. Discord API would queue the edit instead.\n"
                f"I have queued the previous two renaming edits. You can queue another rename "
                f"<t:{first_rename_time + 600}:R> (<t:{first_rename_time + 600}:t>).",
                ephemeral=True)
            return

        limit_info = ""
        old_name = channel.name
        old_limit = channel.user_limit
        if old_name.startswith('〙') != name.startswith('〙'):
            warning += ("You're renaming a vc channel with a '〙' symbol. This symbol is used to blacklist "
                        "voice channels from being automatically removed when the last user leaves. If you "
                        "want a channel to stay (and not be deleted) when no-one is in it, you should start "
                        "the channel with the symbol.\n")
        try:
            if not limit and not name:
                await itx.response.send_message(
                    "You can edit a channel with this command. Set a value for the name or the maximum user limit.",
                    ephemeral=True)
            if limit and not name:
                await channel.edit(reason=f"Staff: Voice channel limit edited from \"{old_limit}\" to \"{limit}\"",
                                   user_limit=limit)
                await log_to_guild(itx.client, itx.guild,
                                   f"Staff: Voice channel \"{old_name}\" ({channel.id}) edited the user limit from "
                                   f"\"{old_limit}\" to \"{limit}\""
                                   f" (by {itx.user.nick or itx.user.name}, {itx.user.id}){limit_info}")
                await itx.response.send_message(
                    warning + f"Staff: Voice channel user limit for \"{old_name}\" successfully edited from "
                              f"\"{old_limit}\" to \"{limit}\"",
                    ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
            if not limit and name:
                await channel.edit(
                    reason=f"Staff: Voice channel renamed from \"{channel.name}\" to \"{name}\"{limit_info}", name=name)
                await log_to_guild(itx.client, itx.guild,
                                   f"Staff: Voice channel ({channel.id}) renamed from "
                                   f"\"{old_name}\" to \"{name}\""
                                   f" (by {itx.user.nick or itx.user.name}, {itx.user.id})")
                await itx.response.send_message(warning + f"Staff: Voice channel successfully renamed to \"{name}\"",
                                                ephemeral=True)  # allowed_mentions=discord.AllowedMentions.none())
            if limit and name:
                await channel.edit(
                    reason=f"Staff: Voice channel edited from name: \"{channel.name}\" to \"{name}\" "
                           f"and user limit from: \"{limit}\" to \"{old_limit}\"",
                    user_limit=limit, name=name)
                await log_to_guild(itx.client, itx.guild,
                                   f"Staff: {itx.user.nick or itx.user.name} ({itx.user.id}) changed "
                                   f"VC ({channel.id}) name \"{old_name}\" to \"{name}\" and user limit "
                                   f"from \"{old_limit}\" to \"{limit}\"{limit_info}")
                await itx.response.send_message(
                    warning + "Staff: Voice channel name and user limit successfully edited.", ephemeral=True,
                    allowed_mentions=discord.AllowedMentions.none())
        except discord.errors.HTTPException as ex:
            ex_message = repr(ex).split("(", 1)[1][1:-2]
            await log_to_guild(itx.client, itx.guild,
                               f"Staff: Warning! >> {ex_message} << {itx.user.nick or itx.user.name} ({itx.user.id}) "
                               f"tried to change {old_name} ({channel.id}) to {name}, but wasn't allowed to by "
                               f"discord, probably because it's in a banned word list for discord's discovery "
                               f"<@262913789375021056>")

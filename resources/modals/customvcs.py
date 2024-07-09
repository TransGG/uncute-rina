import discord
from time import mktime
from datetime import datetime
from resources.utils.utils import log_to_guild

recently_renamed_vcs = {} # make your own vcs!

class CustomVcStaffEditorModal(discord.ui.Modal, title='Edit a custom vc\'s channel'):
    channel_id = discord.ui.TextInput(label='Channel Id', placeholder="Which channel do you want to edit")#, required=True)
    name = discord.ui.TextInput(label='Name', placeholder="Give your voice channel a name", required=False)
    limit = discord.ui.TextInput(label='Limit', placeholder="Give your voice channel a user limit", required=False)

    def __init__(self, vcHub, vcLog, vcCategory):
        self.vcHub = vcHub
        self.vcLog = vcLog
        self.vcCategory = vcCategory

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
        if channel.category.id not in [self.vcCategory] or channel.id == self.vcHub:
            await itx.response.send_message("You can't change that voice channel's name (not with this command, at least)!",ephemeral=True)
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
        old_name = channel.name
        old_limit = channel.user_limit
        try:
            if limit is None:
                if name is None:
                    await itx.response.send_message("You can edit a channel with this command. Set a value for the name or the maximum user limit.", ephemeral=True)
                else:
                    await channel.edit(reason=f"Staff: Voice channel renamed from \"{channel.name}\" to \"{name}\"{limit_info}", name=name)
                    await log_to_guild(self.client, itx.guild, f"Staff: Voice channel ({channel.id}) renamed from \"{old_name}\" to \"{name}\" (by {itx.user.nick or itx.user.name}, {itx.user.id})")
                    await itx.response.send_message(warning+f"Staff: Voice channel successfully renamed to \"{name}\"", ephemeral=True)#allowed_mentions=discord.AllowedMentions.none())
                recently_renamed_vcs[channel.id].append(int(mktime(datetime.now().timetuple())))
            else:
                if name is None:
                    await channel.edit(reason=f"Staff: Voice channel limit edited from \"{old_limit}\" to \"{limit}\"", user_limit=limit)
                    await log_to_guild(self.client, itx.guild, f"Staff: Voice channel \"{old_name}\" ({channel.id}) edited the user limit from  \"{old_limit}\" to \"{limit}\" (by {itx.user.nick or itx.user.name}, {itx.user.id}){limit_info}")
                    await itx.response.send_message(warning+f"Staff: Voice channel user limit for \"{old_name}\" successfully edited from \"{old_limit}\" to \"{limit}\"", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                else:
                    await channel.edit(reason=f"Staff: Voice channel edited from name: \"{channel.name}\" to \"{name}\" and user limit from: \"{limit}\" to \"{old_limit}\"", user_limit=limit,name=name)
                    await log_to_guild(self.client, itx.guild, f"Staff: {itx.user.nick or itx.user.name} ({itx.user.id}) changed VC ({channel.id}) name \"{old_name}\" to \"{name}\" and user limit from \"{old_limit}\" to \"{limit}\"{limit_info}")
                    await itx.response.send_message(warning+f"Staff: Voice channel name and user limit successfully edited.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
                    recently_renamed_vcs[channel.id].append(int(mktime(datetime.now().timetuple())))
        except discord.errors.HTTPException as ex:
            ex_message = repr(ex).split("(", 1)[1][1:-2]
            await log_to_guild(self.client, itx.guild, f"Staff: Warning! >> "+ex_message+f" << {itx.user.nick or itx.user.name} ({itx.user.id}) tried to change {old_name} ({channel.id}) to {name}, but wasn't allowed to by discord, probably because it's in a banned word list for discord's discovery <@262913789375021056>")

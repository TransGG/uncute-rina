from datetime import datetime  # to make report tag auto-trigger at most once every 15 minutes

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.settings.objects import AttributeKeys, ModuleKeys
from resources.checks import module_enabled_check, not_in_dms_check
from resources.customs import Bot
# ^ to specify which tags can be used in which servers (e.g. Mature role not in EnbyPlace)
from resources.utils.utils import get_mod_ticket_channel  # for ticket channel id in Report tag

from extensions.tags.tags import Tags, tag_info_dict

# to prevent excessive spamming when multiple people mention staff. A sorta cooldown
report_message_reminder_unix = 0  # int(datetime.now().timestamp())


async def _tag_autocomplete(itx: discord.Interaction, current: str):
    if current == "":
        return [app_commands.Choice(name="Show list of tags", value="help")]

    # only show tags that are enabled in the server
    options = [i.lower() for i in tag_info_dict if itx.guild_id in tag_info_dict[i][2]]
    return [
               app_commands.Choice(name=term, value=term)
               for term in options if current.lower() in term
           ][:15]


async def _role_autocomplete(itx: discord.Interaction, current: str):
    role_options = {
        1126160553145020460: ("Hide Politics channel role", "NPA"),  # NPA
        1126160612620243044: ("Hide Venting channel role", "NVA")  # NVA
    }
    options = []
    for role in itx.user.roles:
        if role.id in role_options:
            if (current.lower() in role_options[role.id][0].lower() or
                    current.lower() in role_options[role.id][1].lower()):
                options.append(role.id)
    if options:
        return [
                   app_commands.Choice(name=role_options[role_id][0], value=role_options[role_id][1])
                   for role_id in options
               ][:15]
    else:
        return [app_commands.Choice(name="You don't have any roles to remove!", value="none")]


class TagFunctions(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        global report_message_reminder_unix
        if message.guild is None or message.author.bot:
            return

        staff_role_list, admin_role_list = self.client.get_guild_attribute(
            message.guild, AttributeKeys.staff_roles, AttributeKeys.admin_roles, default=[])
        staff_roles = set(staff_role_list + admin_role_list)
        staff_role_mentions = [f"<@&{role.id}>" for role in staff_roles if staff_roles is not None]

        for staff_role_mention in staff_role_mentions:
            if staff_role_mention in message.content:
                time_now = int(datetime.now().timestamp())  # get time in unix
                if time_now - report_message_reminder_unix > 900:  # 15 minutes
                    await Tags().send_report_info("report", message.channel, self.client,
                                                  additional_info=[message.author.name, message.author.id])
                    report_message_reminder_unix = time_now
                    break

    @app_commands.command(name="tag", description="Look up something through a tag")
    @app_commands.describe(tag="What tag do you want more information about?")
    @app_commands.describe(public="Show everyone in chat? (default: yes)")
    @app_commands.describe(anonymous="Hide your name when sending the message publicly? (default: yes)")
    @app_commands.autocomplete(tag=_tag_autocomplete)
    @module_enabled_check(ModuleKeys.tags)
    async def tag(self, itx: discord.Interaction, tag: str, public: bool = True, anonymous: bool = True):
        options = [i for i in tag_info_dict if itx.guild_id in tag_info_dict[i][2]]
        tag = tag.lower()
        if tag in options:
            await tag_info_dict[tag][1](tag, itx, public=public, anonymous=anonymous)
        elif tag in tag_info_dict:
            ticket_channel = get_mod_ticket_channel(itx.client, itx)
            if ticket_channel:
                ticket_string = f"make a staff ticket (<#{ticket_channel.id}>)."
            else:
                ticket_string = "please tell staff to double-check."
            await itx.response.send_message(
                "This tag is not enabled in this server! If you think this is a mistake, " + ticket_string,
                ephemeral=True)
        elif tag == "help":
            await itx.response.send_message("List of tags currently available to send:\n" +
                                            '\n'.join(["- " + i for i in tag_info_dict]), ephemeral=True)
        else:
            await itx.response.send_message("No tag found with this name!", ephemeral=True)

    @app_commands.command(name="remove-role", description="Remove one of your agreement roles")
    @app_commands.describe(role_name="The name of the role to remove")
    @app_commands.autocomplete(role_name=_role_autocomplete)
    @app_commands.check(not_in_dms_check)
    async def remove_role(self, itx: discord.Interaction, role_name: str):
        # todo: move this function out of this cog, since it's not a tag command; more a staff-like command.
        itx.user: discord.Member  # noqa  # it shouldn't be a discord.User cause the app_command check prevents DMs.

        role_options = {
            "npa": ["NPA", 1126160553145020460],
            "nva": ["NVA", 1126160612620243044],
        }
        if role_name.lower() not in role_options:
            await itx.response.send_message("You can't remove that role!", ephemeral=True)
            return

        role_id = role_options[role_name.lower()][1]
        try:
            for role in itx.user.roles:
                if role.id == role_id:
                    await itx.user.remove_roles(role, reason="Removed by user using /remove-role")
                    await itx.response.send_message("Successfully removed role!", ephemeral=True)
                    return
        except discord.Forbidden:
            await itx.response.send_message("I couldn't remove this role! (Forbidden)", ephemeral=True)
            return

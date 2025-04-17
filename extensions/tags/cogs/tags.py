from datetime import datetime  # to make report tag auto-trigger at most once every 15 minutes

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.help.cogs import send_help_menu
from extensions.settings.objects import AttributeKeys, ModuleKeys
from extensions.tags.local_tag_list import create_tag, remove_tag, get_tags
from extensions.tags.tag_manage_modes import TagMode
from resources.checks import module_enabled_check, not_in_dms_check, is_admin_check
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
    return [app_commands.Choice(name=term, value=term)
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
        return [app_commands.Choice(name=role_options[role_id][0], value=role_options[role_id][1])
                for role_id in options
                ][:15]
    else:
        return [app_commands.Choice(name="You don't have any roles to remove!", value="none")]


async def _tag_name_autocomplete(itx: discord.Interaction[Bot], current: str):
    if itx.namespace.mode == TagMode.delete.value:
        tag_objects = get_tags(itx.guild)
        return [
            app_commands.Choice(name=key, value=key)
            for key in tag_objects.keys()
            if current in key
        ]
    return []


class TagFunctions(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        global report_message_reminder_unix
        if message.guild is None or message.author.bot:
            return

        staff_role_list: list[discord.Role]
        admin_role_list: list[discord.Role]
        staff_role_list, admin_role_list = self.client.get_guild_attribute(
            message.guild, AttributeKeys.staff_roles,
            AttributeKeys.admin_roles, default=[])
        staff_roles = set(staff_role_list + admin_role_list)
        staff_role_mentions = [f"<@&{role.id}>" for role in staff_roles
                               if staff_roles is not None]

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

    @app_commands.command(name="tag-manage", description="Add and remove custom tags")
    @app_commands.describe(mode="Do you want to add or remove the tag?")
    @app_commands.describe(tag_name="The identifier of the tag.")
    @app_commands.describe(tag_title="The title of the new tag")
    @app_commands.describe(description="The description of the new tag")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name=TagMode.help.value, value=TagMode.help.value),
        discord.app_commands.Choice(name=TagMode.create.value, value=TagMode.create.value),
        discord.app_commands.Choice(name=TagMode.delete.value, value=TagMode.delete.value),
    ])
    @app_commands.check(is_admin_check)
    @app_commands.autocomplete(tag_name=_tag_name_autocomplete)
    @module_enabled_check(ModuleKeys.tags)
    async def tag_manage(
            self,
            itx: discord.Interaction[Bot],
            mode: str,
            tag_name: str,
            tag_title: app_commands.Range[str, 1, 256] = None,
            description: app_commands.Range[str, 1, 4096] = None,
            color: str = None,
    ):
        itx.response: discord.InteractionResponse[Bot]  # noqa
        if mode == TagMode.help.value:
            await send_help_menu(itx, 0)  # todo: add
        elif mode == TagMode.create.value:
            # validate embed color
            color_value_strings = color.split(",")
            color_value_strings = [i.strip() for i in color_value_strings]
            invalid = False
            if len(color_value_strings) != 3:
                invalid = True
            if not all(i.isdecimal() for i in color_value_strings):
                invalid = True
                color_values = []
            else:
                color_values = [int(i) for i in color_value_strings]
            if not all(0 <= i <= 255 for i in color_values):
                invalid = True
            if invalid:
                await itx.response.send_message(
                    "Invalid color: Format the color as an RGB value from "
                    "0 to 255, separated by digits. Example: \"255, 0, 127\"",
                    ephemeral=True)
                return

            assert len(color_values) == 3
            color_tuple = (color_values[0], color_values[1], color_values[2])

            await create_tag(itx.client.async_rina_db, itx.guild, tag_name,
                             tag_title, description, color_tuple)
            await itx.response.send_message(
                f"Created tag '{tag_name}'.", ephemeral=True)
        elif mode == TagMode.delete.value:
            changed = await remove_tag(itx.client.async_rina_db,
                                       itx.guild, tag_name)
            if changed:
                await itx.response.send_message(
                    f"Successfully removed tag '{tag_name}'.",
                    ephemeral=True)
            else:
                await itx.response.send_message(
                    f"There was no tag named '{tag_name}'.",
                    ephemeral=True)
        else:
            await itx.response.send_message(f"'{mode}' is not a valid mode.",
                                            ephemeral=True)

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

from datetime import datetime, timedelta
# ^ to make report tag auto-trigger at most once every 15 minutes

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.help.cogs import send_help_menu
from extensions.settings.objects import AttributeKeys, ModuleKeys
from extensions.tags.local_tag_list import (
    create_tag, remove_tag, get_tags, get_tag
)
from extensions.tags.modals.create_tag import CreateTagModal
from extensions.tags.tag_manage_modes import TagMode
from resources.checks import module_enabled_check, is_admin_check
from resources.customs import Bot
from resources.utils import replace_string_command_mentions
from resources.utils.utils import get_mod_ticket_channel
# ^ for ticket channel id in Report tag

from extensions.tags.tags import (
    tag_info_dict, create_report_info_tag, CustomTag
)


# To prevent excessive spamming when multiple people mention staff.
#  A sort of cooldown
report_message_reminder = datetime.min


def _get_enabled_tag_ids(itx) -> set[str]:
    """Helper function to get all enabled tags in a guild."""
    default_tags = [i.lower() for i in tag_info_dict]
    custom_tags = [i for i in get_tags(itx.guild)]
    return set(default_tags + custom_tags)


async def _tag_autocomplete(itx: discord.Interaction[Bot], current: str):
    """Autocomplete for /tag command."""
    if current == "":
        return [app_commands.Choice(name="Show list of tags", value="help")]

    # only show tags that are enabled in the server
    tags = _get_enabled_tag_ids(itx)

    return [app_commands.Choice(name=tag, value=tag)
            for tag in tags if current.lower() in tag.lower()
            ][:15]


@module_enabled_check(ModuleKeys.tags)
async def _tag_name_autocomplete(itx: discord.Interaction[Bot], current: str):
    """Autocomplete for /tag-manage command."""
    if itx.namespace.mode == TagMode.delete.value:
        tag_objects = get_tags(itx.guild)
        return [
            app_commands.Choice(name=key, value=key)
            for key in tag_objects.keys()
            if current.lower() in key.lower()
        ]
    return []


async def _parse_embed_color_input(color: str) -> tuple[int, int, int]:
    """
    Helper for parsing r,g,b input for embed colors.

    :param color: The color string to parse
    :return: A parsed tuple of RGB color values between 0 and 255.
    :raise ValueError: If color string is invalid.
    """
    # validate embed color
    color_value_strings = color.split(",")
    color_value_strings = [i.strip() for i in color_value_strings]
    if len(color_value_strings) != 3:
        raise ValueError("You need to provide 3 color values "
                         "separated by commas: `255, 255, 255`")
    if not all(i.isdecimal() for i in color_value_strings):
        expected_format = "255,255,255".split(",")
        raise ValueError(f"Your color values must be numbers. "
                         f"Interpreted colors: {color_value_strings}. "
                         f"Expected format: {expected_format}.")

    color_values = [int(i) for i in color_value_strings]
    assert len(color_values) == 3

    if not all(0 <= i <= 255 for i in color_values):
        raise ValueError(f"Your color values must be a number "
                         f"from 0 to 255. Your numbers ranged from "
                         f"{min(color_values)} to {max(color_values)}. "
                         f"Interpreted colors: {color_values}.")

    color_tuple = (color_values[0], color_values[1], color_values[2])
    return color_tuple


class TagFunctions(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        global report_message_reminder
        if not self.client.is_module_enabled(message.guild, ModuleKeys.tags):
            return
        if message.author.bot:
            return

        staff_role_list: list[discord.Role]
        admin_role_list: list[discord.Role]
        staff_role_list, admin_role_list = self.client.get_guild_attribute(
            message.guild, AttributeKeys.staff_roles,
            AttributeKeys.admin_roles, default=[])
        staff_roles = set(staff_role_list + admin_role_list)
        staff_role_mentions = [f"<@&{role.id}>" for role in staff_roles
                               if staff_roles is not None]

        ticket_channel: discord.abc.Messageable | None
        ticket_channel = get_mod_ticket_channel(self.client, message.guild)

        if any(staff_role_mentions in message.content
               for staff_role_mentions in staff_role_mentions):
            time_now = datetime.now()
            if time_now - report_message_reminder > timedelta(minutes=15):
                tag = create_report_info_tag(ticket_channel)
                await tag.send_to_channel(message.channel)
                report_message_reminder = time_now

    @app_commands.command(name="tag",
                          description="Look up something through a tag")
    @app_commands.describe(tag="What tag do you want more information about?")
    @app_commands.describe(public="Show everyone in chat? (default: yes)")
    @app_commands.describe(anonymous="Hide your name when sending the message "
                                     "publicly? (default: yes)")
    @app_commands.autocomplete(tag=_tag_autocomplete)
    @module_enabled_check(ModuleKeys.tags)
    async def tag(
            self,
            itx: discord.Interaction[Bot],
            tag: str,
            public: bool = True,
            anonymous: bool = True
    ):
        tag_ids = _get_enabled_tag_ids(itx)
        tag = tag.lower()
        if tag in tag_ids:
            if tag in tag_info_dict:
                await tag_info_dict[tag](itx, public, anonymous)
            else:
                tag_data = get_tag(itx.guild, tag)
                if tag_data is None:
                    raise NotImplementedError(f"Tag '{tag}' not found.")
                custom_tag = CustomTag(
                    tag,
                    tag_data["title"],
                    tag_data["description"],
                    tag_data["color"],
                    tag_data["report_to_staff"]
                )
                await custom_tag.send(itx, public, anonymous)
        elif tag == "help":
            await itx.response.send_message(
                "List of tags currently available to send:\n" +
                '\n'.join(["- " + i for i in tag_info_dict]),
                ephemeral=True
            )
        else:
            await itx.response.send_message("No tag found with this name!",
                                            ephemeral=True)

    @app_commands.command(name="tag-manage",
                          description="Add and remove custom tags")
    @app_commands.describe(mode="Do you want to add or remove the tag?")
    @app_commands.describe(tag_name="The identifier of the tag")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name=TagMode.help.value,
                                    value=TagMode.help.value),
        discord.app_commands.Choice(name=TagMode.create.value,
                                    value=TagMode.create.value),
        discord.app_commands.Choice(name=TagMode.delete.value,
                                    value=TagMode.delete.value),
    ])
    @app_commands.check(is_admin_check)
    @app_commands.autocomplete(tag_name=_tag_name_autocomplete)
    @module_enabled_check(ModuleKeys.tags)
    async def tag_manage(
            self,
            itx: discord.Interaction[Bot],
            mode: str,
            tag_name: str,
    ):
        itx.response: discord.InteractionResponse[Bot]  # type: ignore
        if mode == TagMode.help.value:
            await send_help_menu(itx, 901)
        elif mode == TagMode.create.value:
            if tag_name in _get_enabled_tag_ids(itx):
                await itx.response.send_message(
                    "A tag with this name already exists!",
                    ephemeral=True
                )
                return

            create_tag_modal = CreateTagModal()
            await itx.response.send_modal(create_tag_modal)
            await create_tag_modal.wait()
            if not create_tag_modal.return_interaction:
                # interaction aborted
                return
            itx = create_tag_modal.return_interaction

            title = create_tag_modal.embed_title.value
            description = create_tag_modal.description.value
            description = replace_string_command_mentions(
                description, itx.client)
            color = create_tag_modal.color.value
            report_to_staff = create_tag_modal.report_to_staff.value

            if color is None:
                color = "0,0,0"  # #000000 is default embed color.
            try:
                color_tuple = await _parse_embed_color_input(color)
            except ValueError as ex:
                cmd_help = itx.client.get_command_mention_with_args(
                    'help', page="901")
                await itx.response.send_message(
                    f"Invalid color:\n"
                    f"> {ex}\n"
                    f"For more help, run {cmd_help}.",
                    ephemeral=True
                )
                return
            if report_to_staff.lower() not in ["true", "false"]:
                await itx.response.send_message(
                    f"Invalid boolean for `report_to_staff`:"
                    f"Expected either `True`, `true`, `False`, or `false`\n"
                    f"but received `{report_to_staff}`.`",
                    ephemeral=True
                )
                return
            report_to_staff = report_to_staff.lower() == "true"

            await create_tag(
                itx.client.async_rina_db, itx.guild, tag_name,
                title, description, color_tuple, report_to_staff
            )
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
                    f"There was no custom tag named '{tag_name}'.",
                    ephemeral=True)
        else:
            await itx.response.send_message(f"'{mode}' is not a valid mode.",
                                            ephemeral=True)

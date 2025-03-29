import typing

import discord
import discord.ext.commands as commands
import discord.app_commands as app_commands

from resources.customs.bot import Bot
from resources.utils.permissions import is_admin, is_admin_check

from extensions.help.cogs import send_help_menu
from extensions.settings.objects import ServerSettings, ServerAttributeIds, EnabledModules


# todo: make function for parsing channel / role / user
#  Maybe make it match a specific type (eg. discord.CategoryChannel/vc/member/user).
#  Maybe autocomplete with the right type? like autocompleting channel names

# todo: make function to parse a list of ^ one of the above
#  or maybe a mix of multiple
# todo: allow individual adding and removing from lists
# todo: make options an enum or flag (not strings/dictionary! ):


# todo: make settings that are changeable also an enum

# todo: maybe a function to re-fetch settings for a specific server
#  Like if a channel is deleted, or an emoji is removed. That you don't
#  have to completely restart Rina to re-fetch every setting.

# todo: ensure SystemAttributeIds.parent_server is not in a parent server's parent server
#  The same for checking if one of the child_servers contains self, to prevent cyclic dependencies.

@app_commands.check(is_admin_check)
async def _setting_autocomplete(itx: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    if itx.namespace.type not in ["Attribute", "Module"]:
        return []

    if itx.namespace.type == "Attribute":
        attribute_keys = list(ServerAttributeIds.__required_keys__.union(ServerAttributeIds.__optional_keys__))
        return [
            app_commands.Choice(name=key, value=key) for key in attribute_keys
            if current.lower() in key.lower()
        ][:10]
    if itx.namespace.type == "Module":
        module_keys = list(EnabledModules.__required_keys__.union(EnabledModules.__optional_keys__))
        return [
            app_commands.Choice(name=key, value=key) for key in module_keys
            if current.lower() in key.lower()
        ][:10]

    # will never reach this code but IDE happy :)
    return []


class SettingsCog(commands.Cog):
    def __init__(self):
        pass

    @app_commands.command(name="migrate", description="Migrate bot settings to new database.")
    async def migrate(
            self,
            itx: discord.Interaction
    ):
        if not is_admin(itx.guild, itx.user):
            pass
        await ServerSettings.migrate(itx.client.async_rina_db)
        itx.response = typing.cast(discord.InteractionResponse, itx.response)
        await itx.response.send_message("Successfully migrated databases.", ephemeral=True)

    @app_commands.command(name="settings", description="Edit bot settings for this server.")
    @app_commands.describe(setting_type="What do you want to do?",
                           setting="The setting you want to see/modify")
    @app_commands.rename(setting_type="type")
    @app_commands.choices(setting_type=[
        discord.app_commands.Choice(name='Help', value="Help"),
        discord.app_commands.Choice(name='Attribute', value="Attribute"),
        discord.app_commands.Choice(name='Module', value="Module"),
    ])
    @app_commands.autocomplete(setting=_setting_autocomplete)
    @app_commands.check(is_admin_check)
    async def settings(
            self,
            itx: discord.Interaction,
            setting_type: str,
            setting: str | None = None
    ):

        if setting_type not in ["Help", "Attribute", "Module"]:
            itx.response.send_message("That is not a valid mode. Please use the options provided to you.",
                                      ephemeral=True)
            return

        if setting_type == "Help":
            # Todo: Make more functions call HelpPage functions.
            await send_help_menu(itx, requested_page=900)


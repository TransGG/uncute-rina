import discord
import discord.ext.commands as commands
import discord.app_commands as app_commands

from resources.customs.bot import Bot

from extensions.settings.server_settings import ServerSettings


def _setting_autocomplete(itx: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    if not is_admin(itx.guild, itx.user):
        return [app_commands.Choice(name="Only admins can use this command!", value="No permission")]


class SettingsCog(commands.Cog):
    def __init__(self):
        pass

    @app_commands.command(name="migrate", description="Migrate bot settings to new database.")
    async def settings(
            self,
            itx: discord.Interaction
    ):
        if not is_owner(itx.guild, itx.user):
            pass

    @app_commands.command(name="settings", description="Edit bot settings for this server.")
    @app_commands.describe(mode="What do you want to do?",
                           setting="The setting you want to see/modify")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Help', value=0),
        discord.app_commands.Choice(name='View a setting', value=1),
        discord.app_commands.Choice(name='Edit a setting', value=2),
    ])
    @app_commands.autocomplete(setting=_setting_autocomplete)
    async def settings(
            self,
            itx: discord.Interaction,
            mode: int,
            setting: str | None = None
    ):
        pass

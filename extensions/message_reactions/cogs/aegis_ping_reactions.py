import discord
import discord.ext.commands as commands

from resources.checks import MissingAttributesCheckFailure
from resources.customs import Bot

from extensions.settings.objects import AttributeKeys, ModuleKeys


class AEGISPingReactionsAddon(commands.Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not self.client.is_module_enabled(
                message.guild, ModuleKeys.aegis_ping_reactions):
            return
        assert message.guild is not None
        aegis_ping_role = self.client.get_guild_attributes(
            message.guild).aegis_ping_role
        if aegis_ping_role is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.aegis_ping_reactions,
                [AttributeKeys.aegis_ping_role])

        if aegis_ping_role in message.role_mentions:
            await message.add_reaction("👍")

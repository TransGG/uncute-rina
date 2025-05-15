import discord
import discord.ext.commands as commands

from resources.checks import MissingAttributesCheckFailure
from resources.customs import Bot

from extensions.settings.objects import AttributeKeys, ModuleKeys


class AEGISPingReactionsAddon(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.client.is_module_enabled(
                message.guild, ModuleKeys.aegis_ping_reactions):
            return
        aegis_ping_role: discord.Role | None = self.client.get_guild_attribute(
            message.guild, AttributeKeys.aegis_ping_role)
        if aegis_ping_role is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.aegis_ping_reactions,
                [AttributeKeys.aegis_ping_role])

        if aegis_ping_role in message.role_mentions:
            await message.add_reaction("👍")

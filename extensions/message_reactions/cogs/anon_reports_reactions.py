import discord
import discord.ext.commands as commands

from extensions.settings.objects import AttributeKeys, ModuleKeys
from resources.checks import MissingAttributesCheckFailure
from resources.customs.bot import Bot


class AnonReportsReactionsAddon(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.client.is_module_enabled(
                message.guild, ModuleKeys.anonymous_report_reactions):
            return
        anon_reports_webhook_id: int | None
        anon_reports_webhook_id = self.client.get_guild_attribute(
            message.guild, AttributeKeys.anonymous_reports_webhook_id)
        if anon_reports_webhook_id is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.anonymous_report_reactions,
                [AttributeKeys.anonymous_reports_webhook_id]
            )

        if message.webhook_id == anon_reports_webhook_id:
            await message.add_reaction("👍")

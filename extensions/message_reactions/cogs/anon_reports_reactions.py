import discord
from discord.ext import commands

from extensions.settings.objects import AttributeKeys, ModuleKeys
from resources.checks import MissingAttributesCheckFailure
from resources.customs.bot import Bot


class AnonReportsReactionsAddon(commands.Cog):
    def __init__(self, client: Bot) -> None:
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not self.client.is_module_enabled(
                message.guild, ModuleKeys.anonymous_report_reactions):
            return
        if message.guild is None:
            raise ValueError(f"message guild was None! (channel: {message.channel}, id: {message.id})")
        anon_reports_webhook_id = self.client.get_guild_attributes(
            message.guild).anonymous_reports_webhook_id
        if anon_reports_webhook_id is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.anonymous_report_reactions,
                [AttributeKeys.anonymous_reports_webhook_id]
            )

        if message.webhook_id == anon_reports_webhook_id:
            await message.add_reaction("👍")

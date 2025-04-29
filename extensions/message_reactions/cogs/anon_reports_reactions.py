import discord
import discord.ext.commands as commands

from resources.customs.bot import Bot


class AnonReportsReactionsAddon(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.client.custom_ids["anon_reports_webhook_id"]:
            await message.add_reaction("👍")

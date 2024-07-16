import discord
import discord.ext.commands as commands

from resources.customs.bot import Bot


class BanAppealReactionsAddon(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id in self.client.custom_ids["ban_appeal_webhook_ids"]:
            await message.add_reaction("👍")
            await message.add_reaction("🤷")
            await message.add_reaction("👎")


async def setup(client):
    await client.add_cog(BanAppealReactionsAddon(client))

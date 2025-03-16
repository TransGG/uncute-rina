import discord
import discord.ext.commands as commands

from resources.customs.bot import Bot


class AEGISPingReactionsAddon(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if any(role.id == self.client.custom_ids["aegis_ping_role_id"] for role in message.role_mentions):
            await message.add_reaction("👍")


async def setup(client: Bot):
    await client.add_cog(AEGISPingReactionsAddon(client))

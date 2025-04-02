import discord
import discord.ext.commands as commands

from resources.customs.bot import Bot

from extensions.settings.objects import AttributeKeys


class AEGISPingReactionsAddon(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        aegis_ping_role: discord.Role | None = self.client.get_guild_attribute(
            message.guild, AttributeKeys.aegis_ping_role)
        if aegis_ping_role is None:
            return

        if aegis_ping_role in message.role_mentions:
            await message.add_reaction("👍")

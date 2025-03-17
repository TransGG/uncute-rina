from resources.customs.bot import Bot

from extensions.aegis_ping_reactions.cogs import AEGISPingReactionsAddon


async def setup(client: Bot):
    await client.add_cog(AEGISPingReactionsAddon(client))

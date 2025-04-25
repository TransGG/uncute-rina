from resources.customs.bot import Bot

from extensions.message_reactions.cogs import AEGISPingReactionsAddon
from extensions.message_reactions.cogs import BanAppealReactionsAddon


async def setup(client: Bot):
    await client.add_cog(AEGISPingReactionsAddon(client))
    await client.add_cog(BanAppealReactionsAddon(client))


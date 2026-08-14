from extensions.message_reactions.cogs import (
    AEGISPingReactionsAddon,
    AnonReportsReactionsAddon,
    BanAppealReactionsAddon,
)
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(AEGISPingReactionsAddon(client))
    await client.add_cog(AnonReportsReactionsAddon(client))
    await client.add_cog(BanAppealReactionsAddon(client))

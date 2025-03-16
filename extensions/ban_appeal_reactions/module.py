from resources.customs.bot import Bot
from extensions.ban_appeal_reactions.cogs import BanAppealReactionsAddon


async def setup(client: Bot):
    await client.add_cog(BanAppealReactionsAddon(client))

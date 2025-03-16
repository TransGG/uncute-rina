from resources.customs.bot import Bot

from extensions.watchlist.cogs import WatchList


async def setup(client: Bot):
    await client.add_cog(WatchList(client))

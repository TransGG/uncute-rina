from extensions.watchlist.cogs import WatchList
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(WatchList(client))

from resources.customs.bot import Bot

from extensions.watchlist.cogs import WatchList


async def setup(client: Bot) -> None:
    await client.add_cog(WatchList(client))

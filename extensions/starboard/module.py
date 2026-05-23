from resources.customs.bot import Bot

from extensions.starboard.cogs import Starboard


async def setup(client: Bot) -> None:
    await client.add_cog(Starboard(client))

from resources.customs.bot import Bot

from extensions.starboard.cogs import Starboard


async def setup(client: Bot):
    await client.add_cog(Starboard(client))

from resources.customs.bot import Bot

from extensions.compliments.cogs import Compliments


async def setup(client: Bot):
    await client.add_cog(Compliments(client))

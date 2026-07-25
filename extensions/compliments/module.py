from extensions.compliments.cogs import Compliments
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(Compliments(client))

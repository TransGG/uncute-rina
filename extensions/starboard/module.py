from extensions.starboard.cogs import Starboard
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(Starboard(client))

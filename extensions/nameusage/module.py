from extensions.nameusage.cogs import NameUsage
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(NameUsage())

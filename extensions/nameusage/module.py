from resources.customs.bot import Bot

from extensions.nameusage.cogs import NameUsage


async def setup(client: Bot) -> None:
    await client.add_cog(NameUsage())

from resources.customs.bot import Bot

from extensions.nameusage.cogs import NameUsage


async def setup(client: Bot):
    await client.add_cog(NameUsage(client))

from resources.customs.bot import Bot

from extensions.customvcs.cogs import CustomVcs


async def setup(client: Bot):
    await client.add_cog(CustomVcs(client))

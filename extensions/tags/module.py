from resources.customs.bot import Bot

from extensions.tags.cogs import TagFunctions


async def setup(client: Bot):
    await client.add_cog(TagFunctions(client))

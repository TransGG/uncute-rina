from extensions.tags.cogs import TagFunctions
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(TagFunctions(client))

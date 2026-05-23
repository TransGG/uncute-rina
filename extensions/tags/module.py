from resources.customs.bot import Bot

from extensions.tags.cogs import TagFunctions


async def setup(client: Bot) -> None:
    await client.add_cog(TagFunctions(client))

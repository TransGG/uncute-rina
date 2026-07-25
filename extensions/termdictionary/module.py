from extensions.termdictionary.cogs import TermDictionary
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(TermDictionary())

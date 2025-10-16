from resources.customs.bot import Bot

from extensions.termdictionary.cogs import TermDictionary


async def setup(client: Bot) -> None:
    await client.add_cog(TermDictionary())

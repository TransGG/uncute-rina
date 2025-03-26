from resources.customs.bot import Bot

from extensions.termdictionary.cogs import TermDictionary


async def setup(client: Bot):
    await client.add_cog(TermDictionary())

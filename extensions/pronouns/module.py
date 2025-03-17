from resources.customs.bot import Bot

from extensions.pronouns.cogs import Pronouns


async def setup(client: Bot):
    await client.add_cog(Pronouns(client))

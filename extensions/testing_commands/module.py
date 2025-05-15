from resources.customs.bot import Bot
from extensions.testing_commands.cogs import TestingCog


async def setup(client: Bot):
    await client.add_cog(TestingCog())

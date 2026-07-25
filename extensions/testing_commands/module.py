from extensions.testing_commands.cogs import TestingCog
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(TestingCog())

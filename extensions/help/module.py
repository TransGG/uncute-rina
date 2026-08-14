from extensions.help.cogs import HelpCommand
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(HelpCommand())

from resources.customs.bot import Bot

from extensions.help.cogs import HelpCommand


async def setup(client: Bot):
    await client.add_cog(HelpCommand(client))

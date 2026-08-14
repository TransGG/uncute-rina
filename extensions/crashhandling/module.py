from extensions.crashhandling.cogs import CrashHandling
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(CrashHandling(client))

from resources.customs.bot import Bot

from extensions.crashhandling.cogs import CrashHandling


async def setup(client: Bot):
    await client.add_cog(CrashHandling(client))

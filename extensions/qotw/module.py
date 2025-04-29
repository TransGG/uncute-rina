from resources.customs.bot import Bot

from extensions.qotw.cogs import QOTW, DevRequest


async def setup(client: Bot):
    await client.add_cog(QOTW())
    await client.add_cog(DevRequest(client))

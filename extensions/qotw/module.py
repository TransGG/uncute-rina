from extensions.qotw.cogs import QOTW, DevRequest
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(QOTW())
    await client.add_cog(DevRequest(client))

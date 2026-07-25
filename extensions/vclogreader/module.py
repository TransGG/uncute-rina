from extensions.vclogreader.cogs import VCLogReader
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(VCLogReader())

from resources.customs.bot import Bot

from extensions.vclogreader.cogs import VCLogReader


async def setup(client: Bot):
    await client.add_cog(VCLogReader())

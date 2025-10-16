from resources.customs.bot import Bot

from extensions.vclogreader.cogs import VCLogReader


async def setup(client: Bot) -> None:
    await client.add_cog(VCLogReader())

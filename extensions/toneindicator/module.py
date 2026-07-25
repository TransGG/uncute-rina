from extensions.toneindicator.cogs import ToneIndicator
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    # client.add_command("toneindicator")
    await client.add_cog(ToneIndicator(client))

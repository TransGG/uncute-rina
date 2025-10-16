from resources.customs.bot import Bot

from extensions.toneindicator.cogs import ToneIndicator


async def setup(client: Bot) -> None:
    # client.add_command("toneindicator")
    await client.add_cog(ToneIndicator(client))

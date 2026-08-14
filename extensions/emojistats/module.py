from extensions.emojistats.cogs import EmojiStats, StickerStats
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    # client.add_command(getMemberData)
    await client.add_cog(EmojiStats(client))
    await client.add_cog(StickerStats(client))

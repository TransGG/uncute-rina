from resources.customs.bot import Bot

from extensions.emojistats.cogs import EmojiStats, StickerStats


async def setup(client: Bot):
    # client.add_command(getMemberData)
    await client.add_cog(EmojiStats(client))
    await client.add_cog(StickerStats(client))

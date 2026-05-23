from resources.customs.bot import Bot

from extensions.staff_polls_channel.cogs import StaffPollsChannelAddon


async def setup(client: Bot) -> None:
    await client.add_cog(StaffPollsChannelAddon(client))

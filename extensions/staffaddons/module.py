from resources.customs.bot import Bot

from extensions.staffaddons.cogs import StaffAddons


async def setup(client: Bot) -> None:
    await client.add_cog(StaffAddons())

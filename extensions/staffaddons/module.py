from extensions.staffaddons.cogs import StaffAddons
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(StaffAddons())

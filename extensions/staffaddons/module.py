from resources.customs.bot import Bot

from extensions.staffaddons.cogs import StaffAddons


async def setup(client: Bot):
    await client.add_cog(StaffAddons())

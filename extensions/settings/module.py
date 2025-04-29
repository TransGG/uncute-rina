from resources.customs.bot import Bot

from extensions.settings.cogs import SettingsCog


async def setup(client: Bot):
    await client.add_cog(SettingsCog())

from extensions.settings.cogs import SettingsCog
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(SettingsCog())

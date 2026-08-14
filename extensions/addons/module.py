from extensions.addons.cogs import FunAddons, OtherAddons, SearchAddons
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(FunAddons(client))
    await client.add_cog(OtherAddons())
    await client.add_cog(SearchAddons())

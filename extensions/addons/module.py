from resources.customs.bot import Bot
from extensions.addons.cogs import OtherAddons, FunAddons, SearchAddons


async def setup(client: Bot):
    await client.add_cog(FunAddons(client))
    await client.add_cog(OtherAddons())
    await client.add_cog(SearchAddons())

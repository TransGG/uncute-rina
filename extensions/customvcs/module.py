from extensions.customvcs.cogs import CustomVcs, VcTables
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(CustomVcs(client))
    await client.add_cog(VcTables())

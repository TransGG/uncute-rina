from resources.customs.bot import Bot

from extensions.customvcs.cogs import CustomVcs, VcTables


async def setup(client: Bot) -> None:
    await client.add_cog(CustomVcs(client))
    await client.add_cog(VcTables())

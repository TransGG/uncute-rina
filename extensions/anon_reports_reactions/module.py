from resources.customs.bot import Bot

from extensions.anon_reports_reactions.cogs import AnonReportsReactionsAddon


async def setup(client: Bot):
    await client.add_cog(AnonReportsReactionsAddon(client))

from resources.customs.bot import Bot

from extensions.changechannel.cogs import ChangeChannel


async def setup(client: Bot):
    # client.add_command("changechannel")
    await client.add_cog(ChangeChannel(client))

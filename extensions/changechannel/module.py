from extensions.changechannel.cogs import ChangeChannel
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    # client.add_command("changechannel")
    await client.add_cog(ChangeChannel(client))

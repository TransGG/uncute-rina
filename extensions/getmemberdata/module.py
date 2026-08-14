from extensions.getmemberdata.cogs import MemberData
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    # client.add_command(getMemberData)
    await client.add_cog(MemberData(client))

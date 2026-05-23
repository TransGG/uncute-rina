from resources.customs.bot import Bot

from extensions.getmemberdata.cogs import MemberData


async def setup(client: Bot) -> None:
    # client.add_command(getMemberData)
    await client.add_cog(MemberData(client))

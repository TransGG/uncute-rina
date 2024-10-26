import discord
import discord.ext.commands as commands

from resources.customs.bot import Bot


class BanAppealReactionsAddon(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        
    """
    ToDo
    - Make Rina have buttons instead of reactions
    - Make the buttons do something
    - Make the buttons unban if a number of upvotes cast are greater than the downvotes
    - Make the Veto button deny all other requests
    - Make the buttons count upwards when votes are cast or show a text indicator... somehow
    """
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id in self.client.custom_ids["ban_appeal_webhook_ids"]:
            await message.add_reaction("👍")
            await message.add_reaction("🤷")
            await message.add_reaction("👎")
            await message.add_reaction("❌")


async def setup(client):
    await client.add_cog(BanAppealReactionsAddon(client))

## ToDo - Remove later.
@bot.listen()
async def on_reaction_add(reaction, user):
    print("The following reactions have been added:")
    print(on_reaction_add.reaction)
    print(on_reaction_add.user)
# do something with reaction and user


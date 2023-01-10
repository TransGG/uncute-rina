from utils import * #imports 'discord import' and 'mongodb' things too

class QOTW(commands.Cog):
    def __init__(self, client):
        global RinaDB
        self.client = client
        RinaDB = client.RinaDB

    @app_commands.command(name="qotw",description="Suggest a question for the weekly queue!")
    @app_commands.describe(question="What question would you like to add?")
    async def qotw(self, itx: discord.Interaction, question: str):
        if len(question) > 250:
            await itx.response.send_message("Please make your question shorter! If you have a special request, please make a ticket (in #contact-staff)",ephemeral=True)
        # get channel of where this message has to be sent
        confirm_channel = self.client.get_channel(1019706498609319969)
        # make uncool embed for the loading period while it sends the copyable version
        embed = discord.Embed(
                color=discord.Colour.from_rgb(r=33, g=33, b=33),
                description=f"Loading question...", #{message.content}
            )
        # send the uncool embed
        msg = await confirm_channel.send(
                "",
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        #make and join a thread under the question
        thread = await msg.create_thread(name=f"QOTW-{question[:50]}")
        await thread.join()
        #send a plaintext version of the question, and copy a link to it
        copyable_version = await thread.send(f"{question}",allowed_mentions=discord.AllowedMentions.none())
        # edit the uncool embed to make it cool: Show question, link to plaintext, and upvotes/downvotes
        embed = discord.Embed(
                color=discord.Colour.from_rgb(r=255, g=255, b=172),
                title=f'',
                description=f"{question}\n[Jump to plain version]({copyable_version.jump_url})",
                timestamp=datetime.now()
            )
        embed.set_author(
                name=f"{itx.user.nick or itx.user.name}",
                url=f"", #todo
                icon_url=itx.user.display_avatar.url
        )
        embed.set_footer(text=f"")

        await msg.edit(embed=embed)
        await msg.add_reaction("⬆️")
        await msg.add_reaction("⬇️")
        await itx.response.send_message("Successfully added your question to the queue! (must first be accepted by the staff team)",ephemeral=True)

async def setup(client):
    await client.add_cog(QOTW(client))

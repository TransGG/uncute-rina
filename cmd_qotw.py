from Uncute_Rina import *
from import_modules import *

class QOTW(commands.Cog):
    def __init__(self, client: Bot):
        global RinaDB
        self.client = client
        self.qotw_channel_id = 1019706498609319969
        self.dev_request_id = 982351285959413811
        RinaDB = client.RinaDB

    @app_commands.command(name="qotw",description="Suggest a question for the weekly queue!")
    @app_commands.describe(question="What question would you like to add?")
    async def qotw(self, itx: discord.Interaction, question: str):
        if len(question) > 250:
            await itx.response.send_message("Please make your question shorter! If you have a special request, please make a ticket (in #contact-staff)",ephemeral=True)
        await itx.response.defer(ephemeral=True)
        try:
            # get channel of where this message has to be sent
            confirm_channel = itx.client.get_channel(self.qotw_channel_id)
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
                    url=f"https://original.poster/{itx.user.id}/",
                    icon_url=itx.user.display_avatar.url
            )
            embed.set_footer(text=f"")

            await msg.edit(embed=embed)
            await msg.add_reaction("⬆️")
            await msg.add_reaction("⬇️")
            await itx.followup.send("Successfully added your question to the queue! (must first be accepted by the staff team)",ephemeral=True)
        except: #something went wrong before so i wanna see if it happens again
            await itx.followup.send("Something went wrong!")
            raise


    @app_commands.command(name="developer_request",description="Suggest a bot idea to the TransPlace developers!")
    @app_commands.describe(question="What idea would you like to share?")
    async def developer_request(self, itx: discord.Interaction, question: str):
        if len(question) > 1500:
            await itx.response.send_message("Your suggestion won't fit! Please make your suggestion shorter. "
                                            "If you have a special request, you could make a ticket too (in #contact-staff)",ephemeral=True)
            return
        await itx.response.defer(ephemeral=True)
        try:
            # get channel of where this message has to be sent
            confirm_channel = itx.client.get_channel(self.dev_request_id)
            # make uncool embed for the loading period while it sends the copyable version
            embed = discord.Embed(
                    color=discord.Colour.from_rgb(r=33, g=33, b=33),
                    description=f"Loading suggestion...", #{message.content}
                )
            # send the uncool embed
            msg = await confirm_channel.send(
                    "",
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            #make and join a thread under the question
            thread = await msg.create_thread(name=f"BotRQ-{question[:48]}")
            await thread.join()
            question = question.replace("\\n", "\n")
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
                    url=f"https://original.poster/{itx.user.id}/",
                    icon_url=itx.user.display_avatar.url
            )
            embed.set_footer(text=f"")

            await msg.edit(embed=embed)
            await msg.add_reaction("⬆️")
            await msg.add_reaction("⬇️")
            await itx.followup.send("Successfully added your suggestion! The developers will review your idea, "
                                    "and perhaps inform you when it gets added :D",ephemeral=True)
        except: #something went wrong before so i wanna see if it happens again
            await itx.followup.send("Something went wrong!")
            raise

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id != self.client.staff_server_id:
            return
        if payload.channel_id != self.dev_request_id:
            return
        emoji_color_selection = {
            "🔴": discord.Colour.from_rgb(r=255,g=100,b=100),
            "🟡": discord.Colour.from_rgb(r=255,g=255,b=172),
            "🟢": discord.Colour.from_rgb(r=100,g=255,b=100),
            "🔵": discord.Colour.from_rgb(r=172,g=172,b=255)
        }
        if getattr(payload.emoji, "name", None) not in emoji_color_selection:
            return
        channel: discord.TextChannel = await self.client.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message.author.id != self.client.user.id:
            return
        if len(message.embeds) != 1:
            return
        embed = message.embeds[0]
        embed.color = emoji_color_selection[payload.emoji.name]
        await message.edit(embed=embed)
        await message.remove_reaction(payload.emoji.name, payload.member)




async def setup(client):
    await client.add_cog(QOTW(client))

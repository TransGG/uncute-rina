import discord, discord.ext.commands as commands, discord.app_commands as app_commands
from datetime import datetime # to get embed send time for embed because cool (serves no real purpose)
from resources.customs.bot import Bot
from resources.utils.permissions import is_staff # for dev request thread ping


dev_request_emoji_color_options = {
    "🔴": discord.Colour.from_rgb(r=255,g=100,b=100),
    "🟡": discord.Colour.from_rgb(r=255,g=255,b=172),
    "🟢": discord.Colour.from_rgb(r=100,g=255,b=100),
    "🔵": discord.Colour.from_rgb(r=172,g=172,b=255)
}


class QOTW(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @app_commands.command(name="qotw",description="Suggest a question for the weekly queue!")
    @app_commands.describe(question="What question would you like to add?")
    async def qotw(self, itx: discord.Interaction, question: str):
        if len(question) > 250:
            await itx.response.send_message("Please make your question shorter! If you have a special request, please make a ticket (in #contact-staff)",ephemeral=True)
        await itx.response.defer(ephemeral=True)
        try:
            # get channel of where this message has to be sent
            confirm_channel = itx.client.get_channel(self.client.custom_ids["staff_qotw_channel"])
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


class DevRequest(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
    
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
            watchlist_channel = itx.client.get_channel(self.client.custom_ids["staff_dev_request"])
            # make uncool embed for the loading period while it sends the copyable version
            embed = discord.Embed(
                    color=discord.Colour.from_rgb(r=33, g=33, b=33),
                    description=f"Loading suggestion...", #{message.content}
                )
            # send the uncool embed
            msg = await watchlist_channel.send(
                    "",
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions.none(),
                )
            #make and join a thread under the question
            thread = await msg.create_thread(name=f"BotRQ-{question[:48]}", auto_archive_duration=10080)
            await thread.join()
            question = question.replace("\\n", "\n")
            #send a plaintext version of the question, and copy a link to it
            copyable_version = await thread.send(f"{question}",allowed_mentions=discord.AllowedMentions.none())

            # mention developers in a message edit, adding them all to the thread without mentioning them
            joiner_msg = await thread.send("role mention placeholder")
            await joiner_msg.edit(content=f"<@&{self.client.custom_ids['staff_developer_role']}>")
            await joiner_msg.delete()

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
            await itx.followup.send("Something went wrong!", ephemeral=True)
            raise

    @app_commands.command(name="ping_open_dev_requests",description="Send a message in closed green dev request threads")
    async def ping_open_developer_requests(self, itx: discord.Interaction):
        if not is_staff(itx.guild, itx.user):
            await itx.response.send_message("You need to be staff to do this! It just sends \"boop\" to every dev request thread lol.", ephemeral=True)
            return
        
        await itx.response.defer(ephemeral=True)
        try:
            watchlist_channel = itx.client.get_channel(self.client.custom_ids["staff_dev_request"])
            threads: list[discord.Thread] = []
            pinged_thread_count = 0
            async for thread in watchlist_channel.archived_threads(limit=None):
                threads.append(thread)
            archived_thread_ids = [t.id for t in threads]
            for thread in watchlist_channel.threads:
                if thread.archived and thread.id not in archived_thread_ids:
                    threads.append(thread)

            for thread in threads:
                ###### TODO: remove unnecessary code: ######
                if thread.auto_archive_duration != 10080:
                    thread.edit(auto_archive_duration=10080)
                ############################################
                try:
                    starter_message = await watchlist_channel.fetch_message(thread.id)
                except discord.errors.NotFound:
                    continue # thread starter message was removed.
                
                if (starter_message is None or
                        starter_message.author.id != self.client.user.id or
                        len(starter_message.embeds) == 0):
                    continue
                if starter_message.embeds[0].color in [dev_request_emoji_color_options["🟡"], dev_request_emoji_color_options["🔵"]]:
                    cmd_mention = self.client.get_command_mention("ping_open_dev_requests")
                    await thread.send(itx.user.mention + f" poked this thread with {cmd_mention}.\n"
                                      "This channel got a message because it was archived and the request wasn't marked as completed or rejected.", allowed_mentions=discord.AllowedMentions.none())
                    pinged_thread_count += 1
            await itx.followup.send(f"Pinged {pinged_thread_count} archived channel{'' if pinged_thread_count == 1 else 's'} successfully!", ephemeral=True)
        except:
            await itx.followup.send("Something went wrong!", ephemeral=True)
            raise


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if (payload.guild_id   != self.client.custom_ids["staff_server_id"] or
            payload.channel_id != self.client.custom_ids["staff_dev_request"]):
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
    await client.add_cog(DevRequest(client))

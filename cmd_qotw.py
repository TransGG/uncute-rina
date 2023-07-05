from Uncute_Rina import *
from import_modules import *

class QOTW(commands.Cog):
    def __init__(self, client: Bot):
        global RinaDB
        self.client = client
        self.qotw_channel_id = 1019706498609319969
        self.dev_request_id = 982351285959413811
        self.watchoutdoubts_id = 989638606433968159
        RinaDB = client.RinaDB

        # setting ContextMenu here, because apparently you can't use that decorator in classes..?
        self.ctx_menu_user = app_commands.ContextMenu(
            name='Add user to watchlist',
            callback=self.watchlist_ctx_user,
        )
        self.ctx_menu_message = app_commands.ContextMenu(
            name='Add msg to watchlist',
            callback=self.watchlist_ctx_message,
        )
        self.client.tree.add_command(self.ctx_menu_user)
        self.client.tree.add_command(self.ctx_menu_message)

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


    async def add_to_watchlist(self, itx: discord.Interaction, user: discord.Member, reason: str = "", message_id: str = None):
        if not is_staff(itx):
            await itx.response.send_message("You don't have the right permissions to do this.", ephemeral=True)
            return
        
        allow_different_report_author = False
        if message_id is None:
            pass
        elif message_id.isdecimal(): # required cuz discord client doesn't let you fill in message IDs as ints; too large
            message_id = int(message_id)
        else:
            if message_id.endswith(" | overwrite"):
                message_id = message_id.split(" | ")[0]
            if message_id.isdecimal():
                message_id = int(message_id)
                allow_different_report_author = True
            else:
                await itx.response.send_message("Your message_id must be a number (the message id..)!",ephemeral=True)
                return
        if len(reason) > 2000: #embed has higher limits (?)
            await itx.response.send_message("Your watchlist reason won't fit! Please make your reason shorter. "
                                            "You can also expand your reason / add details in the thread",ephemeral=True)
            return
        
        await itx.response.defer(ephemeral=True)
        # get channel of where this message has to be sent
        doubts_channel = itx.client.get_channel(self.watchoutdoubts_id)
        # get message that supports the report / report reason
        if message_id is None:
            mentioned_msg_info = ""
        else:
            try:
                reported_message = await itx.channel.fetch_message(message_id)
                if reported_message.author.id != user.id and not allow_different_report_author:
                    await itx.followup.send(f":warning: The given message didn't match the mentioned user!\n"
                                            f"(message author: {reported_message.author}, mentioned user: {user})\n"
                                            f"If you want to use this message anyway, add \" | overwrite\" after the message id\n"
                                            f"(example: \"1817305029878989603 | overwrite\")")
                    return
                mentioned_msg_info = f"\n\n[Reported Message]({reported_message.jump_url})\n> {reported_message.content}\n"
                if allow_different_report_author:
                    mentioned_msg_info = f"\n\n[Reported Message]({reported_message.jump_url}) (message " \
                                         f"by {reported_message.author.mention})\n> {reported_message.content}\n"
                if reported_message.attachments:
                    mentioned_msg_info += f"(:newspaper: Contains {len(reported_message.attachments)} attachments)\n"
            except:
                await itx.followup.send("Couldn't fetch message from message_id. Perhaps you copied the wrong ID, "
                                        "were in another channel than the one in which the message was sent, or I don't "
                                        "have access to this current channel?")
                raise
        
        # make and send uncool embed for the loading period while it sends the copyable version
        embed = discord.Embed(
                color=discord.Colour.from_rgb(r=33, g=33, b=33),
                description=f"Loading suggestion...", #{message.content}
            )
        msg = await doubts_channel.send("", embed=embed, allowed_mentions=discord.AllowedMentions.none())
        # make and join a thread under the reason
        thread = await msg.create_thread(name=f"Watch-{(str(user)+'-'+reason)[:48]}")
        await thread.join()

        #send a plaintext version of the reason, and copy a link to it
        reason = reason.replace("\\n", "\n")
        if reason:
            copyable_version = await thread.send(f"{reason}",allowed_mentions=discord.AllowedMentions.none())
        if message_id is not None:
            if allow_different_report_author:
                a = await thread.send(f"Reported user: {user.mention} (`{user.id}`) (mentioned message author below)",allowed_mentions=discord.AllowedMentions.none())
            b = await thread.send(f"{reported_message.author.mention} (`{reported_message.author.id}`) - {reported_message.jump_url}",allowed_mentions=discord.AllowedMentions.none())
            await thread.send(f"> {reported_message.content}",allowed_mentions=discord.AllowedMentions.none())
            
            if allow_different_report_author:
                copyable_version = a
            elif not reason:
                copyable_version = b
        if message_id is None and reason == "":
            copyable_version = await thread.send(f"{user.mention} (`{user.id}`)",allowed_mentions=discord.AllowedMentions.none())
        
        # edit the uncool embed to make it cool: Show reason, link to report message (if provided), link to plaintext
        embed = discord.Embed(
                color=discord.Colour.from_rgb(r=0, g=0, b=0),
                title=f'',
                description=f"{reason}{mentioned_msg_info}\n\n[Jump to plain version]({copyable_version.jump_url})",
                timestamp=datetime.now()
            )
        embed.set_author(
                name=f"{user} - {user.display_name}",
                url=f"https://warned.username/{user.id}/",
                icon_url=user.display_avatar.url
        )
        # embed.set_footer(text=f"")

        await msg.edit(embed=embed)
        await itx.followup.send("Successfully added user to watchlist.",ephemeral=True)

    class WatchlistReason(discord.ui.Modal):
        def __init__(self, parent, title: str, reported_user: discord.User, message: discord.Message = None, timeout=None):
            super().__init__(title=title, timeout=timeout)
            self.value = None
            # self.timeout = timeout
            # self.title = title
            self.user = reported_user
            self.message = message
            self.parent: QOTW = parent

            self.reason_text = discord.ui.TextInput(label=f'Reason for reporting {reported_user}',
                                                    placeholder=f"not required but recommended",
                                                    style=discord.TextStyle.paragraph,
                                                    required=False)
            self.add_item(self.reason_text)
        
        async def on_submit(self, itx: discord.Interaction):
            self.value = 1
            await self.parent.add_to_watchlist(itx, self.user, self.reason_text.value, str(getattr(self.message, "id", "")) or None)
            self.stop()

    @app_commands.command(name="watchlist",description="Add a user to the watchlist.")
    @app_commands.describe(user="User to add", reason="Reason for adding", message_id="Message to add to reason")
    async def watchlist(self, itx: discord.Interaction, user: discord.Member, reason: str = "", message_id: str = None):
        await self.add_to_watchlist(itx, user, reason, message_id)

    async def watchlist_ctx_user(self, itx, user: discord.User):
        if not is_staff(itx): # is already checked in the main command, but saves people's time
            await itx.response.send_message("You don't have the right permissions to do this.", ephemeral=True)
            return
        watchlist_reason_modal = self.WatchlistReason(self, "Add user to watchlist", user, None, 300)
        await itx.response.send_modal(watchlist_reason_modal)

    async def watchlist_ctx_message(self, itx, message: discord.Message):
        if not is_staff(itx): # is already checked in the main command, but saves people's time
            await itx.response.send_message("You don't have the right permissions to do this.", ephemeral=True)
            return
        watchlist_reason_modal = self.WatchlistReason(self, "Add user to watchlist using message", message.author, message, 300)
        await itx.response.send_modal(watchlist_reason_modal)
        

async def setup(client):
    await client.add_cog(QOTW(client))

from Uncute_Rina import *
from import_modules import *

local_watchlist_index: dict[int, int] = {} # user_id, thread_id
busy_updating_watchlist_index: bool = False

async def get_watchlist_index(watch_channel: discord.TextChannel):
    global busy_updating_watchlist_index, local_watchlist_index
    if not busy_updating_watchlist_index:
        busy_updating_watchlist_index = True
        watchlist_index_temp: dict[int, int] = {} # to later overwrite the global variable instead of changing that directly
        for thread in watch_channel.threads:
            starter_message = await thread.parent.fetch_message(thread.id)
            try:
                # index: 0    1         2                   3          4
                #     https: / / warned.username / 262913789375021056 /
                user_id = int(starter_message.embeds[0].author.url.split("/")[3])
                if user_id in watchlist_index_temp:
                    continue # only use the user's most recent watchlist thread (if ever there is a second thread)
                watchlist_index_temp[user_id] = thread.id
            except (IndexError, AttributeError):
                pass
        else:
            async for thread in watch_channel.archived_threads(limit=None):
                starter_message = await thread.parent.fetch_message(thread.id)
                try:
                    user_id = int(starter_message.embeds[0].author.url.split("/")[3])
                    if user_id in watchlist_index_temp:
                        continue
                    watchlist_index_temp[user_id] = thread.id
                except (IndexError, AttributeError):
                    pass
        local_watchlist_index = watchlist_index_temp
        busy_updating_watchlist_index = False
    if busy_updating_watchlist_index:
        # wait until not busy anymore, in case a command triggers the function while it's still catching up
        await asyncio.sleep(1)
    return local_watchlist_index

class QOTW(commands.Cog):
    def __init__(self, client: Bot):
        global RinaDB
        self.client = client
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
            confirm_channel = itx.client.get_channel(self.client.custom_ids["staff_dev_request"])
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
        if payload.guild_id != self.client.custom_ids["staff_server"]:
            return
        if payload.channel_id != self.client.custom_ids["staff_dev_request"]:
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

    ####################
    # Watch out doubts #
    ####################
    
    async def add_to_watchlist(self, itx: discord.Interaction, user: discord.Member, reason: str = "", message_id: str = None, warning=""):
        global local_watchlist_index
        if not is_staff(itx):
            await itx.response.send_message("You don't have the right permissions to do this.", ephemeral=True)
            return
        
        allow_different_report_author = False
        # different report author = different message author than the reported user, 
        #   used in case you want to report someone but want to use someone else's 
        #   message as evidence or context.

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
                                            "You can also expand your reason / add details in the thread", ephemeral=True)
            await itx.followup.send("Given reason:\n"+reason[:1950]+"...", ephemeral=True) # because i'm nice
            return
        
        # await itx.response.defer(ephemeral=True)
        await itx.response.send_message("Adding user to watchlist...\n\n"
                                        "Please wait while rina checks if this user has been added to the watch list before. \n"
                                        "This may take a minute. (feel free to not add them to the watch list again, for that "
                                        "might make a duplicate thread for the user, :)", ephemeral=True)
        # get channel of where this message has to be sent
        watch_channel = itx.client.get_channel(self.client.custom_ids["staff_watch_channel"])
        # get message that supports the report / report reason
        if message_id is None:
            mentioned_msg_info = ""
        else:
            try:
                reported_message = await itx.channel.fetch_message(message_id)
            except:
                await itx.followup.send("Couldn't fetch message from message_id. Perhaps you copied the wrong ID, "
                                        "were in another channel than the one in which the message was sent, or I don't "
                                        "have access to this current channel?")
                raise
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

        # make and send uncool embed for the loading period while it sends the copyable version
        embed = discord.Embed(
                color=discord.Colour.from_rgb(r=33, g=33, b=33),
                description=f"Loading WANTED entry...", #{message.content}
            )
        
        watchlist_index = get_watchlist_index(watch_channel)
        already_on_watchlist = user.id in watchlist_index

        if not already_on_watchlist:
            msg = await watch_channel.send("", embed=embed, allowed_mentions=discord.AllowedMentions.none())
            # make and join a thread under the reason
            thread = await msg.create_thread(name=f"Watch-{(str(user)+'-'+str(user.id))}", auto_archive_duration=10080)
            local_watchlist_index[user.id] = thread.id # thread.id will be the same as msg.id, because of discord structure
            await thread.join()
            # await thread.send("<@&986022587756871711>", silent=True) # silent messages don't work for this
            joiner_msg = await thread.send("user-mention placeholder")
            await joiner_msg.edit(content=f"<@&{self.client.custom_ids['active_staff_role']}>")
            # targets = [] # potential workaround for the function above
            # async for user in thread.guild.fetch_members(limit=None):
            #     for role in user.roles:
            #         if role.id in [996802301283020890, 1086348907530965022, 986022587756871711]:
            #             targets.append(user.id)
            #             break
            #     if len(targets) > 50:
            #         await joiner_msg.edit(content="<@&996802301283020890>")
            #         targets = []
            await joiner_msg.delete()
        else:
            thread = await watch_channel.guild.fetch_channel(watchlist_index[user.id]) # fetch thread, in case the thread was archived (not in cache)
            msg = await watch_channel.fetch_message(watchlist_index[user.id]) # fetch message, in case msg is not in cache
            await msg.reply(content=f"Someone added {user.mention} (`{user.id}`) to the watchlist.\n"
                                    f"Since they were already on this list, here's a reply to the original thread.\n"
                                    f"May this serve as a warning for this user.", allowed_mentions=discord.AllowedMentions.none())

        #send a plaintext version of the reason, and copy a link to it
        if message_id is not None:
            if allow_different_report_author:
                a = await thread.send(f"Reported user: {user.mention} (`{user.id}`) (mentioned message author below)", allowed_mentions=discord.AllowedMentions.none())
            b = await thread.send(f"Reported message: {reported_message.author.mention} (`{reported_message.author.id}`) - {reported_message.jump_url}", allowed_mentions=discord.AllowedMentions.none())
            await thread.send(f"> {reported_message.content}",allowed_mentions=discord.AllowedMentions.none())
            
            if allow_different_report_author:
                copyable_version = a
            elif not reason:
                copyable_version = b
            else:
                copyable_version = None
        else:
            copyable_version = await thread.send(f"Reported user: {user.mention} (`{user.id}`)",allowed_mentions=discord.AllowedMentions.none())
        await thread.send(f"Reported by: {itx.user.mention} (`{itx.user.id}`)", allowed_mentions=discord.AllowedMentions.none())
        
        reason = reason.replace("\\n", "\n")
        if reason:
            c = await thread.send(f"Reason: {reason}",allowed_mentions=discord.AllowedMentions.none())
            if copyable_version is None:
                copyable_version = c

        if not already_on_watchlist:
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
            await itx.followup.send(warning+":white_check_mark: Successfully added user to watchlist.",ephemeral=True)
        else:
            await itx.followup.send(warning+":white_check_mark: Successfully added your watchlist reason."
                                    "\nNote: They were already added to the watch list, so instead I added "
                                    "the message to the already-existing thread for this user. :thumbsup:",ephemeral=True)

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
    async def watchlist(self, itx: discord.Interaction, user: discord.User, reason: str = "", message_id: str = None):
        try:
            user = await app_commands.transformers.MemberTransformer().transform(itx, user)
            warning = ""
        except app_commands.errors.TransformerError:
            warning = "This user is not in this server! Either they left or got banned, or you executed this in a server they're not in.\n" + \
                      "If they got banned, there's no reason to look out for them anymore ;)\n" + \
                      "It's also easier to mention them if you run it in the main server. Anyway,\n\n"
        await self.add_to_watchlist(itx, user, reason, message_id, warning=warning)

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
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.guild.id != self.client.custom_ids["staff_server"]:
            return
        if message.author.id != self.client.custom_ids["badeline_bot"]:
            return
        try:
            if message.channel.category.id != self.client.custom_ids["staff_logs_category"]:
                return
        except discord.errors.ClientException:
            return
        if type(message.channel) is discord.Thread: # ignore the #rules channel with its threads
            return
        
        for embed in message.embeds:
            reported_user_id = None
            fields = {"rule":None, "reason":None, "private notes":None}
            for field in embed.fields:
                if field.name.lower() == "user":
                    reported_user_id = field.value.split("`")[1]
                    if reported_user_id.isdecimal():
                        reported_user_id = int(reported_user_id)
                    else:
                        if field.value.startswith("> "):
                            field.value = field.value[2:] # remove the 'quote' md
                        reported_user_id = field.value.split(">",1)[0].split("@")[1] # from "%<@x>%", take "x"
                        if reported_user_id.isdecimal():
                            reported_user_id = int(reported_user_id)
                        else:
                            raise Exception("User id was not an id!")
                    
                if field.name.lower() in fields:
                    if field.value.startswith(">>> "):
                        fields[field.name.lower()] = field.value[4:].replace("\n", "\n> ")
                    elif field.value.startswith("> "):
                        pass # already has the desired format.
                    else: 
                        fields[field.name.lower()] = field.value.replace("\n", "\n> ")

            punish_rule = fields["rule"]
            punish_reason = fields["reason"]
            private_notes = fields["private notes"]
        # action_name = message.channel.name

        watch_channel = self.client.get_channel(self.client.custom_ids["staff_watch_channel"])
        for thread in watch_channel.threads:
            try:
                starter_message = await thread.parent.fetch_message(thread.id)
            except discord.errors.NotFound:
                # someone removed the message that the thread belongs to, without deleting the thread.
                await log_to_guild(self.client, message.guild, ":octagonal_sign: :bangbang: Someone removed a watchlist message without deleting its matching thread!")
                return
            if len(starter_message.embeds) == 0:
                continue
            if starter_message.embeds[0].author.url is None and starter_message.embeds[0].timestamp is None:
                # attempt to fix the embed message
                reason: str = ""
                reason_details_link: str = None
                reported_user: discord.User = None
                reported_message_link: str = None
                reported_message_text: str = None

                async for message in thread.history(limit=10, oldest_first=True):
                    if message.author.id == self.client.user.id:
                        if message.content.startswith("Reported user: ") or message.content.startswith("Reported message: "):
                            user_id_start_index = message.content.index("`")
                            user_id_end_index = message.content.index("`", user_id_start_index+1)
                            user_id = int(message.content[user_id_start_index:user_id_end_index].replace("`", ""))
                            reported_user = self.client.get_user(user_id)
                        if message.content.startswith("Reported message: "):
                            message_link_start_index = message.content.index("https://discord.com/channels/")
                            reported_message_link = message.content[message_link_start_index:]
                        if message.content.startswith("> "):
                            reported_message_text = message.content[2:]
                        if message.content.startswith("Reason: "):
                            reason = message.content[7:].strip()
                            reported_details_link = message.jump_url

                if reported_message_link is not None:
                    reason += f"\n\n[Reported message]({reported_message_link})"
                if reported_message_text is not None:
                    reason += f"\n> {reported_message_text}\n"
                if reason_details_link is not None:
                    reaspon += f"\n\n[Jump to plain version]({reason_details_link})"

                embed = discord.Embed(
                    color=discord.Colour.from_rgb(r=0, g=0, b=0),
                    title=f'',
                    description=f"{reason}\n\n[Jump to plain version]({reported_details_link})",
                    timestamp=starter_message.created_at
                )
                embed.set_author(
                        name=f"{reported_user.name} - {reported_user.display_name}",
                        url=f"https://warned.username/{reported_user.id}/",
                        icon_url=reported_user.display_avatar.url
                )
                await starter_message.edit(embed=embed)
                starter_message.embeds[0] = embed


            #   0       1          2                     3
            # https:  /  /  warned.username  /  262913789375021056  /
            if starter_message.embeds[0].author.url.split("/")[3] == str(reported_user_id):
                await thread.send(f"This user (<@{reported_user_id}>, `{reported_user_id}`) has an [infraction]({message.jump_url}) in {message.channel.mention}:\n" +
                                    f"Rule:\n> {punish_rule}\n" * bool(punish_rule) +
                                    f"Reason:\n> {punish_reason}\n" * bool(punish_reason) +
                                    f"Private notes:\n> {private_notes}" * bool(private_notes), 
                                  allowed_mentions=discord.AllowedMentions.none())
                return
        else:
            async for thread in watch_channel.archived_threads(limit=None):
                starter_message = await thread.parent.fetch_message(thread.id)
                if len(starter_message.embeds) == 0:
                    continue
                #   0       1          2                     3
                # https:  /  /  warned.username  /  262913789375021056  /
                if starter_message.embeds[0].author.url.split("/")[3] == str(reported_user_id):
                    await thread.send(f"This user (<@{reported_user_id}>, `{reported_user_id}`) has an [infraction]({message.jump_url}) in {message.channel.mention}:\n" +
                                        f"Rule:\n> {punish_rule}\n" * bool(punish_rule) +
                                        f"Reason:\n> {punish_reason}\n" * bool(punish_reason) +
                                        f"Private notes:\n> {private_notes}" * bool(private_notes), 
                                    allowed_mentions=discord.AllowedMentions.none())
                    return

    # @app_commands.command(name="send_fake_log_embed",description="make a user report (fake).")
    # @app_commands.describe(target="User to add", reason="Reason for adding", rule="rule to punish for", private_notes="private notes to include")
    # async def send_fake_log_embed(self, itx: discord.Interaction, target: discord.User, reason: str = "", rule: str = None, private_notes: str = ""):
    #     embed = discord.Embed(title="did a log thing for x", color=16705372)
    #     embed.add_field(name="User",value = f"{target.mention} (`{target.id}`)", inline=True)
    #     embed.add_field(name="Moderator",value = f"{itx.user.mention}", inline=True)
    #     embed.add_field(name="\u200b",value = f"\u200b", inline=False)
    #     embed.add_field(name="Rule",value = f">>> {rule}", inline=True)
    #     embed.add_field(name="\u200b",value = f"\u200b", inline=False)
    #     embed.add_field(name="Reason",value = f">>> {reason}")
    #     embed.add_field(name="\u200b",value = f"\u200b", inline=False)
    #     embed.add_field(name="Private Notes",value = f">>> {private_notes}")
    #     await self.client.get_channel(1143642283577725009).send(embed=embed)


async def setup(client):
    await client.add_cog(QOTW(client))

from datetime import datetime  # to get embed send time for embed because cool (serves no real purpose)

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from resources.customs.bot import Bot
from resources.customs.watchlist import get_or_fetch_watchlist_index, add_to_watchlist_cache
from resources.modals.watchlist import WatchlistReasonModal
from resources.utils.permissions import is_staff  # to test staff roles


class WatchList(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

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

    async def add_to_watchlist(
            self, itx: discord.Interaction, user: discord.Member, reason: str = "", message_id: str = None, warning=""
    ):
        if not is_staff(itx.guild, itx.user):
            await itx.response.send_message("You don't have the right permissions to do this.", ephemeral=True)
            return
        if user.id == self.client.user.id:
            await itx.response.send_message(
                f"You just tried to add a watchlist to Uncute Rina. Are you sure about that.......?\n"
                "If so, please send a message to Mia so she can remove this extra if-statement.", ephemeral=True)
            return

        allow_different_report_author = False
        # different report author = different message author than the reported user,
        #   used in case you want to report someone but want to use someone else's
        #   message as evidence or context.

        if message_id is str:
            if message_id is None:
                pass
            elif message_id.isdecimal():
                # required cuz discord client doesn't let you fill in message IDs as ints; too large
                message_id = int(message_id)
            else:
                if message_id.endswith(" | overwrite"):
                    message_id = message_id.split(" | ")[0]
                if message_id.isdecimal():
                    message_id = int(message_id)
                    allow_different_report_author = True
                else:
                    await itx.response.send_message("Your message_id must be a number (the message id..)!",
                                                    ephemeral=True)
                    return
        if len(reason) > 2000:  # todo: embed has higher limits (?)
            await itx.response.send_message("Your watchlist reason won't fit! Please make your reason shorter. "
                                            "You can also expand your reason / add details in the thread",
                                            ephemeral=True)
            await itx.followup.send("Given reason:\n" + reason[:1950] + "...", ephemeral=True)  # because i'm nice
            return

        # await itx.response.defer(ephemeral=True)
        await itx.response.send_message(
            "Adding user to watchlist...\n\n"
            "Please wait while rina checks if this user has been added to the watch list before. \n"
            "This may take a minute. (feel free to not add them to the watch list again, for that might make a "
            "duplicate thread for the user, :)",
            ephemeral=True
        )
        # get channel of where this message has to be sent
        watch_channel = itx.client.get_channel(self.client.custom_ids["staff_watch_channel"])
        # get message that supports the report / report reason
        reported_message = None  # to make IDE happy
        if message_id is None:
            mentioned_msg_info = ""
        else:
            try:
                reported_message = await itx.channel.fetch_message(message_id)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                await itx.followup.send("Couldn't fetch message from message_id. Perhaps you copied the wrong ID, "
                                        "were in another channel than the one in which the message was sent, or I "
                                        "don't have access to this current channel?", ephemeral=True)
                raise
            if reported_message.author.id != user.id and not allow_different_report_author:
                await itx.followup.send(
                    f":warning: The given message didn't match the mentioned user!\n"
                    f"(message author: {reported_message.author}, mentioned user: {user})\n"
                    f"If you want to use this message anyway, add \" | overwrite\" after the message id\n"
                    f"(example: \"1817305029878989603 | overwrite\")",
                    ephemeral=True
                )
                return
            mentioned_msg_info = (f"\n\n[Reported Message]({reported_message.jump_url})\n"
                                  f">>> {reported_message.content}\n")
            if allow_different_report_author:
                mentioned_msg_info = (f"\n\n[Reported Message]({reported_message.jump_url}) (message "
                                      f"by {reported_message.author.mention})\n>>> {reported_message.content}\n")
            if reported_message.attachments:
                mentioned_msg_info += f"(:newspaper: Contains {len(reported_message.attachments)} attachments)\n"

        # make and send uncool embed for the loading period while it sends the copyable version
        embed = discord.Embed(
            color=discord.Colour.from_rgb(r=33, g=33, b=33),
            description=f"Loading WANTED entry...",  # {message.content}
        )

        watchlist_index = await get_or_fetch_watchlist_index(watch_channel)
        already_on_watchlist = user.id in watchlist_index

        if not already_on_watchlist:
            msg = await watch_channel.send("", embed=embed, allowed_mentions=discord.AllowedMentions.none())
            # make and join a thread under the reason
            thread = await msg.create_thread(name=f"Watch-{(str(user) + '-' + str(user.id))}",
                                             auto_archive_duration=10080)
            add_to_watchlist_cache(user.id,
                                   thread.id)  # thread.id will be the same as msg.id, because of discord structure
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
            thread = await watch_channel.guild.fetch_channel(
                watchlist_index[user.id])  # fetch thread, in case the thread was archived (not in cache)
            msg = await watch_channel.fetch_message(
                watchlist_index[user.id])  # fetch message, in case msg is not in cache
            await msg.reply(content=f"Someone added {user.mention} (`{user.id}`) to the watchlist.\n"
                                    f"Since they were already on this list, here's a reply to the original thread.\n"
                                    f"May this serve as a warning for this user.",
                            allowed_mentions=discord.AllowedMentions.none())

        # Send a plaintext version of the reason, and copy a link to it
        if message_id is not None:
            a = ""  # to make IDE happy
            if allow_different_report_author:
                a = await thread.send(f"Reported user: {user.mention} (`{user.id}`) (mentioned message author below)",
                                      allowed_mentions=discord.AllowedMentions.none())
            b = await thread.send(
                f"Reported message: {reported_message.author.mention}"
                f"(`{reported_message.author.id}`) - {reported_message.jump_url}",
                allowed_mentions=discord.AllowedMentions.none())
            await thread.send(f">>> {reported_message.content}", allowed_mentions=discord.AllowedMentions.none())

            if allow_different_report_author:
                copyable_version = a
            elif not reason:
                copyable_version = b
            else:
                copyable_version = None
        else:
            copyable_version = await thread.send(f"Reported user: {user.mention} (`{user.id}`)",
                                                 allowed_mentions=discord.AllowedMentions.none())
        await thread.send(f"Reported by: {itx.user.mention} (`{itx.user.id}`)",
                          allowed_mentions=discord.AllowedMentions.none())

        reason = reason.replace("\\n", "\n")
        if reason:
            c = await thread.send(f"Reason: {reason}", allowed_mentions=discord.AllowedMentions.none())
            if copyable_version is None:
                copyable_version = c

        if not already_on_watchlist:
            # edit the uncool embed to make it cool: Show reason, link to report message (if provided), link
            # to plaintext
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
            await itx.followup.send(warning + ":white_check_mark: Successfully added user to watchlist.",
                                    ephemeral=True)
        else:
            await itx.followup.send(warning + ":white_check_mark: Successfully added your watchlist reason."
                                              "\nNote: They were already added to the watch list, so instead I added "
                                              "the message to the already-existing thread for this user. :thumbsup:",
                                    ephemeral=True)

    @app_commands.command(name="watchlist", description="Add a user to the watchlist.")
    @app_commands.describe(user="User to add", reason="Reason for adding", message_id="Message to add to reason")
    async def watchlist(self, itx: discord.Interaction, user: discord.User, reason: str = "", message_id: str = None):
        try:
            user = await app_commands.transformers.MemberTransformer().transform(itx, user)
            warning = ""
        except app_commands.errors.TransformerError:
            warning = ("This user is not in this server! Either they left or got banned, or you executed this in "
                       "a server they're not in.\n"
                       "If they got banned, there's no reason to look out for them anymore ;)\n"
                       "It's also easier to mention them if you run it in the main server. Anyway,\n\n")
        await self.add_to_watchlist(itx, user, reason, message_id, warning=warning)

    @app_commands.command(name="check_watchlist", description="Check if a user is on the watchlist.")
    @app_commands.describe(user="User to check")
    async def check_watchlist(self, itx: discord.Interaction, user: discord.User):
        if not is_staff(itx.guild, itx.user):
            await itx.response.send_message("You don't have the right permissions to do this.", ephemeral=True)
            return

        await itx.response.defer(ephemeral=True)

        watch_channel = itx.client.get_channel(self.client.custom_ids["staff_watch_channel"])
        watchlist_index = await get_or_fetch_watchlist_index(watch_channel)
        on_watchlist: bool = user.id in watchlist_index

        if on_watchlist:
            await itx.followup.send(f"🔵 This user ({user.mention} `{user.id}`) is already on the watchlist.",
                                    ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        else:
            await itx.followup.send(f"🟡 This user ({user.mention} `{user.id}`) is not yet on the watchlist.",
                                    ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    async def watchlist_ctx_user(self, itx, user: discord.User):
        if not is_staff(itx.guild, itx.user):  # is already checked in the main command, but saves people's time
            await itx.response.send_message("You don't have the right permissions to do this.", ephemeral=True)
            return
        watchlist_reason_modal = WatchlistReasonModal(self.add_to_watchlist, "Add user to watchlist", user, None, 300)
        await itx.response.send_modal(watchlist_reason_modal)

    async def watchlist_ctx_message(self, itx, message: discord.Message):
        if not is_staff(itx.guild, itx.user):  # is already checked in the main command, but saves people's time
            await itx.response.send_message("You don't have the right permissions to do this.", ephemeral=True)
            return
        watchlist_reason_modal = WatchlistReasonModal(self.add_to_watchlist, "Add user to watchlist using message",
                                                      message.author, message, 300)
        await itx.response.send_modal(watchlist_reason_modal)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.guild.id != self.client.custom_ids["staff_server_id"]:
            return
        if message.author.id != self.client.custom_ids["badeline_bot"]:
            return
        try:
            if message.channel.category.id != self.client.custom_ids["staff_logs_category"]:
                return
        except discord.errors.ClientException:
            return
        if type(message.channel) is discord.Thread:  # ignore the #rules channel with its threads
            return
        if len(message.embeds) == 0:
            # ignore messages without embeds (if the bot (or in dev env. rina herself) sends a chat message or
            # reponse in this channel)
            return

        reported_user_id = None
        for embed in message.embeds:
            for field in embed.fields:
                if field.name.lower() == "user":
                    reported_user_id = field.value.split("`")[1]
                    if reported_user_id.isdecimal():
                        reported_user_id = int(reported_user_id)
                    else:
                        if field.value.startswith("> "):
                            field.value = field.value[2:]  # remove the 'quote' md
                        reported_user_id = field.value.split(">", 1)[0].split("@")[1]  # from "%<@x>%", take "x"
                        if reported_user_id.isdecimal():
                            reported_user_id = int(reported_user_id)
                        else:
                            raise Exception("User id was not an id!")

        watch_channel: discord.TextChannel = self.client.get_channel(self.client.custom_ids["staff_watch_channel"])
        watchlist_index = await get_or_fetch_watchlist_index(watch_channel)
        on_watchlist: bool = reported_user_id in watchlist_index

        # for thread in watch_channel.threads:
        if on_watchlist:
            thread: discord.Thread = await watch_channel.guild.fetch_channel(watchlist_index[reported_user_id])
            await message.forward(thread)
            # await thread.send(f"This user (<@{reported_user_id}>, `{reported_user_id}`) has an "
            #                   f"[infraction]({message.jump_url}) in {message.channel.mention}.",
            #                   embeds=message.embeds,
            #                   allowed_mentions=discord.AllowedMentions.none())


async def setup(client: Bot):
    await client.add_cog(WatchList(client))

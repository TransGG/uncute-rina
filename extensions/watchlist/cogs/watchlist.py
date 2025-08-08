from datetime import datetime
# ^ to get embed send time for embed because cool (serves no real purpose)

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands
from discord import RawThreadDeleteEvent

from extensions.settings.objects import ModuleKeys, AttributeKeys
from resources.customs import Bot, GuildInteraction
from resources.checks.permissions import is_staff
# ^ to check role in _add_to_watchlist, as backup
from resources.checks import (
    is_staff_check, module_enabled_check, MissingAttributesCheckFailure
)  # the cog is pretty much only intended for staff use

from extensions.watchlist.local_watchlist import (
    create_watchlist,
    get_watchlist,
    remove_watchlist,
    get_user_id_from_watchlist,
    WatchlistNotLoadedException,
)
from extensions.watchlist.modals import WatchlistReasonModal


def _parse_watchlist_string_message_id(
        message_id: str | None
) -> tuple[int | None, bool]:
    """
    Parse a given message_id from a /watchlist command

    :param message_id: The message id to parse to an int (or ``None``).
    :return: A tuple of the parsed message id (or ``None`` if ``None``
     given), and whether the message_id ended with " | overwrite", to
     allow the user to link someone else's message with the watchlist
     report.
    """
    allow_different_report_author = False
    if message_id is None:
        return message_id, allow_different_report_author

    if message_id.isdecimal():
        # required cuz discord client doesn't let you fill in message
        # IDs as ints; too large
        msg_id = int(message_id)
    else:
        if message_id.endswith(" | overwrite"):
            message_id = message_id.split(" | ")[0]

        msg_id = int(message_id)  # raises ValueError
        allow_different_report_author = True
    return msg_id, allow_different_report_author


async def _create_uncool_watchlist_thread(
        client: Bot,
        user: discord.Member | discord.User,
        watch_channel: discord.TextChannel
) -> tuple[discord.Message, discord.Thread]:
    """
    A helper function to create a new watchlist thread if it
    wasn't created already.

    :param user: The user to create the watchlist thread for.
    :param watch_channel: The channel to create the thread in.
    :return: A tuple of the created watchlist message and thread.
    """
    # make and send uncool embed for the loading period while it sends
    # the copyable version (we want the jump url)
    embed = discord.Embed(
        color=discord.Colour.from_rgb(r=33, g=33, b=33),
        description="Loading WANTED entry...",  # {message.content}
    )

    msg = await watch_channel.send(
        "",
        embed=embed,
        allowed_mentions=discord.AllowedMentions.none()
    )
    # Make and join a thread under the reason.
    # Max thread name length is 100 chars. Shorten username to 70 chars:
    #  "Watch-" = 6 chars + 70 + 1 + 19 (user id) = 96 chars < 100
    thread_username = "Watch-" + str(user)[:70] + '-' + str(user.id)
    thread = await msg.create_thread(name=thread_username,
                                     auto_archive_duration=10080)
    await thread.join()
    joiner_msg = await thread.send("user-mention placeholder")
    watchlist_reaction_role: discord.Guild | None = client.get_guild_attribute(
        watch_channel.guild,
        AttributeKeys.watchlist_reaction_role
    )
    if watchlist_reaction_role is None:
        cmd_settings = client.get_command_mention_with_args(
            "settings",
            type="Attribute",
            setting=AttributeKeys.watchlist_reaction_role,
            mode="Set",
            value=" "
        )
        await joiner_msg.edit(
            content=f"No role has been set up to be pinged when a watchlist "
                    f"is created. Use {cmd_settings} to add one."
        )
    else:
        await joiner_msg.edit(content=f"<@&{watchlist_reaction_role.id}>")
        await joiner_msg.delete()
    return msg, thread


async def _update_uncool_watchlist_embed(
        jump_url: str, reported_message_info,
        msg, reason, user):
    # edit the uncool embed to make it cool: Show reason, link to
    #  report message (if provided), link to plaintext
    embed = discord.Embed(
        color=discord.Colour.from_rgb(r=0, g=0, b=0),
        title='',
        description=f"{reason}{reported_message_info}\n"
                    f"\n"
                    f"[Jump to plain version]({jump_url})",
        timestamp=datetime.now()
    )
    embed.set_author(
        name=f"{user} - {user.display_name}",
        url=f"https://warned.username/{user.id}/",
        icon_url=user.display_avatar.url
    )
    # embed.set_footer(text="")
    await msg.edit(embed=embed)


async def _add_to_watchlist(
        itx: discord.Interaction[Bot],
        user: discord.Member | discord.User,
        reason: str = "",
        message_id_str: str | None = None,
        warning=""
):
    if not is_staff(itx, itx.user):
        await itx.response.send_message(
            "You don't have the right permissions to do this.",
            ephemeral=True,
        )
        return
    if itx.client.is_me(user):
        await itx.response.send_message(
            "You just tried to add a watchlist to Uncute Rina. Are you "
            "sure about that.......?\n"
            "If so, please send a message to Mia so she can remove this "
            "extra if-statement.",
            ephemeral=True,
        )
        return

    # different report author = different message author than the
    #  reported user, used in case you want to report someone but want
    #  to use someone else's message as evidence or context.
    message_id, allow_different_report_author = \
        _parse_watchlist_string_message_id(message_id_str)

    if len(reason) > 4000:
        # embeds have 4096 description length limit (and 6000 total
        # char length limit).
        await itx.response.send_message(
            "Your watchlist reason won't fit! Please make your reason "
            "shorter. You can also expand your reason / add details in "
            "the thread.",
            ephemeral=True,
        )
        # because I'm nice
        await itx.followup.send(
            "Given reason (you can also copy paste the command):\n"  # 52 chars
            + reason[:2000 - 52 - 3] + "...",
            ephemeral=True,
        )
        return

    # get channel of where this message has to be sent
    watch_channel: discord.TextChannel | None = itx.client.get_guild_attribute(
        itx.guild, AttributeKeys.watchlist_channel)
    if watch_channel is None:
        raise MissingAttributesCheckFailure(
            ModuleKeys.watchlist, [AttributeKeys.watchlist_channel])

    # await itx.response.defer(ephemeral=True)
    await itx.response.send_message(
        "Adding user to watchlist...",
        ephemeral=True
    )

    # get message that supports the report / report reason
    reported_message = None  # to make IDE happy
    if message_id is None:
        reported_message_info = ""
    else:
        try:
            reported_message = await itx.channel.fetch_message(message_id)
        except discord.Forbidden:
            await itx.followup.send(
                "Forbidden: I do not have permission to see that message.",
                ephemeral=True,
            )
            return
        except discord.NotFound:
            await itx.followup.send(
                "NotFound: I could not find that message. Make sure you ran "
                "this command in the same channel as the one where the "
                "message id came from.",
                ephemeral=True,
            )
            return
        except discord.HTTPException:
            await itx.followup.send(
                "HTTPException: Something went wrong while trying to fetch "
                "the message.",
                ephemeral=True,
            )
            raise

        if (reported_message.author.id != user.id
                and not allow_different_report_author):
            author_info = (f"(message author: {reported_message.author}, "
                           f"mentioned user: {user})\n")
            await itx.followup.send(
                ":warning: The given message didn't match the mentioned "
                "user!\n"
                + author_info
                + "If you want to use this message anyway, add "
                  "\" | overwrite\" after the message id\n"
                  "(example: \"1817305029878989603 | overwrite\")",
                ephemeral=True
            )
            return

        different_report_author_info = ""
        if allow_different_report_author:
            different_report_author_info = \
                f" (message by {reported_message.author.mention})"

        reported_message_info = (
            f"\n\n[Reported Message]({reported_message.jump_url})"
            f"{different_report_author_info}\n"
            f">>> {reported_message.content}\n"
        )

        if reported_message.attachments:
            reported_message_info += (
                f"(:newspaper: Contains "
                f"{len(reported_message.attachments)} attachments)\n"
            )

    watchlist_thread_id = get_watchlist(watch_channel.guild.id, user.id)
    already_on_watchlist = watchlist_thread_id is not None

    if already_on_watchlist:
        # fetch thread, in case the thread was archived (not in cache)
        thread: discord.Thread = await watch_channel.guild.fetch_channel(
            watchlist_thread_id)  # type: ignore

        # fetch message the thread is attached to (fetch, in case msg
        #  is not in cache)
        msg = await watch_channel.fetch_message(watchlist_thread_id)
        # link back to that original message with the existing thread.
        await msg.reply(
            content=f"Someone added {user.mention} (`{user.id}`) to the "
                    f"watchlist.\n"
                    f"Since they were already on this list, here's a reply "
                    f"to the original thread.\n"
                    f"May this serve as a warning for this user.",
            allowed_mentions=discord.AllowedMentions.none(),
        )
    else:
        msg, thread = await _create_uncool_watchlist_thread(
            itx.client, user, watch_channel)
        # (thread.id would be the same as msg.id, because of
        #  discord structure)
        await create_watchlist(
            itx.client.async_rina_db,
            watch_channel.guild.id,
            user.id,
            thread.id
        )

    # Send a plaintext version of the reason, and copy a link to it

    different_author_warning = ""
    if allow_different_report_author:
        different_author_warning = " (mentioned message author below)"
    copyable_version = await thread.send(
        f"Reported user: {user.mention} (`{user.id}`)"
        + different_author_warning,
        allowed_mentions=discord.AllowedMentions.none())

    if message_id is not None:
        reported_message_data_message = await thread.send(
            f"Reported message: {reported_message.author.mention}"
            f"(`{reported_message.author.id}`) - {reported_message.jump_url}",
            allowed_mentions=discord.AllowedMentions.none(),
        )
        await thread.send(f">>> {reported_message.content}",
                          allowed_mentions=discord.AllowedMentions.none())

        if not reason and not copyable_version:
            copyable_version = reported_message_data_message

    await thread.send(f"Reported by: {itx.user.mention} (`{itx.user.id}`)",
                      allowed_mentions=discord.AllowedMentions.none())

    reason = reason.replace("\\n", "\n")
    if reason:
        c = await thread.send(
            f"Reason: {reason}"[:2000],
            allowed_mentions=discord.AllowedMentions.none()
        )
        if copyable_version is None:
            copyable_version = c

    if already_on_watchlist:
        await itx.followup.send(
            warning
            + ":white_check_mark: Successfully added your watchlist reason."
              "\nNote: They were already added to the watch list, so instead "
              "I added the message to the already-existing thread for this "
              "user. :thumbsup:",
            ephemeral=True
        )
    else:
        await _update_uncool_watchlist_embed(
            copyable_version.jump_url,
            reported_message_info,
            msg,
            reason,
            user
        )
        await itx.followup.send(
            warning
            + ":white_check_mark: Successfully added user to watchlist.",
            ephemeral=True,
        )


@app_commands.context_menu(name="Add user to watchlist")
@is_staff_check
@module_enabled_check(ModuleKeys.watchlist)
async def watchlist_ctx_user(
        itx: GuildInteraction[Bot],
        user: discord.User,
):
    watchlist_reason_modal = WatchlistReasonModal(
        _add_to_watchlist,
        title="Add user to watchlist",
        reported_user=user,
        message=None,
        timeout=300,
    )
    await itx.response.send_modal(watchlist_reason_modal)


@app_commands.context_menu(name="Add msg to watchlist")
@module_enabled_check(ModuleKeys.watchlist)
@is_staff_check
async def watchlist_ctx_message(
        itx: discord.Interaction[Bot],
        message: discord.Message
):
    watchlist_reason_modal = WatchlistReasonModal(
        _add_to_watchlist,
        title="Add user to watchlist using message",
        reported_user=message.author,
        message=message,
        timeout=300,
    )
    await itx.response.send_modal(watchlist_reason_modal)


class WatchList(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        self.client.tree.add_command(watchlist_ctx_user)
        self.client.tree.add_command(watchlist_ctx_message)

    @app_commands.command(name="watchlist",
                          description="Add a user to the watchlist.")
    @app_commands.describe(user="User to add",
                           reason="Reason for adding",
                           message_id="Message to add to reason")
    @is_staff_check
    @module_enabled_check(ModuleKeys.watchlist)
    async def watchlist(
            self,
            itx: discord.Interaction[Bot],
            user: discord.User | discord.Member,
            reason: str = "",
            message_id: str | None = None
    ):
        try:
            user = await (app_commands.transformers
                          .MemberTransformer()
                          .transform(itx, user))
            warning = ""
        except app_commands.errors.TransformerError:
            warning = (
                "This user is not in this server! Either they left or got "
                "banned, or you executed this in a server they're not in.\n"
                "If they got banned, there's no reason to look out for them "
                "anymore ;)\n"
                "It's also easier to mention them if you run it in the main "
                "server. Anyway,\n\n"
            )
        await _add_to_watchlist(itx, user, reason, message_id, warning=warning)

    @app_commands.command(name="check_watchlist",
                          description="Check if a user is on the watchlist.")
    @app_commands.describe(user="User to check")
    @is_staff_check
    @module_enabled_check(ModuleKeys.watchlist)
    async def check_watchlist(
            self,
            itx: discord.Interaction[Bot],
            user: discord.User
    ):
        if not is_staff(itx, itx.user):
            await itx.response.send_message(
                "You don't have the right permissions to do this.",
                ephemeral=True
            )
            return

        watch_channel = itx.client.get_guild_attribute(
            itx.guild, AttributeKeys.watchlist_channel)
        if watch_channel is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.watchlist, [AttributeKeys.watchlist_channel])

        await itx.response.defer(ephemeral=True)
        watchlist_thread_id = get_watchlist(watch_channel.guild.id, user.id)
        on_watchlist: bool = watchlist_thread_id is not None

        if on_watchlist:
            await itx.followup.send(
                f"🔵 This user ({user.mention} `{user.id}`) is already "
                f"on the watchlist.",
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        else:
            await itx.followup.send(
                f"🟡 This user ({user.mention} `{user.id}`) is not yet "
                f"on the watchlist.",
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.client.is_module_enabled(
                message.guild, ModuleKeys.watchlist):
            return
        staff_logs_category: discord.CategoryChannel | None
        badeline_bot: discord.User | None
        watchlist_channel: discord.TextChannel | None
        staff_logs_category, badeline_bot, watchlist_channel = \
            self.client.get_guild_attribute(
                message.guild,
                AttributeKeys.staff_logs_category,
                AttributeKeys.badeline_bot,
                AttributeKeys.watchlist_channel
            )
        if None in (staff_logs_category, badeline_bot, watchlist_channel):
            missing = [key for key, value in {
                AttributeKeys.staff_logs_category: staff_logs_category,
                AttributeKeys.badeline_bot: badeline_bot,
                AttributeKeys.watchlist_channel: watchlist_channel}.items()
                if value is None]
            raise MissingAttributesCheckFailure(ModuleKeys.watchlist, missing)

        if message.author.id != badeline_bot.id:
            # Don't compare author == badeline_bot, because author can be
            #  a discord.Member, whereas badeline_bot would be a discord.User
            return

        if message.channel.category != staff_logs_category:
            return
        if type(message.channel) is discord.Thread:
            # ignore the #rules channel with its threads
            return
        if len(message.embeds) == 0:
            # ignore messages without embeds (if the bot (or in
            #  dev env. rina herself) sends a chat message or
            #  response in this channel)
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
                            # remove the `> quote` markdown
                            field.value = field.value[2:]
                        # from "%<@x>%", take "x"
                        reported_user_id = (field
                                            .value
                                            .split(">", 1)[0]
                                            .split("@")[1])
                        if reported_user_id.isdecimal():
                            reported_user_id = int(reported_user_id)
                        else:
                            raise Exception("User id was not an id!")

        watchlist_thread_id = get_watchlist(
            watchlist_channel.guild.id, reported_user_id)
        on_watchlist: bool = watchlist_thread_id is not None

        if on_watchlist:
            thread: discord.Thread = \
                await watchlist_channel.guild.fetch_channel(
                    watchlist_thread_id
                )
            # ^ fetch, to retrieve (archived) thread.
            await message.forward(thread)

    @commands.Cog.listener()
    async def on_raw_thread_delete(self, event: RawThreadDeleteEvent):
        try:
            user_id = get_user_id_from_watchlist(
                event.guild_id, event.thread_id)
        except WatchlistNotLoadedException:
            return

        await remove_watchlist(self.client.async_rina_db,
                               event.guild_id, user_id)

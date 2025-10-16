import typing

import discord

from resources.customs import Bot
from datetime import datetime


# region create thread

async def _create_starter_message(
        channel: discord.TextChannel,
) -> discord.Message:
    """
    Helper to send a (fancy) temporary message to a channel. Intended for
     adding a thread to later, while also indicating that the command is
     still in progress.
    :param channel: The channel to send the message to.
    :return: The sent message.
    """
    # Make uncool embed for the loading period while it sends the
    #  copyable version
    embed = discord.Embed(
        color=discord.Colour.from_rgb(r=33, g=33, b=33),
        description="Loading request...",
    )
    # send the uncool embed
    msg = await channel.send(
        "",
        embed=embed,
        allowed_mentions=discord.AllowedMentions.none(),
    )
    return msg


async def _create_and_join_thread(
        msg: discord.Message,
        thread_title: str,
) -> discord.Thread:
    """
    Helper to create and join a thread with an archive delay of 7 days.

    :param msg: The message to add a thread to.
    :param thread_title: The thread title, a string between 1 and 100
     characters.
    :return: The created thread.
    """
    # make and join a thread under the question
    thread = await msg.create_thread(
        name=thread_title[:100],
        auto_archive_duration=10080,
    )
    await thread.join()
    return thread


async def _ping_reaction_role(
        client: Bot,
        reaction_role_key: str,
        thread: discord.Thread,
) -> None:
    """
    Helper to retrieve a reaction role and ping it silently, or send a
     message if the reaction role has not been set yet.

    :param itx: The interaction and client to retrieve the reaction role with.
    :param reaction_role_key: The reaction role key to retrieve.
    :param thread: The thread to ping.
    """
    # Mention the reaction role in a message edit, adding them all to the
    # thread without mentioning them and do the same for the requester,
    # though this will only work if they're in the staff server..
    joiner_msg = await thread.send("role mention placeholder")
    reaction_role: discord.Role | None
    reaction_role = client.get_guild_attribute(
        thread.guild,
        reaction_role_key,
    )
    if reaction_role is None:
        cmd_settings = client.get_command_mention_with_args(
            "settings",
            type="Attribute",
            setting=reaction_role_key,
            mode="Set",
            value=" ",
        )
        await joiner_msg.edit(
            content=f"No role has been set up to be pinged after a "
                    f"new thread is created. Use {cmd_settings} "
                    f"to add one."
        )
    else:
        await joiner_msg.edit(
            content=f"<@&{reaction_role.id}>")
        await joiner_msg.delete()


def _create_main_embed(
        copyable_version: discord.Message,
        description: str,
        user: discord.User | discord.Member,
):
    """
    Create an embed for a thread. It has a description and hyperlink to the
     first message in the thread.
    :param copyable_version: The top message in the thread, typically
     containing the raw text description of the thread.
    :param description: The description to put in the embed.
    :param user: The interaction's user to add as author for the embed.
    :return:
    """
    # edit the uncool embed to make it cool: Show question, link to
    #  plaintext
    embed = discord.Embed(
        color=discord.Colour.from_rgb(r=255, g=255, b=172),
        title='',
        description=f"{description}\n"
                    f"[Jump to plain version]"
                    f"({copyable_version.jump_url})",
        timestamp=datetime.now(),
    )
    username = getattr(user, 'nick', user.name)
    embed.set_author(
        name=f"{username}",
        url=f"https://original.poster/{user.id}/",
        icon_url=user.display_avatar.url
    )
    embed.set_footer(text="")
    return embed


async def create_thread(
        client: Bot,
        starter_msg_data: discord.Message | tuple[
            discord.User | discord.Member,
            discord.TextChannel,
            str
        ],  # todo: rename to Literal
        thread_title: str,
        reaction_role_key: str,
        emojis: list[discord.PartialEmoji | discord.Emoji],
) -> None:
    """
    Create a new message and thread in a channel.
    :param client: The client to get the reaction role with.
    :param starter_msg_data: The message to add the thread to, or a
     tuple of the creating user, the channel to create the thread in, and
     the description to put in the thread and embed.
    :param thread_title: The thread title, a string between 1 and 100
     characters.
    :param reaction_role_key: The reaction role to mention after the thread
     is created, or None to not add anyone to the thread.
    :param emojis: Emojis to add to the main thread embed. Typically for
     voting.
    """
    if not isinstance(starter_msg_data, tuple):
        starter_msg = starter_msg_data
        thread = await _create_and_join_thread(starter_msg, thread_title)
    else:
        user, channel, description = starter_msg_data
        starter_msg = await _create_starter_message(channel)
        thread = await _create_and_join_thread(starter_msg, thread_title)

        # send a plaintext version of the question, and copy a link to it
        copyable_version = await thread.send(
            f"{description}",
            allowed_mentions=discord.AllowedMentions.none()
        )

        embed = _create_main_embed(copyable_version, description, user)
        await starter_msg.edit(embed=embed)

    if reaction_role_key is not None:
        await _ping_reaction_role(client, reaction_role_key, thread)

    for emoji in emojis:
        await starter_msg.add_reaction(emoji)

# endregion create thread


async def ping_open_threads(
        itx: discord.Interaction[Bot],
        channel: discord.TextChannel,
        predicate: typing.Callable[
            [discord.Thread, discord.Message],
            bool
        ],
        ping_message: str
):
    """
    Helper to send a message to all threads Rina created in a channel.

    :param itx: The interaction to update for a progress bar.
    :param channel: The channel that contains all the watchlist threads.
    :param predicate: A function with two parameters: The thread to
     test, and the thread's first message (starter message). It should
     return a boolean indicating whether the thread should be pinged.
    :param ping_message: The message to send to each pinged thread.
    """
    await itx.response.send_message(
        "`[+  ]`: Fetching cached threads.",
        ephemeral=True
    )
    threads: list[discord.Thread] = []
    async for thread in channel.archived_threads(limit=None):
        threads.append(thread)

    await itx.edit_original_response(
        content="`[#+ ]`: Fetching archived threads...")
    archived_thread_ids = [t.id for t in threads]
    for thread in channel.threads:
        if thread.archived and thread.id not in archived_thread_ids:
            threads.append(thread)

    await itx.edit_original_response(
        content="`[##+]`: Sending messages in threads...")

    pinged_thread_count = 0
    unpinged_thread_count = 0
    ignored_count = 0
    # irrelevant_threads = []
    missing_starter_messages = []
    forbidden_threads = []

    for thread in threads:
        try:
            starter_message = \
                await channel.fetch_message(thread.id)
        except discord.errors.NotFound:
            missing_starter_messages.append(thread.id)
            continue  # thread starter message was removed.

        if (
                starter_message is None
                or not itx.client.is_me(starter_message.author)
                or len(starter_message.embeds) == 0
        ):
            ignored_count += 1
            # irrelevant_threads.append(thread.id)
            continue

        success = predicate(thread, starter_message)
        if success:
            try:
                await thread.send(
                    ping_message,
                    allowed_mentions=discord.AllowedMentions.none()
                )
                pinged_thread_count += 1
            except discord.Forbidden:
                forbidden_threads.append(thread.id)
        else:
            unpinged_thread_count += 1

    total_count = pinged_thread_count + unpinged_thread_count
    await itx.edit_original_response(
        content=(
            f"`[###]`: Pinged {pinged_thread_count}/{total_count} archived "
            f"thread{'' if pinged_thread_count == 1 else 's'} "
            f"successfully!\n"
            f"\n"
            f"Ignored `{ignored_count}` threads (not by bot or "
            f"no embeds, etc.)\n"
            f"\n"
            f"Could not find starter messages for the following "
            f"{len(missing_starter_messages)} threads:\n"
            f"- {', '.join(['<#' + str(t_id) + '>'
                            for t_id in missing_starter_messages])}\n"
            f"Could not send a message in the following "
            f"{len(forbidden_threads)} threads (Forbidden):\n"
            f"- {', '.join(['<#' + str(t_id) + '>'
                            for t_id in forbidden_threads])}"
        )[:2000]
    )

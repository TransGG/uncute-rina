import typing

import discord
import discord.ext.commands as commands

from extensions.settings.objects import AttributeKeys, ModuleKeys, MessageableGuildChannel
from resources.checks import MissingAttributesCheckFailure
from resources.customs import Bot, GuildMessage
from resources.utils.discord_utils import get_or_fetch_channel
from resources.utils.utils import log_to_guild
# ^ to log starboard addition/removal

from extensions.starboard.local_starboard import (
    add_to_local_starboard,
    delete_from_local_starboard,
    parse_starboard_message,
    get_starboard_message_id,
    is_starboard_message,
    get_original_message_info,
)


starboard_message_ids_marked_for_deletion = []


async def _fetch_starboard_original_message(
        client: Bot,
        starboard_message: GuildMessage,
        starboard_emoji: discord.Emoji
) -> GuildMessage | None:
    """
    Uses the 'jump to original' link in a starboard message to fetch
    its original author's message.

    :param client: The bot, to get the correct logging channel.
    :param starboard_message: The starboard message to get the original
     message of.
    :param starboard_emoji: The starboard upvote emoji, used in
     logging messages.

    :return: The original author's message, or None if it was not
     found (``Forbidden`` or ``NotFound``).

    .. note::

        If the original message was deleted (``NotFound``), it deletes
        its starboard message too.
    """
    # find original message
    try:
        guild_id, channel_id, message_id = \
            parse_starboard_message(starboard_message)
    except (ValueError, IndexError) as ex:
        await log_to_guild(
            client,
            starboard_message.guild,
            f"{starboard_emoji} :x: Starboard message {starboard_message.id} "
            f"was ignored ({ex})"
        )
        return None
    ch = client.get_channel(channel_id)

    if (ch is None
            or not isinstance(ch, MessageableGuildChannel.__value__)):
        await log_to_guild(
            client,
            starboard_message.guild,
            f":warning: Couldn't find starboard channel from starboard "
            f"message!\n"
            f"starboard message: "
            f"{starboard_message.channel.id}/{starboard_message.id}\n"
            f"recovered channel id: {channel_id}"
        )
        return None
    ch = typing.cast(MessageableGuildChannel, ch)

    try:
        original_message = await fetch_message_from_channel(ch, message_id)
    except discord.NotFound:
        # if original message removed, remove starboard message
        await _delete_starboard_message(
            client,
            starboard_message,
            f"{starboard_emoji} :x: Starboard message "
            f"{starboard_message.id} was removed (from {message_id}) "
            f"(original message could not be found)"
        )
        return None
    except discord.errors.Forbidden:
        await log_to_guild(
            client,
            starboard_message.guild,
            f":warning: Couldn't fetch starboard message "
            f"[{starboard_message.id}]({starboard_message.jump_url}) "
            f"from this channel ({ch.mention})!"
        )
        return None
    return original_message


async def _send_starboard_message(
        client: Bot,
        message: GuildMessage,
        starboard_channel: discord.abc.Messageable,
        reaction: discord.Reaction
):
    embed = discord.Embed(
        color=discord.Colour.from_rgb(r=255, g=172, b=51),
        title='',
        description=f"{message.content}",
        timestamp=message.created_at  # this, or datetime.now()
    )
    # noinspection LongLine
    msg_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"  # noqa
    embed.add_field(name="Source", value=f"[Jump!]({msg_link})")
    embed.set_footer(text=f"{message.id}")
    if isinstance(message.author, discord.Member):
        name = message.author.nick or message.author.name
    else:
        # discord.User has no `nick` attribute.
        name = message.author.name
    embed.set_author(
        name=f"{name}",
        url=f"https://original.poster/{message.author.id}/",
        icon_url=message.author.display_avatar.url
    )
    embed_list = []
    for attachment in message.attachments:
        try:
            if attachment.content_type.split("/")[0] == "image":
                # attachment is an image or GIF
                if len(embed_list) == 0:
                    embed.set_image(url=attachment.url)
                    embed_list = [embed]
                else:
                    # You can only set one image per embed... But you
                    #  can add multiple embeds :]
                    embed = discord.Embed(
                        color=discord.Colour.from_rgb(r=255, g=172, b=51),
                    )
                    embed.set_image(url=attachment.url)
                    embed_list.append(embed)
            else:
                if len(embed_list) == 0:
                    embed.set_field_at(
                        0,
                        name=embed.fields[0].name,
                        value=embed.fields[0].value
                        + f"\n\n(⚠️ +1 Unknown attachment "
                          f"({attachment.content_type}))"
                    )
                else:
                    embed_list[0].set_field_at(
                        0,
                        name=embed_list[0].fields[0].name,
                        value=embed_list[0].fields[0].value
                        + f"\n\n(⚠️ +1 Unknown attachment "
                          f"({attachment.content_type}))")
        except AttributeError:
            # if it is neither an image, video, application, nor
            #  recognised file type:
            if len(embed_list) == 0:
                embed.set_field_at(
                    0,
                    name=embed.fields[0].name,
                    value=embed.fields[0].value
                    + "\n\n(💔 +1 Unrecognized attachment type)"
                )
            else:
                embed_list[0].set_field_at(
                    0,
                    name=embed_list[0].fields[0].name,
                    value=embed_list[0].fields[0].value
                    + "\n\n(💔 +1 Unrecognized attachment type)"
                )
    if len(embed_list) == 0:
        embed_list.append(embed)

    # Add new starboard msg
    msg = await starboard_channel.send(
        f"💫 **{reaction.count}** | <#{message.channel.id}>",
        embeds=embed_list,
        allowed_mentions=discord.AllowedMentions.none(),
    )
    msg = typing.cast(GuildMessage, msg)  # sent to starboard channel = guild
    attachment_urls = ','.join(att.url for att in message.attachments)
    await log_to_guild(client, starboard_channel.guild,
                       f"{reaction.emoji} Starboard message {msg.jump_url} "
                       f"was created from {message.jump_url}. "
                       f"Content: \"\"\"{message.content[:1000]}\"\"\" and "
                       f"attachments: {attachment_urls}"
                       )
    # Add star reaction to original message to prevent message from
    #  being re-added to the starboard.
    await msg.add_reaction(reaction.emoji)
    await msg.add_reaction("❌")
    await add_to_local_starboard(client.async_rina_db, msg, message)


async def _update_starboard_message_score(
        client: Bot,
        guild_id: int,
        starboard_message: GuildMessage | int | None,
        original_message: GuildMessage | int | None,
        starboard_emoji: discord.PartialEmoji | discord.Emoji,
        downvote_init_value: int,
        original_message_channel: MessageableGuildChannel | int | None = None,
) -> None:
    """
    Update the score of the starboard message, or delete when downvoted.

    Checks a starboard message and original message's reactions and
    calculate its score. Negative scores can cause the message to
    be removed from the starboard.

    The starboard and original message may be ``None``, so long as not
    both of them are ``None``.

    :param client: The bot, to get the correct logging channel.
    :param starboard_message: The starboard message to update.
    :param starboard_emoji: The starboard upvote emoji (for scoring).
    :param downvote_init_value: The minimum required votes before a
     negative score can cause the message to be deleted.
    :raise ValueError: Both starboard_message and original_message
     were ``None``
    """
    # I need either:
    #  Original message id lets me retrieve starboard msg id.
    #  Starboard message id lets me retrieve original message data.
    #    That would contain both original message id and channel.
    try:
        orig_msg, star_msg = await _fetch_starboard_and_original_messages(
            client, guild_id,
            original_message, original_message_channel, starboard_message
        )
    except KeyError:
        # starboard message is invalid
        raise NotImplementedError()
    except IndexError:  # todo: Implement error handling
        # original message is invalid
        raise NotImplementedError()

    star_reacter_ids: list[int] = []
    reaction_total = 0
    # get message's starboard-reacters
    for reaction in orig_msg.reactions:
        if reaction.emoji == starboard_emoji:
            async for user in reaction.users():
                if user.id not in star_reacter_ids:
                    star_reacter_ids.append(user.id)

    # get starboard's starboard-reacters
    for reaction in star_msg.reactions:
        if reaction.emoji == starboard_emoji:
            async for user in reaction.users():
                if user.id not in star_reacter_ids:
                    star_reacter_ids.append(user.id)

    star_stat = len(star_reacter_ids)
    if getattr(client.user, "id") in star_reacter_ids:
        star_stat -= 1

    for reaction in star_msg.reactions:
        if reaction.emoji == '❌':
            # stars (exc. rina) + x'es - rina's x
            reaction_total = star_stat + reaction.count - reaction.me
            star_stat -= reaction.count - reaction.me

    # if more x'es than stars, and more than [15] reactions, remove
    #  the message.
    if star_stat < 0 and reaction_total >= downvote_init_value:
        await _delete_starboard_message(
            client, star_msg,
            f"{starboard_emoji} :x: Starboard message {star_msg.id} "
            f"was removed (from {orig_msg.id}) (too many downvotes! "
            f"Score: {star_stat}, Votes: {reaction_total})")
        return

    # update message to new star value
    parts = star_msg.content.split("**")
    parts[1] = str(star_stat)
    new_content = '**'.join(parts)
    # update embed message to keep most accurate nickname
    embeds = star_msg.embeds
    if isinstance(orig_msg.author, discord.Member):
        name = orig_msg.author.nick or orig_msg.author.name
    else:
        name = orig_msg.author.name
    embeds[0].set_author(
        name=f"{name}",
        url=f"https://original.poster/{orig_msg.author.id}/",
        icon_url=orig_msg.author.display_avatar.url
    )
    try:
        await star_msg.edit(content=new_content, embeds=embeds)
    except discord.HTTPException as ex:
        if ex.code == 429:
            # Too many requests; can't edit messages older than 1 hour
            #  more than x times an hour.
            return
        raise


async def _fetch_starboard_and_original_messages(
        client: Bot,
        guild_id: int,
        original_message: GuildMessage | int | None,
        original_message_channel: MessageableGuildChannel | int | None,
        starboard_message: GuildMessage | int | None,
) -> tuple[GuildMessage, GuildMessage]:
    """
    A helper function to retrieve the original and starboard messages.

    :param client: The bot, to fetch channels and messages.
    :param guild_id: The guild id of the starboard.
    :param original_message: The starboard message's original message.
    :param original_message_channel: The original message's channel.
    :param starboard_message: The starboard message.
    :return: A tuple of the original and starboard messages.
    :raise ValueError: If starboard message and original message
     are both ``None``. (propagated from _get_starboard_message_data)
    :raise KeyError: If the starboard message is not a known starboard
     message in the database. (propagated from
     _get_starboard_message_data)
    :raise IndexError: If the original message is not a known original
     message in the database. (propagated from
     _get_starboard_message_data)
    """
    orig_msg: GuildMessage
    star_msg: GuildMessage

    if (original_message is None
            or starboard_message is None
            or (original_message is not discord.Message
                and original_message_channel is None)):
        original_message, original_message_channel, starboard_message = \
            _get_starboard_message_data(
                guild_id,
                original_message,
                original_message_channel,
                starboard_message
            )

    if isinstance(original_message, int):
        if isinstance(original_message_channel, int):
            fetched_channel = await get_or_fetch_channel(
                client, original_message_channel)
            assert isinstance(
                fetched_channel, MessageableGuildChannel.__value__)
            channel = typing.cast(
                MessageableGuildChannel, fetched_channel)
        elif original_message_channel is None:
            raise NotImplementedError(str(original_message_channel))
        else:
            channel = original_message_channel

        orig_msg = await fetch_message_from_channel(
            channel, original_message)
    else:
        orig_msg = original_message

    if isinstance(starboard_message, int):
        starboard_channel: MessageableGuildChannel | None
        starboard_channel = client.get_guild_attribute(
            guild_id, AttributeKeys.starboard_channel)
        if starboard_channel is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.starboard, [AttributeKeys.starboard_channel])
        star_msg = await fetch_message_from_channel(
            starboard_channel, starboard_message)
    else:
        star_msg = starboard_message

    return orig_msg, star_msg


def _get_starboard_message_data(
        guild_id: int,
        original_message: GuildMessage | int | None,
        original_message_channel: MessageableGuildChannel | int | None,
        starboard_message: GuildMessage | int | None,
) -> tuple[GuildMessage | int, MessageableGuildChannel | int,
           GuildMessage | int]:
    """
    Get the ids of the starboard and original messages and channel.

    :param guild_id: The guild id of the starboard.
    :param original_message: The starboard message's original message.
    :param original_message_channel: The original message's channel.
    :param starboard_message: The starboard message.
    :return: A tuple of the original message, channel, and starboard message.
     If their input was ``None``, they are now ``int``.
    :raise ValueError: If starboard message and original message
     are both ``None``.
    :raise KeyError: If the starboard message is not a known starboard
     message in the database.
    :raise IndexError: If the original message is not a known original
     message in the database.
    """
    if original_message is None:
        if starboard_message is None:
            raise ValueError("original_message and starboard_message "
                             "cannot both be None")

        if isinstance(starboard_message, GuildMessage):
            starboard_message_id = starboard_message.id
        else:
            starboard_message_id = starboard_message

        orig_data = get_original_message_info(
            guild_id, starboard_message_id)
        if orig_data is None:
            raise IndexError(
                f"Couldn't get original message from starboard message! "
                f"Guild ID: {guild_id}, "
                f"Starboard message ID: {starboard_message_id}"
            )
        original_message = orig_data[1]
        if original_message_channel is None:
            original_message_channel = orig_data[0]

    elif starboard_message is None:
        if isinstance(original_message, GuildMessage):
            original_message_id = original_message.id
        else:
            original_message_id = original_message

        starboard_message = get_starboard_message_id(
            guild_id, original_message_id)
        if starboard_message is None:
            # not a starboard message? but it got here assumed as such?
            # I presume this could be possible if the original message has a
            #  rina reaction, but is no longer on the starboard
            #  (removed manually?).
            raise KeyError(
                f"Couldn't get starboard message from original message! "
                f"Guild ID: {guild_id}, "
                f"Original message ID: {original_message_id}"
            )

    if original_message_channel is None:
        if isinstance(starboard_message, GuildMessage):
            starboard_message_id = starboard_message.id
        else:
            starboard_message_id = starboard_message
        orig_data = get_original_message_info(guild_id, starboard_message_id)
        if orig_data is None:
            raise IndexError(
                f"Couldn't get original message from starboard message! "
                f"Guild ID: {guild_id}, "
                f"Starboard message ID: {starboard_message_id}"
            )
        original_message_channel = orig_data[0]

    return original_message, original_message_channel, starboard_message


async def _delete_starboard_message(
        client: Bot, starboard_message: GuildMessage, reason: str) -> None:
    """
    Handles custom starboard message deletion messages and preventing
    double logging messages when the bot removes a starboard message.

    :param client: The bot, to get the correct logging channel.
    :param starboard_message: The starboard message to delete.
    :param reason: The reason for deletion.
    """
    await log_to_guild(client, starboard_message.guild, reason)
    starboard_message_ids_marked_for_deletion.append(starboard_message.id)
    await starboard_message.delete()
    await delete_from_local_starboard(
        client.async_rina_db,
        starboard_message.guild.id,
        starboard_message.id
    )


async def _handle_starboard_create_or_update(
        client: Bot,
        reaction: discord.Reaction,
        message: GuildMessage,
        starboard_channel: discord.abc.Messageable,
        starboard_emoji: discord.PartialEmoji | discord.Emoji,
        channel_blacklist: list[discord.abc.Messageable],
        star_minimum: int,
        downvote_init_value: int,
):
    # fetched from payload.guild_id.channel_id.message_id, so guild_id
    # must've had a value
    if reaction.me:
        # check if this message is already in the starboard. If so,
        #  update it.
        starboard_message_id = get_starboard_message_id(
            message.guild.id, message.id)
        if starboard_message_id is None:
            return

        await _update_starboard_message_score(
            client, message.guild.id,
            starboard_message_id, message,
            starboard_emoji, downvote_init_value,
        )
        return

    elif reaction.count == star_minimum:
        if client.is_me(message.author):
            # can't starboard Rina's message
            return

        if message.channel in channel_blacklist:
            return

        try:
            # Try to add the initial starboard emoji to a starboarded
            #  message to prevent duplicate entries in starboard.
            await message.add_reaction(starboard_emoji)
        except discord.errors.Forbidden:
            # If "Reaction blocked", then maybe message author blocked
            #  Rina. Thus, I can't track if Rina added it to starboard
            #  already or not.
            await log_to_guild(
                client,
                message.guild.id,
                f'**:warning: Warning: **Couldn\'t add starboard '
                f'emoji to {message.jump_url}. They might have '
                f'blocked Rina...'
            )
            return

        await _send_starboard_message(
            client,
            message,
            starboard_channel,
            reaction
        )


async def fetch_message_from_channel(
        channel: MessageableGuildChannel, message_id: int
) -> GuildMessage:
    message = await channel.fetch_message(message_id)
    # The payload's guild is used to check if starboard is enabled.
    # Therefore, the original message must also be in a guild
    # (hence GuildMessage).
    assert message.guild is not None
    message = typing.cast(GuildMessage, message)
    return message


class Starboard(commands.Cog):
    def __init__(self, client: Bot):
        self.client: Bot = client

    @commands.Cog.listener()
    async def on_raw_reaction_add(
            self, payload: discord.RawReactionActionEvent
    ):
        if payload.guild_id is None:
            return
        if payload.member is None:
            return
        if not self.client.is_module_enabled(payload.guild_id,
                                             ModuleKeys.starboard):
            return

        star_channel: MessageableGuildChannel | None
        star_minimum: int | None
        channel_blacklist: list[discord.abc.Messageable] | None
        starboard_emoji: discord.Emoji | None
        downvote_init_value: int | None
        (star_channel, star_minimum, channel_blacklist,
         starboard_emoji, downvote_init_value) = \
            self.client.get_guild_attribute(
                payload.guild_id,
                AttributeKeys.starboard_channel,
                AttributeKeys.starboard_minimum_upvote_count,
                AttributeKeys.starboard_blacklisted_channels,
                AttributeKeys.starboard_upvote_emoji,
                AttributeKeys.starboard_minimum_vote_count_for_downvote_delete
        )

        if (star_channel is None
                or star_minimum is None
                or channel_blacklist is None
                or starboard_emoji is None
                or downvote_init_value is None):
            missing = [key for key, value in {
                AttributeKeys.starboard_channel:
                    star_channel,
                AttributeKeys.starboard_minimum_upvote_count:
                    star_minimum,
                AttributeKeys.starboard_blacklisted_channels:
                    channel_blacklist,
                AttributeKeys.starboard_upvote_emoji:
                    starboard_emoji,
                AttributeKeys.starboard_minimum_vote_count_for_downvote_delete:
                    downvote_init_value
            }.items()
                if value is None]
            raise MissingAttributesCheckFailure(ModuleKeys.starboard, missing)

        if self.client.is_me(payload.member) or \
                (getattr(payload.emoji, "id", None) != starboard_emoji.id and
                 getattr(payload.emoji, "name", None) != "❌"):
            # Only run starboard code if the reactions tracked are actually
            #  starboard emojis (or the downvote emoji).
            return

        # get the message id from payload.message_id through the channel
        #  (with payload.channel_id) (oof lengthy process)
        ch = self.client.get_channel(payload.channel_id)
        if (ch is None  # channel not in cache?
                or not isinstance(ch, MessageableGuildChannel.__value__)):
            return
        ch = typing.cast(MessageableGuildChannel, ch)

        try:
            message = await fetch_message_from_channel(ch, payload.message_id)
        except discord.errors.NotFound:
            # likely caused by someone removing a PluralKit message by
            #  reacting with the :x: emoji.

            if payload.emoji.name == "❌":
                return

            # noinspection LongLine
            broken_link = f"https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}"  # noqa
            await log_to_guild(
                self.client,
                self.client.get_guild(payload.guild_id),
                f'**:warning: Warning: **Couldn\'t find channel '
                f'{payload.channel_id} (<#{payload.channel_id}>) or '
                f'message {payload.message_id}!\n'
                f'Potentially broken link: {broken_link}\n'
                f'This is likely caused by someone removing a PluralKit '
                f'message by reacting with the :x: emoji.\n'
                f'\n'
                f"In this case, the user reacted with a "
                f"'{repr(payload.emoji)}' emoji"
            )
            return

        if message.channel.id == star_channel.id:
            if not self.client.is_me(message.author):
                # only needs to update the message if it's a rina
                #  starboard message of course...
                return

            # fetch original message, so we can get the original author.
            starboard_original_message: discord.Message | None = \
                await _fetch_starboard_original_message(
                    self.client, message, starboard_emoji)
            if (starboard_original_message is not None and
                    starboard_original_message.author.id == payload.user_id and
                    payload.emoji.name == "❌"):
                # todo: add starboard original message author to database?
                await _delete_starboard_message(
                    self.client,
                    message,
                    f"{starboard_emoji} :x: Starboard message {message.id} "
                    f"was removed (from {starboard_original_message.id}) "
                    f"(original author downvoted the starboard message!)"
                )
                return

            if is_starboard_message(payload.guild_id, payload.message_id):
                await _update_starboard_message_score(
                    self.client, message.guild.id,
                    message, starboard_original_message,
                    starboard_emoji,
                    downvote_init_value,
                )
            return

        # The reaction's parent message was not sent in the starboard channel.
        for reaction in message.reactions:
            if reaction.emoji == starboard_emoji:
                await _handle_starboard_create_or_update(
                    self.client, reaction, message, star_channel,
                    starboard_emoji, channel_blacklist, star_minimum,
                    downvote_init_value
                )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(
            self,
            payload: discord.RawReactionActionEvent
    ):
        if payload.guild_id is None:
            return
        if not self.client.is_module_enabled(payload.guild_id,
                                             ModuleKeys.starboard):
            return

        star_channel: discord.abc.Messageable | None
        starboard_emoji: discord.Emoji | None
        downvote_init_value: int | None
        star_channel, starboard_emoji, downvote_init_value = \
            self.client.get_guild_attribute(
                payload.guild_id,
                AttributeKeys.starboard_channel,
                AttributeKeys.starboard_upvote_emoji,
                AttributeKeys.starboard_minimum_vote_count_for_downvote_delete
            )

        if (star_channel is None
                or starboard_emoji is None
                or downvote_init_value is None):
            missing = [key for key, value in {
                AttributeKeys.starboard_channel: star_channel,
                AttributeKeys.starboard_upvote_emoji: starboard_emoji,
                AttributeKeys.starboard_minimum_vote_count_for_downvote_delete:
                    downvote_init_value}.items()
                if value is None]
            raise MissingAttributesCheckFailure(ModuleKeys.starboard, missing)

        if payload.emoji != starboard_emoji and payload.emoji.name != "❌":
            # only run starboard code if the reactions tracked are actually
            #  starboard emojis (or the downvote emoji)
            return

        # message is starboard_msg
        if is_starboard_message(payload.guild_id, payload.message_id):
            await _update_starboard_message_score(
                self.client, payload.guild_id,
                payload.message_id, None,
                starboard_emoji, downvote_init_value
            )
            return

        # starboard_reactions = [r for r in message.reactions
        #                        if r.emoji == starboard_emoji and r.me]
        # if starboard_reactions:

        orig_data = get_starboard_message_id(
            payload.guild_id, payload.message_id)
        if orig_data:
            # the message is a starboard's original message
            await _update_starboard_message_score(
                self.client, payload.guild_id,
                None, payload.message_id,
                starboard_emoji, downvote_init_value,
                original_message_channel=payload.channel_id
            )

    @commands.Cog.listener()
    async def on_raw_message_delete(
            self,
            message_payload: discord.RawMessageDeleteEvent
    ):
        # can raise discord.NotFound and discord.Forbidden.

        if not self.client.is_module_enabled(message_payload.guild_id,
                                             ModuleKeys.starboard):
            return
        assert message_payload.guild_id is not None

        star_channel: MessageableGuildChannel | None
        starboard_emoji: discord.Emoji | None
        star_channel, starboard_emoji = self.client.get_guild_attribute(
            message_payload.guild_id,
            AttributeKeys.starboard_channel,
            AttributeKeys.starboard_upvote_emoji
        )

        if star_channel is None or starboard_emoji is None:
            missing = [key for key, value in {
                AttributeKeys.starboard_channel: star_channel,
                AttributeKeys.starboard_upvote_emoji: starboard_emoji}.items()
                if value is None]
            raise MissingAttributesCheckFailure(ModuleKeys.starboard, missing)

        # noinspection LongLine
        if message_payload.message_id in starboard_message_ids_marked_for_deletion:  # noqa
            # marked messages is a global variable
            # this prevents having two 'message deleted' logs for
            # manual deletion of starboard message
            starboard_message_ids_marked_for_deletion.remove(
                message_payload.message_id)
            return
        if message_payload.channel_id == star_channel.id:
            # check if the deleted message is a starboard message;
            #  if so, log it at starboard message deletion.
            await log_to_guild(
                self.client,
                star_channel.guild,
                f"{starboard_emoji} :x: Starboard message was removed "
                f"(from {message_payload.message_id}) "
                f"(Starboard message was deleted manually)."
            )
            await delete_from_local_starboard(
                self.client.async_rina_db,
                message_payload.guild_id,
                message_payload.message_id
            )
            return

        # check if this message's is in the starboard. If so, delete it
        starboard_msg_id = get_starboard_message_id(
            message_payload.guild_id, message_payload.message_id)
        if starboard_msg_id is None:
            return

        try:
            starboard_msg = await fetch_message_from_channel(
                star_channel, starboard_msg_id)
        except discord.HTTPException:
            return
        # can raise discord.NotFound and discord.Forbidden.

        try:
            image = starboard_msg.embeds[0].image.url
        except AttributeError:
            image = ""

        partial_channel = discord.PartialMessage(
            channel=star_channel, id=message_payload.message_id)
        msg_link = partial_channel.jump_url

        await _delete_starboard_message(
            self.client,
            starboard_msg,
            f"{starboard_emoji} :x: Starboard message "
            f"{starboard_msg.id} was removed (from {msg_link}) "
            f"(original message was removed (this starboard message's "
            f"linked id matched the removed message's)).\n"
            f"Content: \"\"\"{starboard_msg.embeds[0].description}\"\"\" and "
            f"attachment: {image}")
        return

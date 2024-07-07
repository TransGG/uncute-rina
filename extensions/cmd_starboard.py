from import_modules import (
    discord, commands,
    mktime, datetime, timezone, # to track starboard refresh timestamps TODO: make it not use unix timestamps but just datetimes; and get message send time for embed because cool (serves no real purpose)
    asyncio, # for sleep(1) while waiting for other starboard message fetching function instance. See get_or_fetch_starboard_messages()
    typing # for type checking
)
from resources.utils.utils import log_to_guild # to log starboard addition/removal
from resources.customs.bot import Bot


starboard_message_ids_marked_for_deletion = []
local_starboard_message_list_refresh_timestamp = 0 # TODO: make this not unix :P just use datetime
STARBOARD_REFRESH_DELAY = 1000
local_starboard_message_list: list[discord.Message] = []
busy_updating_starboard_messages = False


async def delete_starboard_message(client: Bot, starboard_message: discord.Message, reason: str) -> None:
    """
    Handles custom starboard message deletion messages and preventing double logging messages when the bot removes a starboard message.

    ### Parameters
    client: :class:`Bot`
        The bot, to get the correct logging channel.
    starboard_message: :class:`discord.Message`
        The starboard message to delete.
    reason: :class:`str`
        The reason of deletion.
    """
    await log_to_guild(client, starboard_message.guild, reason)
    starboard_message_ids_marked_for_deletion.append(starboard_message.id)
    await starboard_message.delete()
    for i in range(len(local_starboard_message_list)):
        if local_starboard_message_list[i].id == starboard_message.id:
            del local_starboard_message_list[i]
            break

async def fetch_starboard_original_message(client: Bot, starboard_message: discord.Message, starboard_emoji: discord.Emoji) -> discord.Message | None:
    """
    Uses the 'jump to original' link in a starboard message to fetch its original author's message.

    ### Parameters
    client: :class:`Bot`
        The bot, to get the correct logging channel.
    starboard_message: :class:`discord.Message`
        The starboard message to get the original message of.
    starboard_emoji: :class:`discord.Emoji`
        The starboard upvote emoji, used in logging messages.

    ### Returns
    The original author's message or None if not found (no permission, or can't be found). If the original message was deleted, it deletes its starboard message too.
    """
    # find original message
    if len(starboard_message.embeds) == 0:
        await log_to_guild(client, starboard_message.guild, f"{starboard_emoji} :x: Starboard message {starboard_message.id} was ignored (from {message_id}) (starboard's message had no embeds)")
        return
    text = starboard_message.embeds[0].fields[0].value ## "[Jump!]({msgLink})"
    link = text.split("(")[1]
    # Initial attempt to use [:-1] to remove the final ")" character doesn't work if there are unknown
    # files in the original starboard message because rina mentions them in the starboard msg after the
    # [Jump] link, adding "\n[...]" so ye.
    link = link.split(")",1)[0]
    #      0    1      2           3          4: guild_id          5: channel_id         6: message_id
    #    https:/ /discord.com / channels / 985931648094834798 / 1006682505149169694 / 1014887159485968455
    guild_id, channel_id, message_id = [int(i) for i in link.split("/")[4:]]
    try:
        ch = client.get_channel(channel_id)
        original_message = await ch.fetch_message(message_id)
    except discord.NotFound:
        # if original message removed, remove starboard message
        delete_starboard_message(client, starboard_message, f"{starboard_emoji} :x: Starboard message {starboard_message.id} was removed (from {message_id}) (original message could not be found)")
        return
    except discord.errors.Forbidden:
        await log_to_guild(client, starboard_message.guild, f":warning: Couldn't fetch starboard message [{starboard_message.id}]({starboard_message.jump_url}) from this channel ({ch.mention})!")
        return
    return original_message

async def update_starboard_message_score(client: Bot, starboard_message: discord.Message, starboard_emoji: discord.Emoji, downvote_init_value: int) -> None:
    """
    Check a starboard message and original message's reactions and calculate its score. Negative scores can cause the message to be removed from the starboard.
    
    ### Parameters
    client: :class:`Bot`
        The bot, to get the correct logging channel.
    starboard_message: :class:`discord.Message`
        The starboard message to update.
    starboard_emoji: :class:`discord.Emoji`
        The starboard upvote emoji (for scoring)
    downvote_init_value: :class:`int`
        The minimum required votes before a negative score can cause the message to be deleted.
    """
    original_message: discord.Message = await fetch_starboard_original_message(client, starboard_message, starboard_emoji)
    if original_message is None:
        return

    star_reacters = []
    reactionTotal = 0
    # get message's starboard-reacters
    for reaction in original_message.reactions:
        if reaction.is_custom_emoji():
            if getattr(reaction.emoji, "id", None) == starboard_emoji.id:
                async for user in reaction.users():
                    if user.id not in star_reacters:
                        star_reacters.append(user.id)

    # get starboard's starboard-reacters
    for reaction in starboard_message.reactions:
        if reaction.is_custom_emoji():
            if getattr(reaction.emoji, "id", None) == starboard_emoji.id:
                async for user in reaction.users():
                    if user.id not in star_reacters:
                        star_reacters.append(user.id)

    star_stat = len(star_reacters)
    if client.user.id in star_reacters:
        star_stat -= 1

    for reaction in starboard_message.reactions:
        if reaction.emoji == '❌':
            reactionTotal = star_stat + reaction.count - reaction.me # stars (exc. rina) + x'es - rina's x
            star_stat -= reaction.count - reaction.me

    #if more x'es than stars, and more than [15] reactions, remove message
    if star_stat < 0 and reactionTotal >= downvote_init_value:
        await delete_starboard_message(client, starboard_message, f"{starboard_emoji} :x: Starboard message {starboard_message.id} was removed (from {original_message.id}) (too many downvotes! Score: {star_stat}, Votes: {reactionTotal})")
        return

    # update message to new star value
    parts = starboard_message.content.split("**")
    parts[1] = str(star_stat)
    new_content = '**'.join(parts)
    # update embed message to keep most accurate nickname
    embeds = starboard_message.embeds
    if isinstance(original_message.author, discord.Member):
        name = original_message.author.nick or original_message.author.name
    else:
        name = original_message.author.name
    embeds[0].set_author(
        name=f"{name}",
        url=f"https://original.poster/{original_message.author.id}/",
        icon_url=original_message.author.display_avatar.url
    )
    try:
        await starboard_message.edit(content=new_content, embeds=embeds)
    except discord.HTTPException as ex:
        if ex.code == 429: # too many requests; can't edit messages older than 1 hour more than x times an hour.
            return
        raise

async def get_or_fetch_starboard_messages(starboard_channel: discord.abc.GuildChannel | discord.abc.PrivateChannel | discord.Thread | None) -> list[discord.Message]:
    """
    Fetch list of all starboard messages, unless it is already fetching: then it waits until the 
    other instance of the fetching function is done and retrieves the cached list. The list is 
    stored for STARBOARD_REFRESH_DELAY seconds.

    ### Parameters
    starboard_channel: :class:`discord.abc.GuildChannel` | :class:`discord.abc.PrivateChannel` | :class:`discord.Thread` | `None`
        The starboard channel to fetch messages from.
    
    ### Returns
    :class:`list[discord.Message]`:
        A list of starboard messages (send by the bot) in the starboard channel.
    """
    global busy_updating_starboard_messages, local_starboard_message_list, local_starboard_message_list_refresh_timestamp
    if not busy_updating_starboard_messages and mktime(datetime.now(timezone.utc).timetuple()) - local_starboard_message_list_refresh_timestamp > STARBOARD_REFRESH_DELAY: # refresh once every 1000 seconds
        busy_updating_starboard_messages = True
        messages: list[discord.Message] = []
        async for star_message in starboard_channel.history(limit=1000):
            messages.append(star_message)
        local_starboard_message_list = messages
        local_starboard_message_list_refresh_timestamp = mktime(datetime.now(timezone.utc).timetuple())
        busy_updating_starboard_messages = False
    while busy_updating_starboard_messages:
        # wait until not busy anymore
        await asyncio.sleep(1)
    return local_starboard_message_list


class Starboard(commands.Cog):
    def __init__(self, client: Bot):
        global RinaDB
        self.client: Bot = client
        RinaDB = client.RinaDB

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id in [None, self.client.custom_ids["staff_server_id"]]:
            return # TODO: implement server-dependent module toggling
        _star_channel, star_minimum, channel_blacklist, starboard_emoji_id, downvote_init_value = await self.client.get_guild_info(
            payload.guild_id, "starboardChannel", "starboardCountMinimum", "starboardBlacklistedChannels", "starboardEmoji", "starboardDownvoteInitValue")
        if payload.member.id == self.client.user.id or \
                (getattr(payload.emoji, "id",   None) != starboard_emoji_id and
                 getattr(payload.emoji, "name", None) != "❌"):
            # only run starboard code if the reactions tracked are actually starboard emojis (or the downvote emoji)
            return

        #get the message id from payload.message_id through the channel (with payload.channel_id) (oof lengthy process)
        try:
            ch = self.client.get_channel(payload.channel_id)
            message = await ch.fetch_message(payload.message_id)
        except discord.errors.NotFound:
            # likely caused by someone removing a PluralKit message by reacting with the :x: emoji.

            if payload.emoji.name == "❌":
                return

            await log_to_guild(
                self.client, self.client.get_guild(payload.guild_id),
                f'**:warning: Warning: **Couldn\'t find channel {payload.channel_id} (<#{payload.channel_id}>) or message {payload.message_id}!\n'
                f'Potentially broken link: https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}\n'
                f'This is likely caused by someone removing a PluralKit message by reacting with the :x: emoji.\n'
                f'\n'
                f"In this case, the user reacted with a '{repr(payload.emoji)}' emoji")

        # print(repr(message.guild.id), repr(self.client.custom_ids["staff_server_id"]), message.guild.id == self.client.custom_ids["staff_server_id"])
        star_channel = self.client.get_channel(_star_channel)
        starboard_emoji = self.client.get_emoji(starboard_emoji_id)

        if message.channel.id == star_channel.id:
            if message.author.id != self.client.user.id:
                return # only needs to update the message if it's a rina starboard message of course...

            starboard_original_message: discord.Message | None = await fetch_starboard_original_message(self.client, message, starboard_emoji)
            if (starboard_original_message is not None and 
                    starboard_original_message.author.id == payload.user_id and 
                    payload.emoji.name == "❌"):
                await delete_starboard_message(self.client, message, f"{starboard_emoji} :x: Starboard message {message.id} was removed (from {starboard_original_message.id}) (original author downvoted the starboard message!)")
                return

            if len(message.embeds) > 0:
                await update_starboard_message_score(self.client, message, starboard_emoji, downvote_init_value)
            return

        for reaction in message.reactions:
            if getattr(reaction.emoji, "id", None) == starboard_emoji_id:
                if reaction.me:
                    # check if this message is already in the starboard. If so, update it
                    starboard_messages = await get_or_fetch_starboard_messages(star_channel)
                    for star_message in starboard_messages:
                        for embed in star_message.embeds:
                            if embed.footer.text == str(message.id):
                                await update_starboard_message_score(self.client, star_message, starboard_emoji, downvote_init_value)
                                return
                    return
                elif reaction.count == star_minimum:
                    if message.author == self.client.user:
                        #can't starboard Rina's message
                        return
                    if message.channel.id in channel_blacklist:
                        return

                    try:
                        # Try to add the initial starboard emoji to starboarded message
                        # to prevent duplicate entries in starboard.
                        await message.add_reaction(starboard_emoji)
                    except discord.errors.Forbidden:
                        # If "Reaction blocked", then maybe message author blocked Rina.
                        # Thus, I can't track if Rina added it to starboard already or not.
                        await log_to_guild(self.client, self.client.get_guild(payload.guild_id), 
                                     f'**:warning: Warning: **Couldn\'t add starboard emoji to {message.jump_url}. They might have blocked Rina...')
                        return

                    msgLink = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
                    embed = discord.Embed(
                            color=discord.Colour.from_rgb(r=255, g=172, b=51),
                            title='',
                            description=f"{message.content}",
                            timestamp=datetime.now()
                        )
                    embed.add_field(name="Source", value=f"[Jump!]({msgLink})")
                    embed.set_footer(text=f"{message.id}")
                    if isinstance(message.author, discord.Member):
                        name = message.author.nick or message.author.name
                    else:
                        name = message.author.name
                    embed.set_author(
                            name=f"{name}",
                            url=f"https://original.poster/{message.author.id}/",
                            icon_url=message.author.display_avatar.url
                    )
                    embed_list = []
                    for attachment in message.attachments:
                        try:
                            if attachment.content_type.split("/")[0] == "image": #is image or GIF
                                if len(embed_list) == 0:
                                    embed.set_image(url=attachment.url)
                                    embed_list = [embed]
                                else:
                                    # can only set one image per embed... But you can add multiple embeds :]
                                    embed = discord.Embed(
                                        color = discord.Colour.from_rgb(r=255, g=172, b=51),
                                    )
                                    embed.set_image(url=attachment.url)
                                    embed_list.append(embed)
                            else:
                                if len(embed_list) == 0:
                                    embed.set_field_at(0,
                                                       name = embed.fields[0].name,
                                                       value = embed.fields[0].value + f"\n\n(⚠️ +1 Unknown attachment ({attachment.content_type}))")
                                else:
                                    embed_list[0].set_field_at(0,
                                                               name=embed_list[0].fields[0].name,
                                                               value=embed_list[0].fields[0].value + f"\n\n(⚠️ +1 Unknown attachment ({attachment.content_type}))")
                        except AttributeError:
                            # if it is neither an image, video, application, or recognised file type:
                            if len(embed_list) == 0:
                                embed.set_field_at(0,
                                                   name=embed.fields[0].name,
                                                   value=embed.fields[0].value + f"\n\n(💔 +1 Unrecognized attachment type)")
                            else:
                                embed_list[0].set_field_at(0,
                                                           name=embed_list[0].fields[0].name,
                                                           value=embed_list[0].fields[0].value + f"\n\n(💔 +1 Unrecognized attachment type)")
                    if len(embed_list) == 0:
                        embed_list.append(embed)

                    msg = await star_channel.send(
                            f"💫 **{reaction.count}** | <#{message.channel.id}>",
                            embeds=embed_list,
                            allowed_mentions=discord.AllowedMentions.none(),
                        )
                    await log_to_guild(self.client, star_channel.guild,
                                 f"{starboard_emoji} Starboard message {msg.jump_url} was created from {message.jump_url}. "
                                 f"Content: \"\"\"{message.content[:1000]}\"\"\" and attachments: {[x.url for x in message.attachments]}")
                    # add new starboard msg
                    await msg.add_reaction(starboard_emoji)
                    await msg.add_reaction("❌")
                    local_starboard_message_list.append(msg)
                    # add star reaction to original message to prevent message from being re-added to the starboard

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id in [None, self.client.custom_ids["staff_server_id"]]:
            return
        _star_channel, starboard_emoji_id, downvote_init_value = await self.client.get_guild_info(payload.guild_id, "starboardChannel", "starboardEmoji", "starboardDownvoteInitValue")
        if getattr(payload.emoji, "id", None) != starboard_emoji_id and \
            getattr(payload.emoji, "name", None) != "❌":
            # only run starboard code if the reactions tracked are actually starboard emojis (or the downvote emoji)
            return
        #get the message id from payload.message_id through the channel (with payload.channel_id) (oof lengthy process)
        ch = self.client.get_channel(payload.channel_id)
        message = await ch.fetch_message(payload.message_id)

        
        star_channel = self.client.get_channel(_star_channel)
        starboard_emoji = self.client.get_emoji(starboard_emoji_id)

        if message.channel.id == star_channel.id:
            if len(message.embeds) > 0:
                await update_starboard_message_score(self.client, message, starboard_emoji, downvote_init_value)
            return

        for reaction in message.reactions:
            if getattr(reaction.emoji, "id", None) == starboard_emoji_id:
                if reaction.me:
                    # check if this message is already in the starboard. If so, update it
                    starboard_messages = await get_or_fetch_starboard_messages(star_channel)
                    for star_message in starboard_messages:
                        for embed in star_message.embeds:
                            if embed.footer.text == str(message.id):
                                await update_starboard_message_score(self.client, star_message, starboard_emoji, downvote_init_value)
                                return

    @commands.Cog.listener()
    async def on_raw_message_delete(self, message_payload: discord.RawMessageDeleteEvent):
        if message_payload.guild_id in [None, self.client.custom_ids["staff_server_id"]]:
            return
        _star_channel, starboard_emoji_id = await self.client.get_guild_info(message_payload.guild_id, "starboardChannel", "starboardEmoji")
        star_channel = self.client.get_channel(_star_channel)
        starboard_emoji = self.client.get_emoji(starboard_emoji_id)

        if message_payload.message_id in starboard_message_ids_marked_for_deletion: #global variable
            # this prevents having two 'message deleted' logs for manual deletion of starboard message
            starboard_message_ids_marked_for_deletion.remove(message_payload.message_id)
            return
        if message_payload.channel_id == star_channel.id:
            # check if the deleted message is a starboard message; if so, log it at starboard message deletion
            await log_to_guild(self.client, star_channel.guild, 
                         f"{starboard_emoji} :x: Starboard message was removed (from {message_payload.message_id}) "
                         f"(Starboard message was deleted manually).")
            return
        elif message_payload.channel_id != star_channel.id:
            # check if this message's is in the starboard. If so, delete it
            starboard_messages = await get_or_fetch_starboard_messages(star_channel)
            for star_message in starboard_messages:
                for embed in star_message.embeds:
                    if embed.footer.text == str(message_payload.message_id):
                        try:
                            image = star_message.embeds[0].image.url
                        except AttributeError:
                            image = ""
                        try:
                            msg_link = str(message_payload.message_id)+"  |  "+(await self.client.get_channel(message_payload.channel_id).fetch_message(message_payload.message_id)).jump_url
                        except discord.NotFound:
                            msg_link = str(message_payload.message_id)+" (couldn't get jump link)"
                        
                        await delete_starboard_message(
                            self.client,
                            star_message,
                            f"{starboard_emoji} :x: Starboard message {star_message.id} was removed (from {msg_link}) "
                            f"(original message was removed (this starboard message's linked id matched the removed message's)). "
                            f"Content: \"\"\"{star_message.embeds[0].description}\"\"\" and attachment: {image}")
                        return


async def setup(client):
    await client.add_cog(Starboard(client))

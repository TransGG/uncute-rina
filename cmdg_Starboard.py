from Uncute_Rina import *

starboard_emoji = "<:TPA_Trans_Starboard:992493515714068480>"#"<:upvote:989259317146439690>"
starboard_emoji_id = int(starboard_emoji.split(":")[-1].replace(">",""))
# starboard_emoji_id = 992493515714068480

messageIdMarkedForDeletion = []

class Starboard(commands.Cog):
    def __init__(self, client: Bot):
        global RinaDB
        self.client = client
        RinaDB = client.RinaDB

    async def updateStat(self, star_message):
        # find original message
        text = star_message.embeds[0].fields[0].value ## "[Jump!]({msgLink})"
        link = text.split("(")[1][:-1]
        #    https: 0 / 1 / discord.com 2 / channels 3 / 985931648094834798 4 / 1006682505149169694 5 / 1014887159485968455 6
        guild_id, channel_id, message_id = [int(i) for i in link.split("/")[4:]]
        try:
            ch = self.client.get_channel(channel_id)
            original_message = await ch.fetch_message(message_id)
        except discord.NotFound:
            # if original message removed, remove starboard message
            await logMsg(star_message.guild, f"{starboard_emoji} :x: Starboard message {star_message.id} was removed (from {message_id}) (original message could not be found)")
            messageIdMarkedForDeletion.append(star_message.id)
            await star_message.delete()
            return

        star_stat_message = 0
        reactionTotal = 0
        # get message stars excluding Rina's
        for reaction in original_message.reactions:
            try:
                if reaction.emoji.id == starboard_emoji_id:
                    star_stat_message += reaction.count
                    if reaction.me:
                        star_stat_message -= 1
            except AttributeError: #is not a custom emoji
                pass

        star_stat_starboard = 0
        # get starboard stars excluding Rina's
        for reaction in star_message.reactions:
            try:
                if reaction.emoji.id == starboard_emoji_id:
                    star_stat_starboard += reaction.count
                    if reaction.me:
                        star_stat_starboard -= 1
            except AttributeError: #is not a custom emoji
                pass

        if star_stat_starboard > star_stat_message:
            star_stat = star_stat_starboard
        else:
            star_stat = star_stat_message

        for reaction in star_message.reactions:
            if reaction.emoji == '❌':
                reactionTotal = star_stat + reaction.count - 1 # stars (exc. rina) + x'es - rina's x
                star_stat -= reaction.count
                if reaction.me:
                    star_stat += 1

        #if more x'es than stars, and more than 15 reactions, remove message
        if star_stat < 0 and reactionTotal > 10:
            await logMsg(star_message.guild, f"{starboard_emoji} :x: Starboard message {star_message.id} was removed (from {message_id}) (too many downvotes! Score: {star_stat}, Votes: {reactionTotal})")
            await star_message.delete()
            return

        # update message to new star value
        parts = star_message.content.split("**")
        parts[1] = str(star_stat)
        new_content = '**'.join(parts)
        # update embed message to keep most accurate nickname
        embeds = star_message.embeds
        if isinstance(original_message.author, discord.Member):
            name = original_message.author.nick or original_message.author.name
        else:
            name = original_message.author.name
        embeds[0].set_author(
            name=f"{name}",
            url=f"https://original.poster/{original_message.author.id}/",
            icon_url=original_message.author.display_avatar.url
        )
        await star_message.edit(content=new_content, embeds=embeds)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.id == self.client.user.id or \
                (payload.emoji.id != starboard_emoji_id and
                 payload.emoji.name != "❌"):
            # only run starboard code if the reactions tracked are actually starboard emojis (or the downvote emoji)
            return

        #get the message id from payload.message_id through the channel (with payload.channel_id) (oof lengthy process)
        try:
            ch = self.client.get_channel(payload.channel_id)
            message = await ch.fetch_message(payload.message_id)
        except discord.errors.NotFound:
            await logMsg(
                self.client.get_guild(payload.guild_id),
                f'**:warning: Warning: **Couldn\'t find channel {payload.channel_id} (<#{payload.channel_id}>) or message {payload.message_id}!\n'
                f'Potentially broken link: https://discord.com/channels/{payload.guild_id}/{payload.channel_id}/{payload.message_id}\n'
                f'This is likely caused by someone removing a PluralKit message by reacting with the :x: emoji.')
            return

        collection = RinaDB["guildInfo"]
        query = {"guild_id": message.guild.id}
        guild = collection.find_one(query)
        if guild is None:
            # can't send logging message, because we have no clue what channel that's supposed to be Xd
            debug("Not enough data is configured to work with the starboard. Please fix this with `/editguildinfo`!",color="red")
            return
        try:
            _star_channel = guild["starboardChannel"]
            star_minimum = guild["starboardCountMinimum"]
        except KeyError:
            raise KeyError("Not enough data is configured to do add an item to the starboard, because idk what channel i need to look in, and what minimum stars a message needs before it can be added to the starboard! Please fix this with `/editguildinfo`!")
        star_channel = self.client.get_channel(_star_channel)

        if message.channel.id == star_channel.id:
            await self.updateStat(message)
            return

        for reaction in message.reactions:
            try:
                reaction.emoji.id
            except AttributeError:
                return
            if reaction.emoji.id == starboard_emoji_id:
                if reaction.me:
                    # check if this message is already in the starboard. If so, update it
                    async for star_message in star_channel.history(limit=200):
                        for embed in star_message.embeds:
                            if embed.footer.text == str(message.id):
                                await self.updateStat(star_message)
                                return
                    return
                elif reaction.count == star_minimum:
                    if message.author == self.client.user:
                        #can't starboard Rina's message
                        return
                    try:
                        # Try to add the initial starboard emoji to starboarded message
                        # to prevent duplicate entries in starboard.
                        await message.add_reaction(starboard_emoji)
                    except discord.errors.Forbidden:
                        # If "Reaction blocked", then maybe message author blocked Rina.
                        # Thus, I can't track if Rina added it to starboard already or not.
                        await logMsg(self.client.get_guild(payload.guild_id), f'**:warning: Warning: **Couldn\'t add starboard emoji to {message.jump_url}. They might have blocked Rina...')
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
                        print(repr(attachment.content_type), type(attachment.content_type))
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
                    await logMsg(star_channel.guild, f"{starboard_emoji} Starboard message {msg.jump_url} was created from {message.jump_url}. Content: \"\"\"{message.content}\"\"\" and attachments: {[x.url for x in message.attachments]}")
                    # add new starboard msg
                    await msg.add_reaction(starboard_emoji)
                    await msg.add_reaction("❌")
                    # add star reaction to original message to prevent message from being re-added to the starboard

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.emoji.id != starboard_emoji_id and payload.emoji.name != "❌":
            # only run starboard code if the reactions tracked are actually starboard emojis (or the downvote emoji)
            return
        #get the message id from payload.message_id through the channel (with payload.channel_id) (oof lengthy process)
        ch = self.client.get_channel(payload.channel_id)
        message = await ch.fetch_message(payload.message_id)

        collection = RinaDB["guildInfo"]
        query = {"guild_id": message.guild.id}
        guild = collection.find_one(query)
        if guild is None:
            # can't send logging message, because we have no clue what channel that's supposed to be Xd
            debug("Not enough data is configured to work with the starboard! Please fix this with `/editguildinfo`!",color="red")
            return
        try:
            _star_channel = guild["starboardChannel"]
        except KeyError:
            raise KeyError("Not enough data is configured to .. remove a star from an item on the starboard because idk what channel i need to look in! Please fix this with `/editguildinfo`!")
        star_channel = self.client.get_channel(_star_channel)

        if message.channel.id == star_channel.id:
            await self.updateStat(message)
            return

        for reaction in message.reactions:
            if str(reaction.emoji) == starboard_emoji:
                if reaction.me:
                    # check if this message is already in the starboard. If so, update it
                    async for star_message in star_channel.history(limit=500):
                        for embed in star_message.embeds:
                            if embed.footer.text == str(message.id):
                                await self.updateStat(star_message)
                                return

    @commands.Cog.listener()
    async def on_raw_message_delete(self, message_payload):
        collection = RinaDB["guildInfo"]
        query = {"guild_id": message_payload.guild_id}
        guild = collection.find_one(query)
        if guild is None:
            debug("Not enough data is configured to work with the starboard! Please fix this with `/editguildinfo`!",color="red")
            return
        try:
            _star_channel = guild["starboardChannel"]
        except KeyError:
            raise KeyError("Not enough data is configured to .. check starboard for a message matching the deleted message's ID, because idk what channel i need to look in! Please fix this with `/editguildinfo`!")
        star_channel = self.client.get_channel(_star_channel)

        if message_payload.message_id in messageIdMarkedForDeletion: #global variable
            # this prevents having two 'message deleted' logs
            messageIdMarkedForDeletion.remove(message_payload.message_id)
            return
        if message_payload.channel_id == star_channel.id:
            # check if the deleted message is a starboard message; if so, log it at starboard message deletion
            await logMsg(star_channel.guild, f"{starboard_emoji} :x: Starboard message was removed (from {message_payload.message_id}) (Starboard message was deleted manually).")
            return
        elif message_payload.channel_id != star_channel.id:
            # check if this message's is in the starboard. If so, delete it
            async for star_message in star_channel.history(limit=300):
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
                        await logMsg(star_channel.guild, f"{starboard_emoji} :x: Starboard message {star_message.id} was removed (from {msg_link}) (original message was removed (this starboard message's linked id matched the removed message's)). Content: \"\"\"{star_message.embeds[0].description}\"\"\" and attachment: {image}")
                        await star_message.delete()
                        return

async def setup(client):
    await client.add_cog(Starboard(client))

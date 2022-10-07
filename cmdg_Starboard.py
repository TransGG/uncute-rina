import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *
from datetime import datetime # for embed timestamp

import pymongo # for online database
from pymongo import MongoClient

starboard_emoji_id = 992493515714068480
starboard_emoji = "<:TPA_Trans_Starboard:992493515714068480>"

messageIdMarkedForDeletion = []

class Starboard(commands.Cog):
    def __init__(self, client):
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
        await star_message.edit(content = new_content)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.id == self.client.user.id:
            return

        #get the message id from payload.message_id through the channel (with payload.channel_id) (oof lengthy process)
        ch = self.client.get_channel(payload.channel_id)
        message = await ch.fetch_message(payload.message_id)

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
                    msgLink = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
                    embed = discord.Embed(
                            color = discord.Colour.from_rgb(r=255, g=172, b=51),
                            title = '',
                            description = f"{message.content}",
                            timestamp = datetime.now()
                        )
                    embed.add_field(name = "Source", value = f"[Jump!]({msgLink})")
                    embed.set_footer(text = f"{message.id}")
                    for attachment in message.attachments:
                        if attachment.height: #is image or video
                            embed.set_image(url = attachment.url)
                            break
                            # can only set one image per embed.. :/
                    embed.set_author(
                            name = f"{message.author.nick or message.author.name}",
                            url = "https://amitrans.org/", #todo
                            icon_url = message.author.display_avatar.url
                    )

                    msg = await star_channel.send(
                            f"💫 **{reaction.count}** <#{message.channel.id}>",
                            embed = embed,
                            allowed_mentions = discord.AllowedMentions.none(),
                        )
                    await logMsg(star_channel.guild, f"{starboard_emoji} Starboard message {msg.jump_url} was created from {message.jump_url}. Content: \"\"\"{message.content}\"\"\" and attachments: {[x.url for x in message.attachments]}")
                    # add initial star reaction to starboarded message, and new starboard msg
                    await message.add_reaction(starboard_emoji)
                    await msg.add_reaction(starboard_emoji)
                    await msg.add_reaction("❌")
                    # todo downvotes
                    # add star reaction to original message to prevent message from being re-added to the starboard

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
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
            if reaction.emoji == '⭐':
                if reaction.me:
                    # check if this message is already in the starboard. If so, update it
                    async for star_message in star_channel.history(limit=200):
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
            messageIdMarkedForDeletion.remove(message_id)
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
                            msg_link = str(message_payload.message_id)+"  |  "+ ((await self.client.get_channel(message_payload.channel_id).fetch_message(message_payload.message_id)).jump_url)
                        except discord.NotFound:
                            msg_link = str(message_payload.message_id)+" (couldn't get jump link)"
                        await logMsg(star_channel.guild, f"{starboard_emoji} :x: Starboard message {star_message.id} was removed (from {msg_link}) (original message was removed (this starboard message's linked id matched the removed message's)). Content: \"\"\"{star_message.embeds[0].description}\"\"\" and attachment: {image}")
                        await star_message.delete()
                        return

async def setup(client):
    await client.add_cog(Starboard(client))
import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *
import re #use regex to identify custom emojis in a text message
from time import mktime # for unix time code
from datetime import datetime # for turning unix time into datetime

import pymongo # for online database
from pymongo import MongoClient

class EmojiStats(commands.Cog):
    def __init__(self, client):
        global RinaDB
        RinaDB = client.RinaDB

    async def addToData(self, emojiID, emojiName, location, animated):
        collection = RinaDB["emojistats"]
        query = {"id": emojiID}
        data = collection.find(query)
        try:
            data = data[0]
        except IndexError:
            collection.insert_one(query)
            data = collection.find(query)[0]

        if location == "message":
            location = "messageUsedCount"
        elif location == "reaction":
            location = "reactionUsedCount"
        else:
            raise ValueError("Cannot add to database since the location of the reaction isn't defined correctly.")

        #increment the usage of the emoji in the dictionary, depending on where it was used (see $location above)
        collection.update_one(  query, {"$inc" : {location:1} } , upsert=True  )
        collection.update_one(  query, {"$set":{"lastUsed": mktime(datetime.utcnow().timetuple()) , "name":emojiName, "animated":animated}}, upsert=True  )
        # collection.update_one( query, {"$set":{"name":emojiName}})
        #debug(f"Successfully added new data for {emojiID} as {location.replace('UsedCount','')}",color="blue")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        emojis = []
        startIndex = 0
        loopCatcher = 0
        while True:
            emoji = re.search("<a?:[a-zA-Z_0-9]+:[0-9]+>", message.content[startIndex:])
            if emoji is None:
                break
            sections = emoji.group().split(":")
            id = sections[2][:-1]
            name = sections[1]
            animated = (sections[0] == "<a")
            if not any(id in emojiList for emojiList in emojis):
                emojis.append([id,name])
            startIndex += emoji.span()[1] # (11,29) for example
            loopCatcher += 1
            if loopCatcher > 50:
                logMsg(message.guild, "<@262913789375021056> @MysticMia#7612 <@280885861984239617> @Cleo#1003 WARNING INFINITE LOOP in on_message of cmd_emojistats cog! Broken it with a `return`! Figure out the situation with Cleo!"+\
                f"\nLook at https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}")
                return
        for emoji in emojis:
            await self.addToData(emoji[0], emoji[1], "message", animated)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if reaction.emoji.id is not None:
            await self.addToData(str(reaction.emoji.id), reaction.emoji.name, "reaction", reaction.emoji.animated)

    @app_commands.command(name="getemojidata",description="Get emoji usage data from an ID!")
    @app_commands.describe(emoji= "Emoji you want to get data of")
    async def getEmojiData(self, itx: discord.Interaction, emoji: str):
        # for testing purposes, for now.
        if not isStaff(itx):
            await itx.response.send_message("You currently can't do this. It's in a testing process.", ephemeral=True)
            return

        if ":" in emoji:
            emoji = emoji.split(":")[2].replace(">","")
        emoji_id = emoji
        for x in emoji_id:
            try:
                int(x)
            except:
                await itx.response.send_message("You need to fill in the ID of the emoji. This ID can't contain other characters. Only numbers.",ephemeral=True)
                return

        collection = RinaDB["emojistats"]
        query = {"id": emoji_id}
        search = collection.find(query)
        try:
            emoji = search[0]
        except:
            await itx.response.send_message("That emoji doesn't have data yet. It hasn't been used since we started tracking the data yet. (<t:1660156260:R>, <t:1660156260:F>)", ephemeral=True)
            return

        try:
            msgUsed = emoji['messageUsedCount']
        except KeyError:
            msgUsed = 0
        try:
            reactionUsed = emoji['reactionUsedCount']
        except KeyError:
            reactionUsed = 0
        try:
            animated = emoji['animated']
        except KeyError:
            animated = False

        emojiSearch = ('a'*animated)+":"+emoji["name"]+":"+emoji["id"]
        emote = discord.PartialEmoji.from_str(emojiSearch)

        await itx.response.send_message(f"Data for {emote}"+f"  ({emote})\n".replace(':','\\:')+\
        f"messageUsedCount: {msgUsed}\n"+\
        f"reactionUsedCount: {reactionUsed}\n"+\
        f"Animated: {(animated)}\n"+\
        f"Last used: {datetime.utcfromtimestamp(emoji['lastUsed']).strftime('%Y-%m-%d (yyyy-mm-dd) at %H:%M:%S')}",ephemeral=True)

    @app_commands.command(name="getemojitop10",description="Get top 10 most used emojis")
    async def getEmojiTop10(self, itx: discord.Interaction):
        # for testing purposes, for now.
        if not isStaff(itx):
            await itx.response.send_message("You currently can't do this. It's in a testing process.", ephemeral=True)
            return

        collection = RinaDB["emojistats"]
        output = ""
        for type in ["messageUsedCount","reactionUsedCount"]:
            results = []
            search = collection.find({},limit=10,sort=[(type,pymongo.DESCENDING)])
            for emoji in search:
                animated = 0
                try:
                    animated = emoji['animated']
                    if animated:
                        animated = 1
                except KeyError:
                    pass

                emojiFull = "<"+("a"*animated)+":"+emoji["name"]+":"+emoji["id"]+">"
                try:
                    results.append(f"> **{emoji[type]}**: {emojiFull}")
                except KeyError:
                    # leftover emoji doesn't have a value for messageUsedCount or reactionUsedCount yet
                    pass
            output += "\nTop 10 for "+type.replace("UsedCount","")+"s:\n"
            output += '\n'.join(results)
        await itx.response.send_message(output,ephemeral=True)

async def setup(client):
    # client.add_command(getMemberData)
    await client.add_cog(EmojiStats(client))

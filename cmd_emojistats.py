import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *
import re #use regex to identify custom emojis in a text message
from time import mktime # for unix time code

import pymongo # for online database
from pymongo import MongoClient
mongoURI = open("mongo.txt","r").read()
cluster = MongoClient(mongoURI)
RinaDB = cluster["Rina"]

class EmojiStats(commands.Cog):
    async def addToData(self, emojiID, emojiName, location):
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
        collection.update_one(  query, {"$set":{"lastUsed": mktime(datetime.utcnow().timetuple()) , "name":emojiName}}, upsert=True  )
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
            if not any(id in emojiList for emojiList in emojis):
                emojis.append([id,name])
            startIndex += emoji.span()[1] # (11,29) for example
            loopCatcher += 1
            if loopCatcher > 50:
                logMsg(message.guild, "<@262913789375021056> @MysticMia#7612 <@280885861984239617> @Cleo#1003 WARNING INFINITE LOOP in on_message of cmd_emojistats cog! Broken it with a `return`! Figure out the situation with Cleo!"+\
                f"\nLook at https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}")
                return
        for emoji in emojis:
            await self.addToData(emoji[0], emoji[1], "message")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if reaction.emoji.id is not None:
            await self.addToData(str(reaction.emoji.id), reaction.emoji.name, "reaction")

async def setup(client):
    # client.add_command(getMemberData)
    await client.add_cog(EmojiStats(client))

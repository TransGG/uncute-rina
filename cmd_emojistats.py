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
        data = collection.find_one(query)
        if data is None:
            collection.insert_one(query)
            data = collection.find_one(query)

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
            emoji = emoji.split(":")[2][:-1]
        emoji_id = emoji
        for x in emoji_id:
            try:
                int(x)
            except:
                await itx.response.send_message("You need to fill in the ID of the emoji. This ID can't contain other characters. Only numbers.",ephemeral=True)
                return

        collection = RinaDB["emojistats"]
        query = {"id": emoji_id}
        emoji = collection.find_one(query)
        if emoji is None:
            await itx.response.send_message("That emoji doesn't have data yet. It hasn't been used since we started tracking the data yet. (<t:1660156260:R>, <t:1660156260:F>)", ephemeral=True)
            return

        msgUsed = emoji.get('messageUsedCount',0)
        reactionUsed = emoji.get('reactionUsedCount',0)
        animated = emoji.get('animated',False)
        # try:
        #     animated = emoji['animated']
        # except KeyError:
        #     animated = False

        emojiSearch = ('a'*animated)+":"+emoji["name"]+":"+emoji["id"]
        emote = discord.PartialEmoji.from_str(emojiSearch)

        await itx.response.send_message(f"Data for {emote}"+f"  ({emote})\n".replace(':','\\:')+\
        f"messageUsedCount: {msgUsed}\n"+\
        f"reactionUsedCount: {reactionUsed}\n"+\
        f"Animated: {(animated)}\n"+\
        f"Last used: {datetime.utcfromtimestamp(emoji['lastUsed']).strftime('%Y-%m-%d (yyyy-mm-dd) at %H:%M:%S')}",ephemeral=True)

    @app_commands.command(name="getunusedemojis",description="Get the least-used emojis")
    @app_commands.describe(hidden= "Do you want everyone in this channel to be able to see this result?",
                           max_results = "How many emojis do you want to retrieve at most? (may return fewer)",
                           min_used = "Up to how many times may the emoji have been used? (= min_msg + min_react)(default: 1)",
                           min_msg = "Up to how many times may the emoji have been used in a message? (default: 1)",
                           min_react = "Up to how many times may the emoj have been used as a reaction? (default: 1)",
                           animated = "Are you looking for animated emojis or static emojis")
    @app_commands.choices(animated=[
        discord.app_commands.Choice(name='Animated emojis', value=1),
        discord.app_commands.Choice(name='Static/Image emojis', value=2),
        discord.app_commands.Choice(name='Both', value=3)
    ])
    async def getUnusedEmojis(self,itx: discord.Interaction, hidden: bool =True, max_results:int = 10, min_used:int = 1, min_msg:int = 1, min_react:int = 1, animated:int = 3):
        if not isStaff(itx):
            await itx.response.send_message("You currently can't do this. It's in a testing process.", ephemeral=True)
            return
        await itx.response.send_message("This might take a while (\"Rina is thinking...\")\nThis message will be edited when it has found a few unused emojis (both animated and non-animated)",ephemeral=hidden)

        if max_results > 50:
            max_results = 50
        if min_used < 0:
            min_used = 0
        if min_msg < 0:
            min_msg = 0
        if min_react < 0:
            min_react = 0

        unused_emojis = []
        for emoji in itx.guild.emojis:
            if emoji.animated and (animated == 2):
                continue
            if (not emoji.animated) and animated == 1:
                continue

            collection = RinaDB["emojistats"]
            query = {"id": str(emoji.id)}
            emojidata = collection.find_one(query)
            if emojidata is None:
                unused_emojis.append(f"<{'a'*emoji.animated}:{emoji.name}:{emoji.id}> (0,0)")
                continue

            msgUsed = emojidata.get('messageUsedCount',0)
            reactionUsed = emojidata.get('reactionUsedCount',0)
            if (msgUsed + reactionUsed <= min_used) and (msgUsed <= min_msg) and (reactionUsed <= min_react):
                unused_emojis.append(f"<{'a'*emoji.animated}:{emoji.name}:{emoji.id}> ({msgUsed},{reactionUsed})")

            if len(unused_emojis) > max_results:
                break

        output = ', '.join(unused_emojis)
        if len(output) > 1850:
            output = output[:1850] + "\nShortened to be able to be sent."
        await itx.edit_original_response(content="These emojis have been used very little (x used in msg, x used as reaction):\n"+output)

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

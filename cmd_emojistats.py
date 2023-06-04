from Uncute_Rina import *
from import_modules import *

async def add_to_data(emoji_id, emoji_name, location, animated):
    collection = asyncRinaDB["emojistats"]
    query = {"id": emoji_id}
    data = await collection.find_one(query)
    if data is None:
        await collection.insert_one(query)

    if location == "message":
        location = "messageUsedCount"
    elif location == "reaction":
        location = "reactionUsedCount"
    else:
        raise ValueError("Cannot add to database since the location of the reaction isn't defined correctly.")

    #increment the usage of the emoji in the dictionary, depending on where it was used (see $location above)
    await collection.update_one(query, {"$inc" : {location:1}} , upsert=True)
    await collection.update_one(query, {"$set":{"lastUsed": mktime(datetime.now(timezone.utc).timetuple()) , "name":emoji_name, "animated":animated}}, upsert=True)
    # collection.update_one( query, {"$set":{"name":emojiName}})
    #debug(f"Successfully added new data for {emojiID} as {location.replace('UsedCount','')}",color="blue")


class EmojiStats(commands.Cog):
    def __init__(self, client: Bot):
        global asyncRinaDB
        asyncRinaDB = client.asyncRinaDB
        self.client = client

    emojistats = app_commands.Group(name='emojistats', description='Get information about emoji usage in messages and reactions')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        emojis = []
        start_index = 0
        animated = None
        while True:
            emoji = re.search("<a?:[a-zA-Z_0-9]+:[0-9]+>", message.content[start_index:])
            if emoji is None:
                break
            sections = emoji.group().split(":")
            id = sections[2][:-1]
            name = sections[1]
            animated = (sections[0] == "<a")
            if not any(id in emojiList for emojiList in emojis):
                emojis.append([id,name])
            start_index += emoji.span()[1] # (11,29) for example


        for emoji in emojis:
            assert animated is not None
            await add_to_data(emoji[0], emoji[1], "message", animated)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if reaction.emoji.id is not None:
            await add_to_data(str(reaction.emoji.id), reaction.emoji.name, "reaction", reaction.emoji.animated)

    @emojistats.command(name="getemojidata",description="Get emoji usage data from an ID!")
    @app_commands.rename(emoji_name="emoji")
    @app_commands.describe(emoji_name="Emoji you want to get data of")
    async def get_emoji_data(self, itx: discord.Interaction, emoji_name: str):
        # for testing purposes, for now.
        if not is_staff(itx):
            await itx.response.send_message("You currently can't do this. It's in a testing process.", ephemeral=True)
            return

        if ":" in emoji_name:
            emoji_name = emoji_name.split(":")[2][:-1]
        emoji_id = emoji_name
        if not emoji_id.isdecimal():
            await itx.response.send_message("You need to fill in the ID of the emoji. This ID can't contain other characters. Only numbers.",ephemeral=True)
            return

        collection = asyncRinaDB["emojistats"]
        query = {"id": emoji_id}
        emoji = await collection.find_one(query)
        if emoji is None:
            await itx.response.send_message("That emoji doesn't have data yet. It hasn't been used since we started tracking the data yet. (<t:1660156260:R>, <t:1660156260:F>)", ephemeral=True)
            return

        msg_used = emoji.get('messageUsedCount',0)
        reaction_used = emoji.get('reactionUsedCount',0)
        animated = emoji.get('animated',False)
        # try:
        #     animated = emoji['animated']
        # except KeyError:
        #     animated = False

        emoji_search = ('a'*animated)+":"+emoji["name"]+":"+emoji["id"]
        emote = discord.PartialEmoji.from_str(emoji_search)

        await itx.response.send_message(f"Data for {emote}"+f"  ({emote})\n".replace(':','\\:') +
                                        f"messageUsedCount: {msg_used}\n" +
                                        f"reactionUsedCount: {reaction_used}\n" +
                                        f"Animated: {animated}\n" +
                                        f"Last used: {datetime.utcfromtimestamp(emoji['lastUsed']).strftime('%Y-%m-%d (yyyy-mm-dd) at %H:%M:%S')}",ephemeral=True)

    @emojistats.command(name="getunusedemojis",description="Get the least-used emojis")
    @app_commands.describe(hidden="Do you want everyone in this channel to be able to see this result?",
                           max_results="How many emojis do you want to retrieve at most? (may return fewer)",
                           min_used="Up to how many times may the emoji have been used? (= min_msg + min_react)(default: 1)",
                           min_msg="Up to how many times may the emoji have been used in a message? (default: 1)",
                           min_react="Up to how many times may the emoj have been used as a reaction? (default: 1)",
                           animated="Are you looking for animated emojis or static emojis")
    @app_commands.choices(animated=[
        discord.app_commands.Choice(name='Animated emojis', value=1),
        discord.app_commands.Choice(name='Static/Image emojis', value=2),
        discord.app_commands.Choice(name='Both', value=3)
    ])
    async def get_unused_emojis(self,itx: discord.Interaction, hidden: bool = True, max_results:int = 10, min_used:int = 1, min_msg:int = 1, min_react:int = 1, animated:int = 3):
        if not is_staff(itx):
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

            collection = asyncRinaDB["emojistats"]
            query = {"id": str(emoji.id)}
            emojidata = await collection.find_one(query)
            if emojidata is None:
                unused_emojis.append(f"<{'a'*emoji.animated}:{emoji.name}:{emoji.id}> (0,0)")
                continue

            msg_used = emojidata.get('messageUsedCount',0)
            reaction_used = emojidata.get('reactionUsedCount',0)
            if (msg_used + reaction_used <= min_used) and (msg_used <= min_msg) and (reaction_used <= min_react):
                unused_emojis.append(f"<{'a'*emoji.animated}:{emoji.name}:{emoji.id}> ({msg_used},{reaction_used})")

            if len(unused_emojis) > max_results:
                break
            await asyncio.sleep(0)

        output = ', '.join(unused_emojis)
        if len(output) > 1850:
            output = output[:1850] + "\nShortened to be able to be sent."
        await itx.edit_original_response(content="These emojis have been used very little (x used in msg, x used as reaction):\n"+output)

    @emojistats.command(name="getemojitop10",description="Get top 10 most used emojis")
    async def get_emoji_top_10(self, itx: discord.Interaction):
        # for testing purposes, for now.
        if not is_staff(itx):
            await itx.response.send_message("You currently can't do this. It's in a testing process.", ephemeral=True)
            return

        collection = asyncRinaDB["emojistats"]
        output = ""
        for type in ["messageUsedCount","reactionUsedCount"]:
            results = []
            async for emoji in collection.find({},limit=10,sort=[(type,pymongo.DESCENDING)]):
                animated = 0
                try:
                    animated = emoji['animated']
                    if animated:
                        animated = 1
                except KeyError:
                    pass

                emoji_full = "<"+("a"*animated)+":"+emoji["name"]+":"+emoji["id"]+">"
                try:
                    results.append(f"> **{emoji[type]}**: {emoji_full}")
                except KeyError:
                    # leftover emoji doesn't have a value for messageUsedCount or reactionUsedCount yet
                    pass
            output += "\nTop 10 for "+type.replace("UsedCount","")+"s:\n"
            output += '\n'.join(results)
        await itx.response.send_message(output,ephemeral=True)

async def setup(client):
    # client.add_command(getMemberData)
    await client.add_cog(EmojiStats(client))

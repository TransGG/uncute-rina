import re  # to find all emojis used in someone's message
import sys  # for integer max value: sys.maxsize
from datetime import datetime, timezone
from time import mktime  # for logging emoji last use time

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands
import motor.core as motorcore  # for typing
import pymongo  # for pymongo.DESCENDING when sorting db query output

from resources.customs.bot import Bot
from resources.customs.emojistats import EmojiSendSource


#   Rina.emojistats         # snippet of <:ask:987785257661108324> in a test db at 2024-02-17T00:06+01:00
# ------------------------------------------------------
#               _id = Object('62f3004156483575bb3175de')
#                id = "987785257661108324"          #  str  of emoji.id
#              name = "ask"                         #  str  of emoji.name
#  messageUsedCount = 11                            #  int  of how often messages have contained this emoji
#          lastUsed = 1666720691                    #  int  of unix timestamp of when this emoji was last used
#          animated = false                         #  bool of emoji.animated
# reactionUsedCount = 8                             #  int  of how often messages have been replied to with this emoji


async def add_to_emoji_data(
        emoji: tuple[bool, str, str],
        async_rina_db: motorcore.AgnosticDatabase,
        location: EmojiSendSource,
):
    """
    Helper function to add emoji data to the mongo database when an emoji is sent/replied in chat.

    Parameters
    -----------
    emoji: :class:`tuple[animated, emoji_name, emoji_id]`
        The emoji (kind of in format of <a:Emoji_Name1:0123456789>).
    async_rina_db: :class:`AgnosticDatabase`
        An async connection to Rina's MongoDb.
    location: :class:`EmojiSendEnum`
        Whether the emoji was used in a message or as a reaction.
    """

    (animated, emoji_name, emoji_id) = emoji
    collection = async_rina_db["emojistats"]
    query = {"id": emoji_id}
    data = await collection.find_one(query)
    if data is None:
        await collection.insert_one(query)

    if location == EmojiSendSource.MESSAGE:
        location = "messageUsedCount"
    elif location == EmojiSendSource.REACTION:
        location = "reactionUsedCount"
    else:
        raise ValueError("Cannot add to database since the location of the reaction isn't defined correctly.")

    # increment the usage of the emoji in the dictionary, depending on where it was used (see $location above)
    await collection.update_one(query, {"$inc": {location: 1}}, upsert=True)
    await collection.update_one(query,
                                {"$set": {"lastUsed": mktime(datetime.now(timezone.utc).timetuple()),
                                          "name": emoji_name,
                                          "animated": animated}},
                                upsert=True)


async def add_to_sticker_data(sticker_name: str, async_rina_db: motorcore.AgnosticDatabase, sticker_id: str):
    """
    Helper function to add sticker data to the mongo database when a sticker is sent in chat.

    Parameters
    -----------
    sticker_name: string
        The sticker name.
    async_rina_db: :class:`AgnosticDatabase`:
        An async link to the MongoDB.
    sticker_id: str
        The sticker id, as string.
    """
    collection = async_rina_db["stickerstats"]
    query = {"id": sticker_id}
    data = await collection.find_one(query)
    if data is None:
        await collection.insert_one(query)

    location = "messageUsedCount"

    # increment the usage of the sticker in the dictionary
    await collection.update_one(query, {"$inc": {location: 1}}, upsert=True)
    await collection.update_one(query, {
        "$set": {"lastUsed": mktime(datetime.now(timezone.utc).timetuple()), "name": sticker_name}}, upsert=True)


class EmojiStats(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    emojistats = app_commands.Group(name='emojistats',
                                    description='Get information about emoji usage in messages and reactions')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        emojis: list[tuple[bool, str, str]] = []
        start_index: int = 0
        while True:
            # check for an emoji that isn't escaped (at beginning of msg or any non-backslash character
            # in front of it): with this format <a:Name_1:0123456789> or <:Name_2:0123456789> (a = animated)
            emoji = re.search("(?:[^\\\\]|^)<a?:[a-zA-Z_0-9]+:[0-9]+>", message.content[start_index:])
            # get first instance of an emoji in the message slice (to get a list of all emojis)
            if emoji is None:
                break
            emoji_capture = emoji.group()
            if not emoji_capture.startswith("<") and not emoji_capture.startswith("\\"):
                # to test when an emoji is escaped (\:hello:), the regex tests the character in front of
                # the emoji. It also captures that character if it isn't a backslash, so we have to filter it out.
                # Can also be fixed by using positive lookahead: changed "(?:[^" to "(?=:[^"
                emoji_capture = emoji_capture[1:]
            (animated, name, emoji_id) = emoji_capture.replace(">", "").split(":")
            assert emoji_id.isdecimal(), f"Emoji `{emoji}` should have a numeric emoji id"
            # should be decimal due to regex
            animated = (animated.split("<")[-1] == "a")

            if not any(emoji_id in emojiList for emojiList in emojis):
                emojis.append((animated, name, emoji_id))
            start_index += emoji.span()[1]  # (11,29) for example

        for emoji in emojis:
            await add_to_emoji_data(emoji, self.client.async_rina_db, location=EmojiSendSource.MESSAGE)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        if reaction.emoji.id is not None:
            await add_to_emoji_data((reaction.emoji.animated, reaction.emoji.name, str(reaction.emoji.id)),
                                    self.client.async_rina_db,
                                    location=EmojiSendSource.REACTION)

    @emojistats.command(name="getemojidata", description="Get emoji usage data from an ID!")
    @app_commands.rename(emoji_name="emoji")
    @app_commands.describe(emoji_name="Emoji you want to get data of")
    async def get_emoji_data(self, itx: discord.Interaction, emoji_name: str):
        if ":" in emoji_name:
            emoji_name = emoji_name.strip().split(":")[2][:-1]
        emoji_id = emoji_name
        if not emoji_id.isdecimal():
            await itx.response.send_message(
                "You need to fill in the ID of the emoji. This ID can't contain other characters. Only numbers.",
                ephemeral=True)
            return

        collection = self.client.async_rina_db["emojistats"]
        query = {"id": emoji_id}
        emoji = await collection.find_one(query)
        if emoji is None:
            await itx.response.send_message(
                "That emoji doesn't have data yet. It hasn't been used since we started tracking the "
                "data yet. (<t:1660156260:R>, <t:1660156260:F>)",
                ephemeral=True)
            return

        msg_used = emoji.get('messageUsedCount', 0)
        reaction_used = emoji.get('reactionUsedCount', 0)
        animated = emoji.get('animated', False)
        # try:
        #     animated = emoji['animated']
        # except KeyError:
        #     animated = False

        emoji_search = ('a' * animated) + ":" + emoji["name"] + ":" + emoji["id"]
        emote = discord.PartialEmoji.from_str(emoji_search)

        await itx.response.send_message(f"Data for {emote}" + f"  ({emote})\n".replace(':', '\\:') +
                                        f"messageUsedCount: {msg_used}\n" +
                                        f"reactionUsedCount: {reaction_used}\n" +
                                        f"Animated: {animated}\n" +
                                        f"Last used: {datetime.fromtimestamp(emoji['lastUsed']).strftime('%Y-%m-%d (yyyy-mm-dd) at %H:%M:%S')}",
                                        ephemeral=True)

    @emojistats.command(name="get_unused_emojis", description="Get the least-used emojis")
    @app_commands.describe(public="Do you want everyone in this channel to be able to see this result?",
                           max_results="How many emojis do you want to retrieve at most? (may return fewer)",
                           used_max="Up to how many times may the emoji have been used? "
                                    "(= min_msg + min_react)(default: 10)",
                           msg_max="Up to how many times may the emoji have been used in a message? (default: inf)",
                           react_max="Up to how many times may the emoji have been used as a reaction? (default: inf)",
                           animated="Are you looking for animated emojis or static emojis")
    @app_commands.choices(animated=[
        discord.app_commands.Choice(name='Animated emojis', value=1),
        discord.app_commands.Choice(name='Static/Image emojis', value=2),
        discord.app_commands.Choice(name='Both', value=3)
    ])
    async def get_unused_emojis(
            self, itx: discord.Interaction, public: bool = False,
            max_results: int = 10,
            used_max: int = sys.maxsize,
            msg_max: int = sys.maxsize,
            react_max: int = sys.maxsize,
            animated: int = 3
    ):
        await itx.response.defer(ephemeral=not public)

        unused_emojis = []

        collection = self.client.async_rina_db["emojistats"]
        query = {
            "$expr": {
                "$lte": [
                    {"$add": [
                        {"$ifNull": ["$messageUsedCount", 0]},
                        {"$ifNull": ["$reactionUsedCount", 0]}
                    ]},
                    used_max
                ]
            }
        }  # = [x for x in collection if x.get(messageUsedCount,0) + x.get(reactionUsedCount,0) <= used_max]

        if max_results > 50:
            max_results = 50
        if used_max < 0:
            used_max = 0
        if msg_max < 0:
            msg_max = 0
        if react_max < 0:
            react_max = 0

        if msg_max != sys.maxsize:
            # only limit query on '_UsedCount' if you want to limit for it.
            # Some entries don't have a value for it- Don't want to search for a "0" then.
            query["messageUsedCount"] = {"$lte": msg_max}
        if react_max != sys.maxsize:
            # only limit query on '_UsedCount' if you want to limit for it.
            # Some entries don't have a value for it- Don't want to search for a "0" then.
            query["reactionUsedCount"] = {"$lte": react_max}
        if animated != 3:
            # only limit query with 'animated' if its value actually matters (not 3 / "Both")
            query["animated"] = animated == 1

        emoji_stats: list[dict[
            typing.Literal["id", "messageUsedCount", "reactionUsedCount", "animated"],
            str | int | bool]] = [x async for x in collection.find(query)]
        emoji_stat_ids: list[str] = await collection.distinct("id")

        for emoji in itx.guild.emojis:
            if str(emoji.id) not in emoji_stat_ids:
                unused_emojis.append(f"<{'a' * emoji.animated}:{emoji.name}:{emoji.id}> (0,0)")
                continue

            for emoji_stat in emoji_stats:
                if emoji_stat["id"] == str(emoji.id):
                    # assumes the db ID column is unique (grabs first matching result)
                    break
            else:
                continue  # emoji doesn't exist anymore?

            if emoji_stat["messageUsedCount"] + emoji_stat["reactionUsedCount"] > used_max:
                continue

            unused_emojis.append(f"<{'a' * emoji.animated}:{emoji.name}:{emoji.id}>" +
                                 f"({emoji_stat.get('messageUsedCount', 0)},{emoji_stat.get('reactionUsedCount', 0)})")

            if len(unused_emojis) >= max_results:
                break

        header = "These emojis have been used very little (x used in msg, x used as reaction):\n"
        output = ', '.join(unused_emojis)
        if len(output) > 1850:
            warning = "\nShortened to be able to be sent."
            output = output[:(2000 - len(header) - len(warning) - 5)] + warning
        await itx.followup.send(content=header + output)

    @emojistats.command(name="getemojitop10", description="Get top 10 most used emojis")
    async def get_emoji_top_10(self, itx: discord.Interaction):
        collection = self.client.async_rina_db["emojistats"]
        output = ""
        for source_type in ["messageUsedCount", "reactionUsedCount"]:
            results = []
            async for emoji in collection.find({}, limit=10, sort=[(source_type, pymongo.DESCENDING)]):
                animated = 0
                try:
                    animated = emoji['animated']
                    if animated:
                        animated = 1
                except KeyError:
                    pass

                emoji_full = "<" + ("a" * animated) + ":" + emoji["name"] + ":" + emoji["id"] + ">"
                try:
                    results.append(f"> **{emoji[source_type]}**: {emoji_full}")
                except KeyError:
                    # leftover emoji doesn't have a value for messageUsedCount or reactionUsedCount yet
                    pass
            output += "\nTop 10 emojis for " + source_type.replace("UsedCount", "") + "s:\n"
            output += '\n'.join(results)
        await itx.response.send_message(output, ephemeral=True)


class StickerStats(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    stickerstats = app_commands.Group(name='stickertats',
                                      description='Get information about sticker usage in messages and reactions')

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        for sticker in message.stickers:
            # if sticker in message.guild.stickers:
            #     # only track if it's actually a guild's sticker; not some outsider one
            await add_to_sticker_data(sticker.name, self.client.async_rina_db, str(sticker.id))

    @stickerstats.command(name="getstickerdata", description="Get sticker usage data from an ID!")
    @app_commands.rename(sticker_name="sticker")
    @app_commands.describe(sticker_name="Sticker you want to get data of")
    async def get_sticker_data(self, itx: discord.Interaction, sticker_name: str):
        if ":" in sticker_name:
            # idk why people would, but idk the format for stickers so ill just assume <name:id> or something idk
            sticker_name = sticker_name.strip().split(":")[1][:-1]
        sticker_id = sticker_name
        if not sticker_id.isdecimal():
            await itx.response.send_message(
                "You need to fill in the ID of the sticker. This ID can't contain other characters. Only numbers.",
                ephemeral=True)
            return

        collection = self.client.async_rina_db["stickerstats"]
        query = {"id": sticker_id}
        sticker_response = await collection.find_one(query)
        if sticker_response is None:
            await itx.response.send_message("That sticker doesn't have data yet. It hasn't been used since "
                                            "we started tracking the data yet. (<t:1729311000:R>, <t:1729311000:F>)",
                                            ephemeral=True)
            return

        msg_used = sticker_response.get('messageUsedCount', 0)

        sticker_search = (sticker_response["name"] + ":" + sticker_response["id"])
        sticker = sticker_search
        msg_last_use_time = datetime.fromtimestamp(
            sticker_response['lastUsed'],
            tz=timezone.utc
        ).strftime('%Y-%m-%d (yyyy-mm-dd) at %H:%M:%S')

        await itx.response.send_message(f"Data for {sticker}" + f"  ".replace(':', '\\:') +
                                        f"(`{sticker}`)\n"
                                        f"messageUsedCount: {msg_used}\n"
                                        f"Last used: {msg_last_use_time}",
                                        ephemeral=True)

    @stickerstats.command(name="get_unused_stickers", description="Get the least-used stickers")
    @app_commands.describe(public="Do you want everyone in this channel to be able to see this result?",
                           max_results="How many stickers do you want to retrieve at most? (may return fewer)",
                           used_max="Up to how many times may the sticker have been used? (default: 10)")
    async def get_unused_stickers(
            self, itx: discord.Interaction, public: bool = False,
            max_results: int = 10, used_max: int = sys.maxsize
    ):
        await itx.response.defer(ephemeral=not public)

        unused_stickers = []

        collection = self.client.async_rina_db["stickerstats"]
        query = {
            "$expr": {
                "$lte": [
                    {"$add": [
                        {"$ifNull": ["$messageUsedCount", 0]}
                    ]},
                    used_max
                ]
            }
        }

        if max_results > 50:
            max_results = 50
        if used_max < 0:
            used_max = 0
        if used_max != sys.maxsize:
            # only limit query on '_UsedCount' if you want to limit for it.
            # Some entries don't have a value for it- Don't want to search for a "0" then.
            query["messageUsedCount"] = {"$lte": used_max}

        sticker_stats: list[dict[str, str | int | bool]] = [x async for x in collection.find(query)]
        sticker_stat_ids: list[str] = await collection.distinct("id")

        for sticker in await itx.guild.fetch_stickers():
            if str(sticker.id) not in sticker_stat_ids:
                unused_stickers.append(f"<{sticker.name}\\:{sticker.id}> (0)")
                continue

            for sticker_stat in sticker_stats:
                if sticker_stat["id"] == str(
                        sticker.id):  # assumes the db ID column is unique (grabs first matching result)
                    break
            else:
                continue  # sticker doesn't exist anymore?

            if sticker_stat["messageUsedCount"] + sticker_stat["reactionUsedCount"] > used_max:
                continue

            unused_stickers.append(f"<{sticker.name}\\:{sticker.id}>" +
                                   f"({sticker_stat.get('messageUsedCount', 0)})")

            if len(unused_stickers) > max_results:
                break

        header = "These stickers have been used very little (x used in msg):\n"
        output = ', '.join(unused_stickers)
        if len(output) > 1850:
            warning = "\nShortened to be able to be sent."
            output = output[:(2000 - len(header) - len(warning) - 5)] + warning
        await itx.followup.send(content=header + output)

    @stickerstats.command(name="getstickertop10", description="Get top 10 most used stickers")
    async def get_sticker_top_10(self, itx: discord.Interaction):
        collection = self.client.async_rina_db["stickerstats"]
        output = ""
        for source_type in ["messageUsedCount"]:
            results = []
            async for sticker in collection.find({}, limit=10, sort=[(source_type, pymongo.DESCENDING)]):
                sticker_full = "<" + sticker["name"] + "\\:" + sticker["id"] + ">"
                try:
                    results.append(f"> **{sticker[source_type]}**: {sticker_full}")
                except KeyError:
                    # leftover sticker doesn't have a value for messageUsedCount yet
                    pass
            output += "\nTop 10 stickers for " + source_type.replace("UsedCount", "") + "s:\n"
            output += '\n'.join(results)
        await itx.response.send_message(output, ephemeral=True)


async def setup(client):
    # client.add_command(getMemberData)
    await client.add_cog(EmojiStats(client))
    await client.add_cog(StickerStats(client))

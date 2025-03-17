from datetime import datetime, timezone
from time import mktime  # for logging emoji last use time
import sys  # for integer max value: sys.maxsize
import motor.core as motorcore  # for typing
from pymongo import DESCENDING

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from resources.customs.bot import Bot


async def _add_to_sticker_data(sticker_name: str, async_rina_db: motorcore.AgnosticDatabase, sticker_id: str):
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
            await _add_to_sticker_data(sticker.name, self.client.async_rina_db, str(sticker.id))

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
            async for sticker in collection.find({}, limit=10, sort=[(source_type, DESCENDING)]):
                sticker_full = "<" + sticker["name"] + "\\:" + sticker["id"] + ">"
                try:
                    results.append(f"> **{sticker[source_type]}**: {sticker_full}")
                except KeyError:
                    # leftover sticker doesn't have a value for messageUsedCount yet
                    pass
            output += "\nTop 10 stickers for " + source_type.replace("UsedCount", "") + "s:\n"
            output += '\n'.join(results)
        await itx.response.send_message(output, ephemeral=True)

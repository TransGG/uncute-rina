import discord
from motor.core import AgnosticDatabase

from resources.pymongo import (
    remove_data, DatabaseKeys, add_data, get_data, get_all_data
)


GuildId = int
StarboardMessageId = int
OriginalChannelId = int
OriginalMessageId = int
OriginalMessageData = tuple[OriginalChannelId, OriginalMessageId]

local_starboard_index: dict[GuildId, dict[StarboardMessageId, OriginalMessageData]] = {}
starboard_loaded = False


class StarboardNotLoadedException(Exception):
    pass


async def import_starboard_messages(
        async_rina_db: AgnosticDatabase,
        starboard_channel: discord.abc.Messageable
):
    """

    :param async_rina_db:
    :param starboard_channel:
    :return:
    """
    global local_starboard_index
    if not starboard_loaded:
        raise StarboardNotLoadedException()

    async for starboard_msg in starboard_channel.history(limit=None):
        try:
            guild_id, channel_id, message_id = parse_starboard_message(starboard_msg)
        except ValueError:
            continue

        orig_data = (channel_id, message_id)
        local_starboard_index[guild_id][starboard_msg.id] = orig_data

        await add_data(
            async_rina_db, starboard_msg.guild.id, DatabaseKeys.starboard,
            starboard_msg.id, orig_data
        )

    return local_starboard_index


async def fetch_starboard_messages(
        async_rina_db: AgnosticDatabase,
        guild_id: GuildId,
) -> dict[StarboardMessageId, OriginalMessageData]:
    data = await get_data(async_rina_db, guild_id, DatabaseKeys.starboard)
    if data is None:
        return {}

    local_starboard_index[guild_id] = data
    return local_starboard_index[guild_id]


async def fetch_all_starboard_messages(
    async_rina_db: AgnosticDatabase,
) -> dict[GuildId, dict[StarboardMessageId, OriginalMessageData]]:
    global local_starboard_index, starboard_loaded
    data = await get_all_data(async_rina_db, DatabaseKeys.starboard)
    if data is None:
        return {}

    local_starboard_index = data
    starboard_loaded = True
    return local_starboard_index


def get_starboard_message_ids(
        guild_id: GuildId
) -> dict[StarboardMessageId, tuple[OriginalChannelId, OriginalMessageId]]:
    """
    Retrieve the list of all starboard data for a guild.

    :param guild_id: The guild to get data for.
    :return: A tuple of the starboard message id, the original message's
     channel id, and the original message's id.
    """
    if not starboard_loaded:
        raise StarboardNotLoadedException()
    return local_starboard_index.get(guild_id, {})


def get_starboard_message_id(
        guild_id: GuildId,
        message_id: OriginalMessageId
) -> StarboardMessageId | None:
    if not starboard_loaded:
        raise StarboardNotLoadedException()
    for star_id, msg_data in get_starboard_message_ids(guild_id).items():
        orig_chan, orig_id = msg_data
        if orig_id == message_id:
            return star_id
    return None


def get_original_message_id(
        guild_id: GuildId,
        message_id: OriginalMessageId
) -> tuple[OriginalChannelId, OriginalMessageId] | None:
    if not starboard_loaded:
        raise StarboardNotLoadedException()
    for star_id, orig_chan, orig_id in get_starboard_message_ids(guild_id):
        if star_id == message_id:
            return orig_chan, orig_id
    return None


def parse_starboard_message(
    starboard_msg: discord.Message,
) -> tuple[GuildId, OriginalChannelId, OriginalMessageId]:
    # find original message
    if len(starboard_msg.embeds) == 0:
        raise ValueError("Message has no embeds.")
    if len(starboard_msg.embeds[0].fields) == 0:
        raise ValueError("Message embed has no fields.")
    text = starboard_msg.embeds[0].fields[0].value
    # "[Jump!](https:/ /4/5/6/)" -> "https:/ /4/5/6/)"
    link = text.split("(")[1]
    # Initial attempt to use [:-1] to remove the final ")" character
    #  doesn't work if there are unknown files in the original starboard
    #  message because rina mentions them in the starboard msg after the
    #  [Jump] link, adding "\n[...]" so ye.
    # "https:/ /4/5/6/)" -> "https:/ /4/5/6/"
    link = link.split(")", 1)[0]
    #   0    1      2           3
    # https:/ /discord.com / channels /
    #   4: guild_id          5: channel_id         6: message_id      7+
    # 985931648094834798 / 1006682505149169694 / 1014887159485968455 / ...
    guild_id, channel_id, message_id = [int(i) for i in link.split("/")[4:]]
    return guild_id, channel_id, message_id


async def add_to_local_starboard(
        async_rina_db: AgnosticDatabase,
        starboard_msg: discord.Message,
        original_msg: discord.Message
):
    global local_starboard_index
    guild_id = starboard_msg.guild.id
    if guild_id not in local_starboard_index:
        local_starboard_index[guild_id] = {}

    orig_data = (original_msg.channel.id, original_msg.id)
    local_starboard_index[guild_id][starboard_msg.id] = orig_data

    await add_data(async_rina_db, guild_id, DatabaseKeys.starboard,
                   starboard_msg.id, orig_data)


async def delete_from_local_starboard(
        async_rina_db: AgnosticDatabase,
        guild_id: int,
        starboard_message_id: int
) -> None:
    local_starboard_index.get(guild_id, {}).pop(starboard_message_id, None)
    await remove_data(async_rina_db, guild_id, DatabaseKeys.starboard,
                      starboard_message_id)

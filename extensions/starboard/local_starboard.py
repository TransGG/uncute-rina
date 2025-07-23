import discord
from motor.core import AgnosticDatabase
from resources.customs import Bot, GuildMessage

from resources.pymongo import (
    remove_data, DatabaseKeys, add_data, get_data, get_all_data
)


GuildId = int
StarboardMessageId = int
OriginalChannelId = int
OriginalMessageId = int
OriginalMessageData = tuple[OriginalChannelId, OriginalMessageId]
DatabaseData = tuple[StarboardMessageId, OriginalChannelId, OriginalMessageId]

local_starboard_index: dict[
    GuildId, dict[StarboardMessageId, OriginalMessageData]] = {}
starboard_loaded = False


class StarboardNotLoadedException(Exception):
    pass


async def import_starboard_messages(
        client: Bot,
        async_rina_db: AgnosticDatabase,
        starboard_channel: discord.abc.Messageable
) -> dict[GuildId, dict[StarboardMessageId, OriginalMessageData]]:
    """
    A helper function to retrieve all starboard messages in a channel.

    :param client: The client to test if starboard messages
     were sent by this bot.
    :param async_rina_db: The database in which to store the
     starboard messages.
    :param starboard_channel: The channel in which to look for
     starboard messages.
    :return: The local starboard index. {GuildId: {StarboardMessageId:
     (OriginalChannelId, OriginalMessageId) }}
    """
    async for starboard_msg in starboard_channel.history(limit=None):
        if not client.is_me(starboard_msg.author):
            continue
        try:
            guild_id, channel_id, message_id \
                = parse_starboard_message(starboard_msg)
        except (ValueError, IndexError):
            continue
        orig_data = (channel_id, message_id)
        if guild_id not in local_starboard_index:
            local_starboard_index[guild_id] = {}
        local_starboard_index[guild_id][starboard_msg.id] = orig_data

        database_data: DatabaseData = (
            starboard_msg.id, channel_id, message_id)

        # Json keys can't be integers, so starboard_msg.id will turn
        # into a string.
        await add_data(
            async_rina_db, starboard_msg.guild.id, DatabaseKeys.starboard,
            str(starboard_msg.id), database_data
        )

    return local_starboard_index


async def fetch_starboard_messages(
        async_rina_db: AgnosticDatabase,
        guild_id: GuildId,
) -> dict[StarboardMessageId, OriginalMessageData]:
    """
    Retrieve all of a guild's starboard data.

    :param async_rina_db: The database with which to retrieve the data.
    :param guild_id: The guild to retrieve data for
    :return: A dictionary mapping starboard message ids a tuple of its
     original message's channel id and message id.
    """
    data: dict[str, DatabaseData]
    data = await get_data(async_rina_db, guild_id, DatabaseKeys.starboard)
    if data is None:
        return {}

    guild_data = {}
    for database_data in data.values():
        starboard_msg_id = database_data[0]
        orig_data = (database_data[1], database_data[2])
        guild_data[starboard_msg_id] = orig_data

    local_starboard_index[guild_id] = guild_data

    return local_starboard_index[guild_id]


async def fetch_all_starboard_messages(
    async_rina_db: AgnosticDatabase,
) -> dict[GuildId, dict[StarboardMessageId, OriginalMessageData]]:
    """
    Retrieve all starboard data.

    :param async_rina_db: The database with which to retrieve the data.
    :return: A dictionary mapping guild ids dictionaries of starboard
     message ids mapping to tuples of their original message's
     channel id and message id.
    """
    global local_starboard_index, starboard_loaded
    data: dict[GuildId, dict[str, DatabaseData]]
    # starboard msg id turns into a string because json keys can't be integers
    data = await get_all_data(async_rina_db, DatabaseKeys.starboard)
    if data is None:
        return {}

    starboard_loaded = False
    local_starboard_index = {}

    for guild_id, guild_data in data.items():
        temp_guild_data = {}
        for database_data in guild_data.values():
            starboard_msg_id = database_data[0]
            orig_data = (database_data[1], database_data[2])
            temp_guild_data[starboard_msg_id] = orig_data

        local_starboard_index[guild_id] = temp_guild_data

    starboard_loaded = True
    return local_starboard_index


def get_starboard_message_ids(
        guild_id: GuildId
) -> dict[StarboardMessageId, tuple[OriginalChannelId, OriginalMessageId]]:
    """
    Get the list of all starboard data for a guild.

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
    """
    Get the starboard message id from a (potential) original message's id.

    :param guild_id: The guild to find the starboard message in.
    :param message_id: The original message id that would correspond to
     the starboard message id.
    :return: The starboard message id, or None if not found.
    """
    if not starboard_loaded:
        raise StarboardNotLoadedException()
    for star_id, msg_data in get_starboard_message_ids(guild_id).items():
        orig_chan, orig_id = msg_data
        if orig_id == message_id:
            return star_id
    return None


def get_original_message_info(
        guild_id: GuildId,
        starboard_msg_id: StarboardMessageId
) -> tuple[OriginalChannelId, OriginalMessageId] | None:
    """
    Get a starboard message's original message channel and id.

    :param guild_id: The guild id of the starboard message.
    :param starboard_msg_id: The starboard message to find the original
     message info for.
    :return: A tuple of the original message's channel id and message id.
    """
    if not starboard_loaded:
        raise StarboardNotLoadedException()

    guild_data = get_starboard_message_ids(guild_id)
    return guild_data.get(starboard_msg_id, None)


def parse_starboard_message(
    starboard_msg: discord.Message,
) -> tuple[GuildId, OriginalChannelId, OriginalMessageId]:
    """
    Get the original message data from a starboard message.

    It looks at the starboard message's first embed attempts to parse
    the jump_url in the first field value.

    The expected format of a hyperlink with the jump url is as follows:
     "x(0/1/2/3/4/5/6)y" where x does not contain a '(', and y is any string.
      0/1/2/3 would equal ["https:", "", "discord.com", "channels"].
      The expected return value would be [4, 5, 6].

    :param starboard_msg: The starboard message to parse.
    :return: A tuple of the original message's guild, channel,
     and message ids.
    :raise ValueError: If the message has no embeds; if the first embed has
     no fields; or if the split jump url contains ids that are not integers.
    :raise IndexError: If the format of the embed field value does not match
     that of a starboard's jump hyperlink.
    """
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
        starboard_msg: GuildMessage,
        original_msg: GuildMessage
):
    """
    Add a starboard message to the database and local cache.

    :param async_rina_db: The database with which to add the data.
    :param starboard_msg: The starboard message to add data for.
    :param original_msg: The original message to add data for.
    """
    guild_id = starboard_msg.guild.id
    if guild_id not in local_starboard_index:
        local_starboard_index[guild_id] = {}

    orig_data = (original_msg.channel.id, original_msg.id)
    local_starboard_index[guild_id][starboard_msg.id] = orig_data

    database_data = (starboard_msg.id, original_msg.channel.id,
                     original_msg.id)
    # Json keys can't be integers, so starboard_msg.id will turn
    # into a string.
    await add_data(async_rina_db, guild_id, DatabaseKeys.starboard,
                   str(starboard_msg.id), database_data)


async def delete_from_local_starboard(
        async_rina_db: AgnosticDatabase,
        guild_id: int,
        starboard_message_id: int
) -> None:
    """
    Delete a starboard message from the database and local cache.

    :param async_rina_db: The database with which to delete the data.
    :param guild_id: The guild id of the starboard message.
    :param starboard_message_id: The id of the starboard message and
     data to delete.
    """
    local_starboard_index.get(guild_id, {}).pop(starboard_message_id, None)
    await remove_data(async_rina_db, guild_id, DatabaseKeys.starboard,
                      str(starboard_message_id))


def is_starboard_message(guild_id: int, starboard_message_id: int) -> bool:
    """A helper function in O(1) to check if a message is in the starboard."""
    return starboard_message_id in local_starboard_index.get(guild_id, {})

import discord
from motor.core import AgnosticDatabase

from resources.pymongo.database_keys import DatabaseKeys
from resources.pymongo.guild_customs_manager import (
    add_data, remove_data, get_data, get_all_data
)


local_watchlist_index: dict[int, int] = {}  # user_id, thread_id
busy_updating_watchlist_index: bool = False


local_watchlist: dict[int, dict[int, int]] = {}
watchlist_loaded = False


class WatchlistNotLoadedException(Exception):
    pass


def get_watchlist(
        guild: discord.Guild,
        user_id: int,
) -> int | None:
    """
    Get a watchlist from the cache.

    :param guild: The guild to get the watchlist from.
    :param user_id: The id of the watchlist's user.

    :return: The watchlist thread id or ``None`` if no watchlist for
     this user was found.
    """
    if not watchlist_loaded:
        raise WatchlistNotLoadedException()
    if guild in local_watchlist:
        if user_id in local_watchlist[guild.id]:
            return local_watchlist[guild.id][user_id]
    return None


def get_watchlists(
        guild: discord.Guild,
) -> dict[int, int]:
    """
    Get a guild's watchlists from the cache.

    :param guild: The guild to get watchlists from.

    :return: A dictionary containing all watchlists registered in the guild.
    """
    if not watchlist_loaded:
        raise WatchlistNotLoadedException()
    if guild in local_watchlist:
        return local_watchlist[guild.id]
    return {}


async def create_watchlist(
        async_rina_db: AgnosticDatabase,
        guild: discord.Guild,
        user_id: int,
        thread_id: int
) -> None:
    """
    Create a new watchlist for the given guild.

    :param async_rina_db: The database to store the watchlist in.
    :param guild: The guild to add the watchlist to.
    :param user_id: The id of the watchlist's user.
    :param thread_id: The id of the watchlist thread.
    """
    global local_watchlist
    await add_data(
        async_rina_db,
        guild.id,
        DatabaseKeys.watchlist,
        user_id,
        thread_id,
    )

    if guild.id not in local_watchlist:
        local_watchlist[guild.id] = {}

    local_watchlist[guild.id][user_id] = thread_id


async def remove_watchlist(
        async_rina_db: AgnosticDatabase,
        guild: discord.Guild,
        user_id: int
) -> bool:
    """
    Remove a watchlist from the database for a guild.

    :param async_rina_db: The database to remove the watchlist from.
    :param guild: The guild to remove the watchlist from.
    :param user_id: The id of the watchlist's user.
    :return: Whether there was a watchlist for this user.
    """
    global local_watchlist
    changed, _ = await remove_data(
        async_rina_db,
        guild.id,
        DatabaseKeys.watchlist,
        user_id,
    )

    if guild.id not in local_watchlist:
        local_watchlist[guild.id] = {}

    if user_id in local_watchlist[guild.id]:
        del local_watchlist[guild.id][user_id]

    return changed


async def fetch_watchlists(
        async_rina_db: AgnosticDatabase,
        guild: discord.Guild,
) -> dict[int, int]:
    """
    Fetch watchlists in a guild from the database.
    :param async_rina_db: The database to fetch watchlists from.
    :param guild: The guild to fetch watchlists for.
    :return: A dictionary of watchlist user_ids and the matching thread_id for
     the given guild.
    """
    global local_watchlist
    data: dict[int, int] | None = await get_data(
        async_rina_db,
        guild.id,
        DatabaseKeys.watchlist,
    )

    if data is None:
        return {}

    local_watchlist[guild.id] = data
    return data


async def fetch_all_watchlists(
        async_rina_db: AgnosticDatabase,
) -> dict[int, dict[int, int]]:
    """
    Fetch all watchlists from the database.

    :param async_rina_db: The database to fetch watchlists with.
    :return: A dictionary of guild_ids, with a dictionary of watchlist
     user_ids and their corresponding thread_id.
    """
    global watchlist_loaded, local_watchlist
    data: dict[int, dict[int, int]] = await get_all_data(
        async_rina_db,
        DatabaseKeys.watchlist,
    )

    for guild_id, watchlist_objects in data.items():
        watchlists = {}
        for user_id, thread_id in watchlist_objects.items():
            watchlists[user_id] = thread_id
        local_watchlist[guild_id] = watchlists
    watchlist_loaded = True
    return local_watchlist


async def import_watchlist_threads(
        async_rina_db: AgnosticDatabase,
        watch_channel: discord.TextChannel
) -> list[discord.Thread]:
    """
    Import watchlists into the database and cache.

    :param async_rina_db: The database to store the watchlists into.
    :param watch_channel: The text channel containing this guild's watchlists.

    :return: A list of threads whose starter message could not be fetched.
    """
    global local_watchlist
    if watch_channel.guild.id not in local_watchlist:
        local_watchlist[watch_channel.guild.id] = {}

    # store reference to dict into a shorter variable

    failed_fetches = []
    # iterate non-archived threads
    for thread in watch_channel.threads:
        await _import_thread_to_local_list(
            async_rina_db, failed_fetches, thread)

    # iterate archived threads
    async for thread in watch_channel.archived_threads(limit=None):
        await _import_thread_to_local_list(
            async_rina_db, failed_fetches, thread)

    return failed_fetches


async def _import_thread_to_local_list(
        async_rina_db: AgnosticDatabase,
        failed_fetches: list[discord.Thread],
        thread: discord.Thread):
    global local_watchlist
    try:
        starter_message = await thread.parent.fetch_message(thread.id)
    except (discord.HTTPException, discord.NotFound, discord.Forbidden):
        failed_fetches.append(thread)
        return
    try:
        # index: 0    1         2                   3          4
        #     https: / / warned.username / 262913789375021056 /
        user_id = int(starter_message.embeds[0].author.url.split("/")[3])
        if user_id in local_watchlist:
            return
        # Only use the user's most recent watchlist thread
        #  (if ever there is a second thread).
        #  or maybe it does the earliest one?
        local_watchlist[thread.guild.id][user_id] = thread.id

        # this is not a kind operation on the mongo db lol
        await create_watchlist(async_rina_db, thread.guild, user_id, thread.id)
    except (IndexError, AttributeError):
        pass

import discord
import asyncio # for sleep(1) while waiting for other thread fetching function instance. Like cmdg_starboard: see get_or_fetch_starboard_messages()


local_watchlist_index: dict[int, int] = {} # user_id, thread_id
busy_updating_watchlist_index: bool = False


def add_to_watchlist_cache(user_id: int, thread_id: int):
    """
    Add a user to the watchlist cache.

    Parameters
    -----------
    user_id: :class:`int`
        The user id to add.
    thread_id: :class:`int`
        The id of the thread to link with the user.
    """
    local_watchlist_index[user_id] = thread_id

async def get_or_fetch_watchlist_index(watch_channel: discord.TextChannel) -> dict[int, int]:
    """
    Get or fetch a dictionary of all users currently on the watchlist, and their matching watchlist thread id.

    Parameters
    -----------
    watch_channel: :class:`discord.TextChannel`
        The text channel with all the stored watchout doubt messages and threads.

    Returns
    --------
    :class:`dict[int, int]`
        A dictionary with [user_id, thread_id] for the watchout doubts.
    """
    global busy_updating_watchlist_index, local_watchlist_index
    if not busy_updating_watchlist_index and local_watchlist_index == {}:
        busy_updating_watchlist_index = True
        watchlist_index_temp: dict[int, int] = {} # to later overwrite the global variable instead of changing that directly
        for thread in watch_channel.threads:
            starter_message = await thread.parent.fetch_message(thread.id)
            try:
                # index: 0    1         2                   3          4
                #     https: / / warned.username / 262913789375021056 /
                user_id = int(starter_message.embeds[0].author.url.split("/")[3])
                if user_id in watchlist_index_temp:
                    continue # only use the user's most recent watchlist thread (if ever there is a second thread) \\ or maybe it does the earliest one?
                watchlist_index_temp[user_id] = thread.id
            except (IndexError, AttributeError):
                pass
        else:
            async for thread in watch_channel.archived_threads(limit=None):
                starter_message = await thread.parent.fetch_message(thread.id)
                try:
                    user_id = int(starter_message.embeds[0].author.url.split("/")[3])
                    if user_id in watchlist_index_temp:
                        continue
                    watchlist_index_temp[user_id] = thread.id
                except (IndexError, AttributeError):
                    pass
        local_watchlist_index = watchlist_index_temp
        busy_updating_watchlist_index = False
    if busy_updating_watchlist_index:
        # wait until not busy anymore, in case a command triggers the function while it's still catching up
        await asyncio.sleep(1)
    return local_watchlist_index

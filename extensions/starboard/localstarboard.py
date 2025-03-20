import asyncio
from datetime import datetime, timezone

import discord

from resources.customs.bot import Bot


local_starboard_message_list_refresh_timestamp = datetime.fromtimestamp(0, timezone.utc)
STARBOARD_REFRESH_DELAY = 3000
local_starboard_message_list: list[discord.Message] = []
busy_updating_starboard_messages = False


async def get_or_fetch_starboard_messages(
        starboard_channel: discord.abc.GuildChannel | discord.abc.PrivateChannel | discord.Thread | None
) -> list[discord.Message]:
    """
    Fetch list of all starboard messages, unless it is already fetching: then it waits until the
    other instance of the fetching function is done and retrieves the cached list. The list is
    stored for STARBOARD_REFRESH_DELAY seconds.

    Parameters
    -----------
    starboard_channel: :class:`discord.abc.GuildChannel` | :class:`discord.abc.PrivateChannel` |
            :class:`discord.Thread` | :class:`None`
        The starboard channel to fetch messages from.

    Returns
    --------
    :class:`list[discord.Message]`:
        A list of starboard messages (sent by the bot) in the starboard channel.
    """
    global busy_updating_starboard_messages, local_starboard_message_list, \
        local_starboard_message_list_refresh_timestamp
    time_since_last_starboard_fetch = (
            datetime.now().astimezone() - local_starboard_message_list_refresh_timestamp
    ).total_seconds()
    if not busy_updating_starboard_messages and time_since_last_starboard_fetch > STARBOARD_REFRESH_DELAY:
        # refresh once every STARBOARD_REFRESH_DELAY seconds
        busy_updating_starboard_messages = True
        messages: list[discord.Message] = []
        async for star_message in starboard_channel.history(limit=None):
            messages.append(star_message)
        local_starboard_message_list = messages
        local_starboard_message_list_refresh_timestamp = datetime.now().astimezone()
        busy_updating_starboard_messages = False
    while busy_updating_starboard_messages:
        # wait until not busy anymore
        await asyncio.sleep(1)
    return local_starboard_message_list


def add_to_local_starboard(
        msg
):
    global local_starboard_message_list
    local_starboard_message_list.append(msg)


def delete_from_local_starboard(starboard_message_id: int) -> None:
    global local_starboard_message_list
    for i in range(len(local_starboard_message_list)):
        if local_starboard_message_list[i].id == starboard_message_id:
            del local_starboard_message_list[i]
            break

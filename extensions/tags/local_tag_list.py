import discord
from motor.core import AgnosticDatabase

from extensions.tags.database_tag_object import DatabaseTagObject
from resources.pymongo.database_keys import DatabaseKeys
from resources.pymongo.guild_customs_manager import (
    add_data, remove_data, get_data, get_all_data
)

local_tag_list: dict[int, dict[str, DatabaseTagObject]] = {}


def get_tag(
        guild: discord.Guild,
        tag_name: str,
) -> DatabaseTagObject | None:
    """
    Get a tag from the cache.

    :param guild: The guild to get the tag from.
    :param tag_name: The name of the tag.

    :return: A tag object or ``None`` if no tag with this name is found.
    """
    if guild.id in local_tag_list:
        if tag_name in local_tag_list[guild.id]:
            return local_tag_list[guild.id][tag_name]
    return None


def get_tags(
        guild: discord.Guild,
) -> dict[str, DatabaseTagObject]:
    """
    Get a server's tags from the cache.

    :param guild: The guild to get tags from.

    :return: A dictionary containing all tags registered in the guild.
    """
    if guild.id in local_tag_list:
        return local_tag_list[guild.id]
    return {}


async def create_tag(
        async_rina_db: AgnosticDatabase,
        guild: discord.Guild,
        tag_name: str,
        embed_title: str,
        embed_description: str,
        embed_color: tuple[int, int, int],
        report_to_staff: bool,
) -> None:
    """
    Create a new tag for the given guild.

    :param async_rina_db: The database to store the tag in.
    :param guild: The guild to add the tag to.
    :param tag_name: The unique name of the tag.
    :param embed_title: The title of the tag embed.
    :param embed_description: The description of the tag embed.
    :param embed_color: The color of the tag embed.
    :param report_to_staff: Whether sending this tag anonymously should
     be reported to staff.
    """
    global local_tag_list
    if len(embed_title) > 256:
        raise ValueError("Embed title too long.")
    if len(embed_description) > 4096:
        raise ValueError("Embed description too long.")
    if not all([0 <= c <= 255 for c in embed_color]):
        raise ValueError("Embed colors must be RGB values between 0 and 255.")

    embed_object = DatabaseTagObject(
        title=embed_title,
        description=embed_description,
        color=embed_color,
        report_to_staff=report_to_staff,
    )
    await add_data(
        async_rina_db,
        guild.id,
        DatabaseKeys.tag_list,
        tag_name,
        embed_object,
    )

    if guild.id not in local_tag_list:
        local_tag_list[guild.id] = {}

    local_tag_list[guild.id][tag_name] = embed_object


async def remove_tag(
        async_rina_db: AgnosticDatabase,
        guild: discord.Guild,
        tag_name: str
) -> bool:
    """
    Remove a tag from the database for a guild.

    :param async_rina_db: The database to remove the tag from.
    :param guild: The guild to remove the tag from.
    :param tag_name: The name of the tag to remove.
    :return: Whether there was a tag with this name.
    """
    global local_tag_list
    changed, _ = await remove_data(
        async_rina_db,
        guild.id,
        DatabaseKeys.tag_list,
        tag_name,
    )

    if guild.id not in local_tag_list:
        local_tag_list[guild.id] = {}

    if tag_name in local_tag_list[guild.id]:
        del local_tag_list[guild.id][tag_name]

    return changed


async def fetch_tags(
        async_rina_db: AgnosticDatabase,
        guild: discord.Guild,
) -> dict[str, DatabaseTagObject]:
    """
    Fetch tags in a guild from the database.
    :param async_rina_db: The database to fetch tags from.
    :param guild: The guild to fetch tags for.
    :return: A dictionary of tag names and the matching tag object in the
     given guild.
    """
    global local_tag_list
    data: dict[str, dict] | None = await get_data(
        async_rina_db,
        guild.id,
        DatabaseKeys.tag_list,
    )

    if data is None:
        return {}

    data = {name: DatabaseTagObject(**tag_data) for name, tag_data in data}
    local_tag_list[guild.id] = data
    return data


async def fetch_all_tags(
        async_rina_db: AgnosticDatabase,
) -> dict[int, dict[str, DatabaseTagObject]]:
    """
    Fetch all tags from the database.

    :param async_rina_db: The database to fetch tags with.
    :return: A dictionary of guild_ids, with a dictionary of tag names and
     their corresponding tag objects.
    """
    global local_tag_list
    data: dict[int, dict[str, dict]] = await get_all_data(
        async_rina_db,
        DatabaseKeys.tag_list,
    )

    for guild_id, tag_objects in data.items():
        tags = {}
        for tag_name, tag_data in tag_objects.items():
            tag_object = DatabaseTagObject(**tag_data)
            tags[tag_name] = tag_object
        local_tag_list[guild_id] = tags

    return local_tag_list

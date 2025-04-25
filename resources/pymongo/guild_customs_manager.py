from motor.core import AgnosticDatabase
from typing import TypeVar

from .utils import encode_field, decode_field

T = TypeVar('T', str, str)  # name / id (as string) (it's cheat-y oof)
V = TypeVar('V')


# Database format (a list of the following):
# {
#    guild_id: 12345678912345678,
#    data: dict[T, V]
# }

# Database properties:
# - Each guild_id is unique.
# - Every entry that has a 'guild_id' key must also contain a 'data' key.


async def add_data(
        async_rina_db: AgnosticDatabase,
        guild_id: int,
        database_name: str,
        key: T,
        value: V,
) -> tuple[bool, bool]:
    """
    Add data into a key for the given guild.

    :param async_rina_db: The database connection.
    :param guild_id: The id of the guild you want to add data for.
    :param database_name: The database to add data into.
    :param key: The key to store data to.
    :param value: The data to store.

    :return: A tuple of booleans: whether any documents were changed, and
     whether any new documents were created.
    """
    collection = async_rina_db[database_name]
    query = {"guild_id": guild_id}
    result = await collection.update_one(
        query,
        {"$set": {f"data.{encode_field(key)}": value}},
        upsert=True
    )
    return result.modified_count > 0, result.did_upsert


async def remove_data(
        async_rina_db: AgnosticDatabase,
        guild_id: int,
        database_name: str,
        key: T,
) -> tuple[bool, bool]:
    """
    Remove data at a key for the given guild.

    :param async_rina_db: The database connection.
    :param guild_id: The id of the guild you want to remove data for.
    :param database_name: The database to remove data from.
    :param key: The key in the data to remove.

    :return: A tuple of booleans: whether any documents were changed, and
     whether any new documents were created.
    """
    collection = async_rina_db[database_name]
    query = {"guild_id": guild_id}
    result = await collection.update_one(
        query,
        {"$unset": {f"data.{encode_field(key)}": ""}},
        # value "" is not used by MongoDB when unsetting.
        upsert=True
    )
    return result.modified_count > 0, result.did_upsert


async def update_data(
        async_rina_db: AgnosticDatabase,
        guild_id: int,
        database_name: str,
        data: dict[T, V],
) -> tuple[bool, bool]:
    """
    Store data for the given guild.

    :param async_rina_db: The database connection.
    :param guild_id: The id of the guild you want to store data for.
    :param database_name: The database to store data into.
    :param data: The data to store.

    :return: A tuple of booleans: whether any documents were changed, and
     whether any new documents were created.
    """
    collection = async_rina_db[database_name]
    query = {"guild_id": guild_id}
    encoded_data = {encode_field(k): v for k, v in data.items()}
    result = await collection.update_one(
        query,
        {"$set": {"data": encoded_data}},
        upsert=True
    )
    return result.modified_count > 0, result.did_upsert


async def get_data(
        async_rina_db: AgnosticDatabase,
        guild_id: int,
        database_name: str,
) -> dict[T, V] | None:
    """
    Fetch data for the given guild.

    :param async_rina_db: The database connection.
    :param guild_id: The id of the guild you want to fetch data for.
    :param database_name: The database to fetch data from.

    :return: The data in the database for the requested guild_id, or
     ``None`` if not found.
    """
    collection = async_rina_db[database_name]
    query = {"guild_id": guild_id}
    result = await collection.find_one(query)

    if result is None:
        return None
    decoded_data = {decode_field(k): v for k, v in result["data"].items()}
    return decoded_data


async def get_all_data(
        async_rina_db: AgnosticDatabase,
        database_name: str,
) -> dict[int, dict[T, V]]:
    """
    Fetch data for the given guild.

    :param async_rina_db: The database connection.
    :param database_name: The database to fetch data from.

    :return: The data in the database for the requested guild_id, or
     ``None`` if not found.
    """
    collection = async_rina_db[database_name]
    results = collection.find()

    data = {}
    async for result in results:
        guild_id = result["guild_id"]
        decoded_data = {decode_field(k): v for k, v in result["data"].items()}
        data[guild_id] = decoded_data

    return data

from __future__ import annotations

import types
import typing

import motor.core
from typing import TypedDict, Required, Any, TypeVar, get_args, get_origin, Union, Callable, Type, Optional

import discord
import pymongo.results

from resources.customs.bot import Bot

from extensions.settings.objects import ServerAttributes, ServerAttributeIds


GuildId = int
UserId = int
ChannelId = int
RoleId = int
EmojiId = int
TextChannelId = int
VoiceChannelId = int
CategoryChannelId = int
MessageableChannelId = int
MessageChannel = discord.TextChannel | discord.Thread

T = TypeVar('T')


def parse_id_generic(
        invalid_arguments: dict[str, str],
        invalid_argument_name: str,
        get_object_function: Callable[[int], T],
        object_id: int | None
) -> T:
    parsed_obj = None
    if object_id is not None:
        parsed_obj = get_object_function(object_id)
        if parsed_obj is None:
            invalid_arguments[invalid_argument_name] = str(object_id)
    return parsed_obj

def parse_list_id_generic(
        invalid_arguments: dict[str, str],
        invalid_argument_name: str,
        get_object_function: Callable[[int], T | None],
        object_ids: list[int] | None
) -> list[T]:
    parsed_objects: list[T] = []
    if object_ids is None:
        # Return early
        return parsed_objects

    invalid_object_ids: list[str] = []
    for object_id in object_ids:
        parsed_obj: T | None = get_object_function(object_id)
        if parsed_obj is None:
            invalid_object_ids.append(str(object_id))
        else:
            parsed_objects.append(parsed_obj)
    invalid_arguments.append(invalid_argument_name + f": [{','.join(invalid_object_ids)}]")
    return parsed_objects


def convert_old_settings_to_new(old_settings: dict[str, int | list[int]]) -> ServerAttributeIds:
    guild_id: GuildId = old_settings.get("guild_id")  # this one shouldn't ever be None
    if guild_id is None:
        raise ValueError("guild_id in this object was not found!")
    custom_vc_create_channel_id: VoiceChannelId | None = old_settings.get("vcHub", None)
    log_channel_id: MessageableChannelId | None = old_settings.get("vcLog", None)
    custom_vc_category_id: CategoryChannelId | None = old_settings.get("vcCategory", None)
    starboard_channel_id: TextChannelId | None = old_settings.get("starboardChannel", None)
    starboard_minimum_upvote_count: int | None = old_settings.get("starboardCountMinimum", None)
    bump_reminder_channel_id: MessageableChannelId | None = old_settings.get("bumpChannel", None)
    bump_reminder_role_id: RoleId | None = old_settings.get("bumpRole", None)
    poll_reaction_blacklisted_channel_ids: list[int] = old_settings.get("pollReactionsBlacklist", [])
    bump_reminder_bot_id: UserId | None = old_settings.get("bumpBot", None)
    starboard_blacklisted_channel_ids: list[int] = old_settings.get("starboardBlacklistedChannels", [])
    starboard_upvote_emoji_id: EmojiId | None = old_settings.get("starboardEmoji", None)
    starboard_minimum_vote_count_for_downvote_delete: int | None = old_settings.get("starboardDownvoteInitValue", None)
    voice_channel_logs_channel_id: MessageableChannelId | None = old_settings.get("vcActivityLogChannel", None)

    new_settings = {
        "guild_id": guild_id,
        "custom_vc_create_channel_id": custom_vc_create_channel_id,
        "log_channel_id": log_channel_id,
        "custom_vc_category_id": custom_vc_category_id,
        "starboard_channel_id": starboard_channel_id,
        "starboard_minimum_upvote_count": starboard_minimum_upvote_count,
        "bump_reminder_channel_id": bump_reminder_channel_id,
        "bump_reminder_role_id": bump_reminder_role_id,
        "poll_reaction_blacklisted_channel_ids": poll_reaction_blacklisted_channel_ids,
        "bump_reminder_bot_id": bump_reminder_bot_id,
        "starboard_blacklisted_channel_ids": starboard_blacklisted_channel_ids,
        "starboard_upvote_emoji_id": starboard_upvote_emoji_id,
        "starboard_minimum_vote_count_for_downvote_delete": starboard_minimum_vote_count_for_downvote_delete,
        "voice_channel_logs_channel_id": voice_channel_logs_channel_id,
    }
    return ServerAttributeIds(**new_settings)


class ServerSettings:
    database_key = "server_settings"

    @staticmethod
    async def migrate(async_rina_db: motor.core.AgnosticDatabase):
        """
        Migrate all data from the old guildInfo database to the new server_settings database.

        :param async_rina_db: The database to reference to look up the old and store the new database.
        :raise IndexError: No online database of the old version was found.
        """
        old_collection: motor.MotorCollection = await async_rina_db["guildInfo"]
        old_settings = old_collection.find()
        new_collection: motor.MotorCollection = await async_rina_db[ServerSettings.database_key]
        new_settings = []
        async for old_setting in old_settings:
            new_setting = convert_old_settings_to_new(old_setting)
            new_settings.append(new_setting)

        if new_settings:
            await new_collection.insert_many(new_settings)

    @staticmethod
    async def load_all(client: Bot, async_rina_db: motor.core.AgnosticDatabase, server_id: int) -> list[ServerSettings]:
        """
        Load all server settings from database and format into a ServerSettings object.
        :param async_rina_db: The database to reference to look up the database.
        :return: A list of ServerSettings matching all ServerAttributeIds stored in the database.
        """
        collection: motor.MotorCollection = await async_rina_db[ServerSettings.database_key]
        all_settings = await collection.find(query)
        server_settings: list[ServerSettings] = []
        async for setting in all_settings:
            server_id = setting["guild_id"]
            attributes = ServerAttributeIds(**setting)
            server_settings.append(ServerSettings.from_ids(client, server_id, attributes))
        return server_settings

    @staticmethod
    async def load(client: Bot, async_rina_db: motor.core.AgnosticDatabase, server_id: int) -> ServerSettings:
        collection: motor.MotorCollection = await async_rina_db[ServerSettings.database_key]
        query = {"guild_id": server_id}
        result = await collection.find_one(query)
        if result is None:
            attributes = ServerAttributeIds()
        else:
            attributes = ServerAttributeIds(**result)
        return ServerSettings.from_ids(client, server_id, attributes)

    # todo: perhaps a function to convert this back to ID version?
    # todo: perhaps a repair function to remove unknown/migrated keys from the database?

    async def add(self, async_rina_db: motor.core.AgnosticDatabase, parameter: str, value: Any) -> bool:
        if parameter not in ServerAttributeIds:
            raise KeyError(f"{parameter} is not a valid Server Attribute.")

        collection: motor.MotorCollection = await async_rina_db[ServerSettings.database_key]
        query = {"guild_id": self.server}
        update = {"$set": {parameter: value}}

        result = await collection.update_one(query, update, upsert=True)
        return result.modified_count > 0
        # todo: add new id to ServerSettings as correct Channel etc object

    @staticmethod
    def from_ids(
            client: Bot,
            server_id: int,
            attributes: ServerAttributeIds
    ) -> ServerSettings:
        invalid_arguments: dict[str, str | list[str]] = {}

        server = client.get_guild(server_id)
        if server is None:
            invalid_arguments.append(f"server_id: {server_id}")

        new_settings: dict[str, Any | None] = {k: None for k in ServerAttributes.__required_keys__}
        attribute_types: dict[str, Type[list | None] | Type[int | None]] = typing.get_type_hints(ServerAttributes)
        for attribute_pair in attributes.items():
            attribute = attribute_pair[0]
            attribute_value = attribute_pair[1]
            attribute_type = attribute_types[attribute]  # raises KeyError (but probably not, if the tests passed)
            if get_origin(attribute_type) is list:
                # original was: list[T]`. get_origin returns `list`.
                attribute_type = get_args(attribute_type)[0]  # get_args returns `T`
                if attribute_type is discord.Guild:
                    new_settings[attribute] = parse_list_id_generic(
                        invalid_arguments, attribute, client.get_guild, attribute_value
                    )
                if attribute_type is discord.Role:
                    new_settings[attribute] = parse_list_id_generic(
                        invalid_arguments, attribute, server.get_role, attribute_value
                    )
                if attribute_type is discord.abc.Messageable:
                    new_settings[attribute] = parse_list_id_generic(
                        invalid_arguments, attribute, client.get_channel, attribute_value
                    )
            else:
                if attribute_type is discord.Guild:
                    new_settings[attribute] = parse_id_generic(
                        invalid_arguments, attribute, client.get_guild, attribute_value)
                if attribute_type is discord.abc.Messageable:
                    new_settings[attribute] = parse_id_generic(
                        invalid_arguments, attribute, client.get_channel, attribute_value)
                if attribute_type is discord.User:
                    new_settings[attribute] = parse_id_generic(
                        invalid_arguments, attribute, client.get_user, attribute_value)
                if attribute_type is discord.Role:
                    new_settings[attribute] = parse_id_generic(
                        invalid_arguments, attribute, server.get_role, attribute_value)
                if attribute_type is discord.CategoryChannel:
                    # I think it's safe to assume the stored value was an object of the correct type in the first place.
                    new_settings[attribute] = parse_id_generic(
                        invalid_arguments, attribute, client.get_channel, attribute_value)
                if attribute_type is discord.VoiceChannel:
                    new_settings[attribute] = parse_id_generic(
                        invalid_arguments, attribute, client.get_channel, attribute_value)
                if attribute_type is discord.Emoji:
                    new_settings[attribute] = parse_id_generic(
                        invalid_arguments, attribute, client.get_emoji, attribute_value)
                if attribute_type is int:
                    new_settings[attribute] = attribute_value
                if attribute_type is str:
                    new_settings[attribute] = str(attribute_value)
                    pass

        if len(invalid_arguments) > 0:
            raise ValueError("Some server settings for {} are unset!\n" + ','.join(invalid_arguments))

        return ServerSettings(
            server=server,
            attributes=ServerAttributes(**new_settings)
        )

    def __init__(
            self, *,
            server: discord.Guild,
            attributes: ServerAttributes
    ):
        self.server = server
        self.attributes: ServerAttributes = attributes

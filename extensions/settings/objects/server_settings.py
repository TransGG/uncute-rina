from __future__ import annotations

import types
import typing

import motor.core
from typing import TypedDict, Required, Any, TypeVar, get_args, get_origin, Union, Callable, Type, Optional

import discord
import pymongo.results

from resources.customs.bot import Bot

from extensions.settings.objects import ServerAttributes, ServerAttributeIds, EnabledModules

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
        get_object_function: Callable[[int], T | None],
        object_id: int | None
) -> T | None:
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


def convert_old_settings_to_new(old_settings: dict[str, int | list[int]]) -> tuple[int, ServerAttributeIds]:
    """
    Migrate server settings from old settings to new ones.

    Parameters
    ----------
    old_settings: A dictionary of the old server settings.

    Returns
    -------
    A tuple of the guild_id and extracted server attribute ids.
    """
    guild_id: GuildId = old_settings.get("guild_id")
    if guild_id is None:
        # this one shouldn't ever be None
        raise ValueError("guild_id in this object was not found!")

    # Retrieve all previously-saved values
    custom_vc_create_channel_id: VoiceChannelId | None = old_settings.get("vcHub", None)
    log_channel_id: MessageableChannelId | None = old_settings.get("vcLog", None)
    custom_vc_category_id: CategoryChannelId | None = old_settings.get("vcCategory", None)
    starboard_channel_id: TextChannelId | None = old_settings.get("starboardChannel", None)
    starboard_minimum_upvote_count: int | None = old_settings.get("starboardCountMinimum", None)
    bump_reminder_channel_id: MessageableChannelId | None = old_settings.get("bumpChannel", None)
    bump_reminder_role_id: RoleId | None = old_settings.get("bumpRole", None)
    poll_reaction_blacklisted_channel_ids: list[int] = old_settings.get("pollReactionsBlacklist", None)
    bump_reminder_bot_id: UserId | None = old_settings.get("bumpBot", None)
    starboard_blacklisted_channel_ids: list[int] = old_settings.get("starboardBlacklistedChannels", None)
    starboard_upvote_emoji_id: EmojiId | None = old_settings.get("starboardEmoji", None)
    starboard_minimum_vote_count_for_downvote_delete: int | None = old_settings.get("starboardDownvoteInitValue", None)
    voice_channel_logs_channel_id: MessageableChannelId | None = old_settings.get("vcActivityLogChannel", None)

    # Format attributes in the new ServerAttributeIds format
    converted_settings = {
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

    # remove all Nones
    new_settings = {}
    for setting_pair in converted_settings.items():
        if setting_pair[1] is not None:
            new_settings[setting_pair[0]] = setting_pair[1]

    return guild_id, ServerAttributeIds(**new_settings)


class ServerSettingData(TypedDict):
    guild_id: int
    enabled_modules: EnabledModules
    attribute_ids: ServerAttributeIds


class ServerSettings:
    DATABASE_KEY = "server_settings"

    @staticmethod
    async def migrate(async_rina_db: motor.core.AgnosticDatabase):
        """
        Migrate all data from the old guildInfo database to the new server_settings database.

        :param async_rina_db: The database to reference to look up the old and store the new database.
        :raise IndexError: No online database of the old version was found.
        """
        old_collection: motor.core.AgnosticCollection = async_rina_db["guildInfo"]
        old_settings = old_collection.find()
        new_collection: motor.core.AgnosticCollection = async_rina_db[ServerSettings.DATABASE_KEY]
        new_settings = []
        async for old_setting in old_settings:
            new_setting: ServerSettingData = {}
            guild_id, attributes = convert_old_settings_to_new(old_setting)
            new_setting["guild_id"] = guild_id
            new_setting["attribute_ids"] = attributes
            new_setting["enabled_modules"] = EnabledModules()
            new_settings.append(new_setting)

        if new_settings:
            await new_collection.insert_many(new_settings)

    async def set_attribute(self, async_rina_db: motor.core.AgnosticDatabase, parameter: str, value: Any) -> bool:
        if "." in parameter or "$" in parameter:
            raise ValueError(f"Parameters are not allowed to contain '.' or '$'! (parameter: '{parameter}')")
        if parameter not in ServerAttributeIds:
            raise KeyError(f"'{parameter}' is not a valid Server Attribute.")

        collection: motor.MotorCollection = await async_rina_db[ServerSettings.DATABASE_KEY]
        query = {"guild_id": self.server}
        update = {"$set": {parameter: value}}

        result = await collection.update_one(query, update, upsert=True)
        return result.modified_count > 0
        # todo: add new id to ServerSettings as correct Channel etc object

    async def remove_attribute(self, async_rina_db: motor.core.AgnosticDatabase, parameter: str) -> bool:
        if "." in parameter or "$" in parameter:
            raise ValueError(f"Parameters are not allowed to contain '.' or '$'! (parameter: '{parameter}')")
        collection: motor.MotorCollection = await async_rina_db[ServerSettings.DATABASE_KEY]
        query = {"guild_id": self.server}
        update = {"$unset": {f"attribute_ids.{parameter}": ""}}

        result = await collection.update_one(query, update, upsert=True)
        return result.modified_count > 0
        # todo: add new id to ServerSettings as correct Channel etc object

    @staticmethod
    async def fetch_all(client: Bot, async_rina_db: motor.core.AgnosticDatabase) -> dict[int, ServerSettings]:
        """
        Load all server settings from database and format into a ServerSettings object.
        :param client: The client to use to retrieve matching attribute objects from ids.
        :param async_rina_db: The database to reference to look up the database.
        :return: A dictionary of guild_id and a tuple of the server's enabled modules and attributes.
        """
        collection: motor.MotorCollection = await async_rina_db[ServerSettings.DATABASE_KEY]
        settings_data = await collection.find()

        server_settings: dict[int, ServerSettings] = {}
        async for setting in settings_data:
            server_setting = ServerSettings.load(client, setting)
            server_settings[server_setting.guild.id] = server_setting

        return server_settings

    @staticmethod
    async def fetch(client: Bot, async_rina_db: motor.core.AgnosticDatabase, guild_id: int) -> ServerSettings:
        """
        Load a given guild_id's settings from database and format into a ServerSettings object.
        Parameters
        ----------
        client: The client to use to retrieve matching attributes from ids.
        async_rina_db: The database to reference to look up the database.
        guild_id: The guild_id to look up.

        Returns
        -------
        A ServerSettings object, corresponding to the given guild_id.
        """
        collection: motor.MotorCollection = await async_rina_db[ServerSettings.DATABASE_KEY]
        query = {"guild_id": guild_id}
        result: ServerSettingData | None = await collection.find_one(query)
        if result is None:
            raise KeyError(f"Guild '{guild_id}' has no data yet!")

        return ServerSettings.load(client, result)

    @staticmethod
    def load(client: Bot, settings: ServerSettingData) -> ServerSettings:
        """
        Load all server settings from database and format into a ServerSettings object.

        Parameters
        -----------
        client: The client to use to retrieve matching attribute objects from ids.
        settings: The settings object to load.

        Returns
        --------
        A ServerSettings object with the setting's retrieved guild, enabled modules, and attributes.
        """
        guild_id = settings["guild_id"]
        enabled_modules = settings["enabled_modules"]
        attribute_ids = ServerAttributeIds(**settings["attribute_ids"])
        guild, attributes = ServerSettings.get_attributes(client, guild_id, attribute_ids)
        return ServerSettings(
            guild=guild,
            enabled_modules=enabled_modules,
            attributes=attributes
        )

    # todo: perhaps a repair function to remove unknown/migrated keys from the database?

    @staticmethod
    def get_attributes(
            client: Bot,
            guild_id: int,
            attributes: ServerAttributeIds
    ) -> tuple[discord.Guild, ServerAttributes]:
        """
        Load the guild and all attributes from the given ids, using the given client.
        Parameters
        ----------
        client: The client to use to retrieve matching attribute objects from ids.
        guild_id: The guild id of the guild of the server attributes.
        attributes: The ids of the attributes to load.

        Returns
        -------
        A tuple of the loaded guild and its attributes, corresponding with the given ids.

        Raises
        -------
        NotImplementedError: If a key in ServerAttributes does not yet have a parsing function assigned to it.
        ValueError: The given ServerAttributeIds contains ids that can't be converted to their corresponding
         ServerAttributes object.
        """
        invalid_arguments: dict[str, str | list[str]] = {}

        server = client.get_guild(guild_id)
        if server is None:
            invalid_arguments.append(f"guild_id: {guild_id}")

        new_settings: dict[str, Any | None] = {k: None for k in ServerAttributes.__required_keys__}
        attribute_types: dict[str, Type[list | None] | Type[int | None]] = typing.get_type_hints(ServerAttributes)
        for attribute_pair in attributes.items():
            attribute = attribute_pair[0]
            attribute_value = attribute_pair[1]
            attribute_type = attribute_types[attribute]  # raises KeyError (but probably not, if the tests passed)
            if get_origin(attribute_type) is list:
                # original was: `list[T]`. get_origin returns `list`.
                attribute_type = get_args(attribute_type)[0]  # get_args returns `T`
                strategy = parse_list_id_generic
            else:
                strategy = parse_id_generic

            func = None
            if attribute_type is discord.Guild:
                func = client.get_guild
            if attribute_type is discord.abc.Messageable:
                func = client.get_channel
            if attribute_type is discord.User:
                func = client.get_user
            if attribute_type is discord.Role:
                func = server.get_role
            if attribute_type is discord.CategoryChannel:
                # I think it's safe to assume the stored value was an object of the correct type in the first place.
                #  As in, it's a CategoryChannel id, not a VoiceChannel id.
                func = client.get_channel
            if attribute_type is discord.VoiceChannel:
                func = client.get_channel
            if attribute_type is discord.Emoji:
                func = client.get_emoji
            if attribute_type is int:
                strategy = None
                new_settings[attribute] = attribute_value
            if attribute_type is str:
                strategy = None
                new_settings[attribute] = str(attribute_value)

            if strategy is not None:
                if func is None:
                    raise NotImplementedError(f"Attribute '{attribute}' of type '{attribute_type}' could not be retrieved.")
                new_settings[attribute] = strategy(
                    invalid_arguments, attribute, func, attribute_value
                )

        if len(invalid_arguments) > 0:
            raise ValueError("Some server settings for {} are unset!\n" + ','.join(invalid_arguments))

        return server, ServerAttributes(**new_settings)

    def __init__(
            self, *,
            guild: discord.Guild,
            enabled_modules: EnabledModules,
            attributes: ServerAttributes
    ):
        self.guild = guild,
        self.enabled_modules = enabled_modules
        self.attributes = attributes

from __future__ import annotations

import types
import typing
import warnings

import motor.core
from typing import TypedDict, Required, Any, TypeVar, get_args, get_origin, Union, Callable, Type, Optional, Awaitable

import discord
import pymongo.results

from .serverattributes import ServerAttributes
from .serverattributeids import ServerAttributeIds
from .enabled_modules import EnabledModules

if typing.TYPE_CHECKING:
    from resources.customs.bot import Bot


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


async def parse_id_generic(
        invalid_arguments: dict[str, str],
        invalid_argument_name: str,
        get_object_function: Callable[[int], Awaitable[T | None]],
        object_id: int | None
) -> T | None:
    parsed_obj: T | None = None
    if object_id is not None:
        try:
            parsed_obj = await get_object_function(object_id)
        except (discord.NotFound, discord.HTTPException, discord.Forbidden, discord.InvalidData) as ex:
            invalid_arguments[invalid_argument_name] = f"{ex.__class__.__name__}: {object_id}"
        else:
            if parsed_obj is None:
                invalid_arguments[invalid_argument_name] = str(object_id)
    return parsed_obj


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
        "custom_vc_create_channel": custom_vc_create_channel_id,
        "log_channel": log_channel_id,
        "custom_vc_category": custom_vc_category_id,
        "starboard_channel": starboard_channel_id,
        "starboard_minimum_upvote_count": starboard_minimum_upvote_count,
        "bump_reminder_channel": bump_reminder_channel_id,
        "bump_reminder_role": bump_reminder_role_id,
        "poll_reaction_blacklisted_channels": poll_reaction_blacklisted_channel_ids,
        "bump_reminder_bot": bump_reminder_bot_id,
        "starboard_blacklisted_channels": starboard_blacklisted_channel_ids,
        "starboard_upvote_emoji": starboard_upvote_emoji_id,
        "starboard_minimum_vote_count_for_downvote_delete": starboard_minimum_vote_count_for_downvote_delete,
        "voice_channel_logs_channel": voice_channel_logs_channel_id,
    }

    # remove all Nones
    new_settings = {k:v for k,v in converted_settings.items() if v is not None}

    return guild_id, ServerAttributeIds(**new_settings)


def get_attribute_type(attribute_key: str) -> tuple[type | None, bool]:
    """
    Get the type of a given attribute.

    Parameters
    ----------
    attribute_key: The attribute to get the type of.

    Returns
    -------
    A tuple of the type of the attribute (or None if the attribute wasn't found) and whether the attribute was
     in a list.
    """
    attribute_types = typing.get_type_hints(ServerAttributes)
    attribute_type = None
    attribute_in_list = False
    if attribute_key in ServerAttributes.__annotations__:
        attribute_type = attribute_types[attribute_key]
        if typing.get_origin(attribute_type) is typing.types.UnionType:  # typing.Union != typing.types.UnionType :/
            # original was: `list[T] | None` (`Union[list[T], None]`).
            #   get_origin returns `<class 'types.UnionType'>`
            #   get_args   returns `(list[T], <class 'NoneType'>)`.
            attribute_type = typing.get_args(attribute_type)[0]
        if typing.get_origin(attribute_type) is list:
            # original was `list[T]`. get_args returns `T`
            attribute_type = typing.get_args(attribute_type)[0]
            attribute_in_list = True
    return attribute_type, attribute_in_list


async def parse_attribute(
        client: discord.Client,
        guild: discord.Guild,
        attribute_key: str,
        attribute_value: str,
        *,
        invalid_arguments: dict[str, str | list[str]] | None = None
) -> object | None:
    """
    Parse the attribute value as ServerAttribute based on the given attribute key.

    :param client: The client to get the attribute from.
    :param guild: The guild to get a potential discord.Role from.
    :param attribute_key: The key of the attribute type to parse it to.
    :param attribute_value: The attribute value to parse.
    :param invalid_arguments: An optional dictionary tracking previously unparseable arguments.
    :return: The parsed value, or None if not found.
    """
    if invalid_arguments is None:
        invalid_arguments = {}

    attribute_type, _ = get_attribute_type(attribute_key)
    func = None
    if attribute_type is discord.Guild:
        func = client.fetch_guild
    if attribute_type is discord.abc.Messageable:
        func = client.fetch_channel
    if attribute_type is discord.User:
        func = client.fetch_user
    if attribute_type is discord.Role:
        func = guild.fetch_role
    if attribute_type is discord.CategoryChannel:
        # I think it's safe to assume the stored value was an object of the correct type in the first place.
        #  As in, it's a CategoryChannel id, not a VoiceChannel id.
        func = client.fetch_channel
    if attribute_type is discord.VoiceChannel:
        func = client.fetch_channel
    if attribute_type is discord.Emoji:
        func = guild.fetch_emoji
    if attribute_type is int:
        func = None
    if attribute_type is str:
        return str(attribute_value)

    try:
        attribute_value_id = int(attribute_value)
        parsed_attribute = attribute_value_id
    except ValueError:
        return None

    if func is not None:
        parsed_attribute = await parse_id_generic(
            invalid_arguments, attribute_key, func, attribute_value_id
        )
    return parsed_attribute


class ParseError(ValueError):
    def __init__(self, message):
        self.message = message


class ServerSettingData(TypedDict):
    guild_id: int
    enabled_modules: EnabledModules
    attribute_ids: ServerAttributeIds


class ServerSettings:
    DATABASE_KEY = "server_settings"

    @staticmethod
    def get_original(attribute: T) -> T | tuple[str | None, int | None] | list[T | tuple[str | None, int | None]]:
        def get_name_or_id_maybe(attribute1: T) -> T | tuple[str | None, int | None]:
            name = None
            a_id = None
            if hasattr(attribute1, "name"):
                name = attribute1.name
            if hasattr(attribute1, "id"):
                a_id = attribute1.id
            if name or a_id:
                return name, a_id
            else:
                return attribute1

        if type(attribute) is list:
            output = []
            for att in attribute:
                output.append(get_name_or_id_maybe(att))
            return output
        return get_name_or_id_maybe(attribute)


    @staticmethod
    async def get_entry(async_rina_db: motor.core.AgnosticDatabase, guild_id: int) -> ServerSettingData | None:
        """
        Retrieve a database entry for the given guild ID.

        Parameters
        ----------
        async_rina_db: The database with which to retrieve the entry.
        guild_id: The guild id of the guild to retrieve the entry for.

        Returns
        -------
        A ServerSettingData or None if there is no entry for the given guild.
        """
        collection = async_rina_db[ServerSettings.DATABASE_KEY]
        query = {"guild_id": guild_id}
        result: ServerSettingData | None = await collection.find_one(query)
        return result

    @staticmethod
    async def migrate(async_rina_db: motor.core.AgnosticDatabase):
        """
        Migrate all data from the old guildInfo database to the new server_settings database.

        :param async_rina_db: The database to reference to look up the old and store the new database.
        :raise IndexError: No online database of the old version was found.
        """
        old_collection = async_rina_db["guildInfo"]
        new_collection = async_rina_db[ServerSettings.DATABASE_KEY]
        new_settings = []
        async for old_setting in old_collection.find():
            new_setting: ServerSettingData = {}
            guild_id, attributes = convert_old_settings_to_new(old_setting)
            new_setting["guild_id"] = guild_id
            new_setting["attribute_ids"] = attributes
            new_setting["enabled_modules"] = EnabledModules()
            new_settings.append(new_setting)

        if new_settings:
            await new_collection.insert_many(new_settings)

    @staticmethod
    async def set_attribute(
            async_rina_db: motor.core.AgnosticDatabase,
            guild_id: int,
            parameter: str,
            value: Any
    ) -> tuple[bool, bool]:
        if "." in parameter or "$" in parameter:
            raise ValueError(f"Parameters are not allowed to contain '.' or '$'! (parameter: '{parameter}')")
        if parameter not in ServerAttributeIds.__annotations__:
            raise KeyError(f"'{parameter}' is not a valid Server Attribute.")

        collection = async_rina_db[ServerSettings.DATABASE_KEY]
        query = {"guild_id": guild_id}
        update = {"$set": {f"attribute_ids.{parameter}": value}}

        result = await collection.update_one(query, update, upsert=True)
        # result.did_upsert -> if yes, make new ServerSettings?
        # result.raw_result
        return result.modified_count > 0, result.did_upsert
        # todo: add new id to ServerSettings as correct Channel etc object

    @staticmethod
    async def remove_attribute(
            async_rina_db: motor.core.AgnosticDatabase,
            guild_id: int,
            parameter: str
    ) -> tuple[bool, bool]:
        if "." in parameter or "$" in parameter:
            raise ValueError(f"Parameters are not allowed to contain '.' or '$'! (parameter: '{parameter}')")
        collection = async_rina_db[ServerSettings.DATABASE_KEY]
        query = {"guild_id": guild_id}
        update = {"$unset": {f"attribute_ids.{parameter}": ""}}  # value "" is not used by MongoDB when unsetting.

        result = await collection.update_one(query, update, upsert=True)
        return result.modified_count > 0, result.did_upsert
        # todo: add new id to ServerSettings as correct Channel etc object

    @staticmethod
    async def set_module_state(
            async_rina_db: motor.core.AgnosticDatabase,
            guild_id: int,
            parameter: str,
            value: bool
    ) -> tuple[bool, bool]:
        if "." in parameter or "$" in parameter:
            raise ValueError(f"Parameters are not allowed to contain '.' or '$'! (parameter: '{parameter}')")
        if parameter not in EnabledModules.__annotations__:
            raise KeyError(f"'{parameter}' is not a valid Module.")
        if type(value) is not bool:
            raise TypeError(f"'{parameter}' must be a boolean, not '{type(value).__name__}'.")

        collection = async_rina_db[ServerSettings.DATABASE_KEY]
        query = {"guild_id": guild_id}
        update = {"$set": {f"enabled_modules.{parameter}": value}}

        result = await collection.update_one(query, update, upsert=True)
        # result.did_upsert -> if yes, make new ServerSettings?
        # result.raw_result
        return result.modified_count > 0, result.did_upsert
        # todo: update ServerSettings object to use new module state.

    @staticmethod
    async def fetch_all(client: Bot) -> dict[int, ServerSettings]:
        """
        Load all server settings from database and format into a ServerSettings object.
        :param client: The bot to use to retrieve matching attribute objects from ids, and for async_rina_db
        :return: A dictionary of guild_id and a tuple of the server's enabled modules and attributes.
        """
        collection = client.async_rina_db[ServerSettings.DATABASE_KEY]
        settings_data = collection.find()

        server_settings: dict[int, ServerSettings] = {}
        async for setting in settings_data:
            setting: ServerSettingData
            try:
                server_setting = await ServerSettings.load(client, setting)
                server_settings[server_setting.guild.id] = server_setting
            except ParseError as ex:
                warnings.warn(f"ParseError for {setting["guild_id"]}: " + ex.message)

        return server_settings

    @staticmethod
    async def fetch(client: Bot, guild_id: int) -> ServerSettings:
        """
        Load a given guild_id's settings from database and format into a ServerSettings object.
        Parameters
        ----------
        client: The bot to use to retrieve matching attributes from ids, and for async_rina_db
        guild_id: The guild_id to look up.

        Returns
        -------
        A ServerSettings object, corresponding to the given guild_id.

        Raises
        ------
        KeyError: If the given guild_id has no data yet.
        ParseError: If values from the database could not be parsed.
        """
        result = await ServerSettings.get_entry(client.async_rina_db, guild_id)
        if result is None:
            raise KeyError(f"Guild '{guild_id}' has no data yet!")

        return await ServerSettings.load(client, result)

    @staticmethod
    async def load(client: discord.Client, settings: ServerSettingData) -> ServerSettings:
        """
        Load all server settings from database and format into a ServerSettings object.

        Parameters
        -----------
        client: The client to use to retrieve matching attribute objects from ids.
        settings: The settings object to load.

        Returns
        --------
        A ServerSettings object with the setting's retrieved guild, enabled modules, and attributes.

        Raises
        ------
        ParseError: If attributes in the data object could not be parsed.
        """
        guild_id = settings["guild_id"]
        enabled_modules = settings["enabled_modules"]
        attribute_ids = ServerAttributeIds(**settings["attribute_ids"])
        guild, attributes = await ServerSettings.get_attributes(client, guild_id, attribute_ids)
        return ServerSettings(
            guild=guild,
            enabled_modules=enabled_modules,
            attributes=attributes
        )

    # todo: perhaps a repair function to remove unknown/migrated keys from the database?

    @staticmethod
    async def get_attributes(
            client: discord.Client,
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
        ParseError: The given ServerAttributeIds contains ids that can't be converted to their corresponding
         ServerAttributes object.
        """
        invalid_arguments: dict[str, str | list[str]] = {}

        guild = client.get_guild(guild_id)
        if guild is None:
            invalid_arguments["guild_id"] = str(guild_id)
            raise ParseError("Some server settings could not be parsed: " + ', '.join(
                [f"{k}:{v}" for k, v in invalid_arguments.items()]))

        new_settings: dict[str, Any | None] = {k: None for k in ServerAttributes.__annotations__}
        for attribute, attribute_value in attributes.items():
            if type(attribute_value) is list:
                parsed_values = []
                for value in attribute_value:
                    parsed_value = await parse_attribute(
                        client, guild, attribute, value, invalid_arguments=invalid_arguments)
                    if parsed_value is not None:
                        parsed_values.append(parsed_value)
            else:
                new_settings[attribute] = await parse_attribute(
                    client, guild, attribute, attribute_value, invalid_arguments=invalid_arguments
                )

        if invalid_arguments:
            raise ParseError("Some server settings could not be parsed: \n- " + '\n- '.join(
                [f"{k}: {v}" for k, v in invalid_arguments.items()]))

        return guild, ServerAttributes(**new_settings)

    def __init__(
            self, *,
            guild: discord.Guild,
            enabled_modules: EnabledModules,
            attributes: ServerAttributes
    ):
        self.guild = guild
        self.enabled_modules = enabled_modules
        self.attributes = attributes

    async def reload(self, client: Bot) -> None:
        """
        Reload the server settings object to fetch and parse the latest server attribute ids from the database.

        Parameters
        ----------
        client: The client with which to get roles and fetch from the database.

        Raises
        ------
        ParseError: If attributes in the data object could not be parsed.
        """
        state = await ServerSettings.fetch(client, self.guild.id)
        self.guild = state.guild  # just get the latest stuff, I guess.
        self.attributes = state.attributes
        self.enabled_modules = state.enabled_modules

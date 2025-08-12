from __future__ import annotations

import typing

import motor.core
from typing import TypedDict, Any, TypeVar, Callable, TypeAliasType
from types import UnionType

import discord

from resources.utils.debug import debug, DebugColor
from .server_attributes import ServerAttributes, GuildAttributeType
from .server_attribute_ids import ServerAttributeIds
from .enabled_modules import EnabledModules

if typing.TYPE_CHECKING:
    from resources.customs import Bot


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
        get_object_function: Callable[[int], GuildAttributeType | None],
        object_id: int | None
) -> GuildAttributeType | None:
    parsed_obj: GuildAttributeType | None = None
    if object_id is not None:
        parsed_obj = get_object_function(object_id)
    return parsed_obj


def get_attribute_type(attribute_key: str) -> tuple[list[type] | None, bool]:
    """
    Get the type of a given attribute.

    :param attribute_key: The attribute to get the type of.

    :return A tuple of the type of the attribute (or None if the
     attribute wasn't found) and whether the attribute was in a list.
    """
    attribute_types = typing.get_type_hints(ServerAttributes)
    attribute_type: list[type] | None = None
    attribute_in_list = False
    if attribute_key in ServerAttributes.__annotations__:
        attribute_type = attribute_types[attribute_key]
        # typing.Union != types.UnionType :/
        #  typing.Union is for `Union[int, str]`
        #  types.UnionType is for `int | str`
        if (typing.get_origin(attribute_type) is UnionType
                or typing.get_origin(attribute_type) is TypeAliasType):
            # The original was: `type1 | type2 | None`.
            #   get_origin returns `<class 'UnionType'>`
            #   get_args returns `(<class 'type1'>, <class 'type2'>,
            #    <class 'NoneType'>)`.
            attribute_type = [t for t in typing.get_args(attribute_type)
                              if t is not type(None)]
        elif typing.get_origin(attribute_type) is list:
            # original was `list[T]`. get_args returns `T`
            attribute_type_list = [
                typing.get_args(attribute_type)
                if type(t) is UnionType
                else (typing.get_args(t.__value__)
                      if type(t) is TypeAliasType
                      else [t])
                for t in typing.get_args(attribute_type)
            ]
            attribute_type = [attribute
                              for type_list in attribute_type_list
                              for attribute in type_list]
            # should not have any None's
            attribute_in_list = True
        else:
            raise NotImplementedError(
                f"Type of {attribute_key} is not supported")
    return attribute_type, attribute_in_list


def parse_attribute(
        client: discord.Client,
        guild: discord.Guild,
        attribute_key: str,
        attribute_value: str | int | None,
        *,
        invalid_arguments: dict[str, str] | None = None
) -> GuildAttributeType | None:
    """
    Parse the attribute value as ServerAttribute based on the given
    attribute key.

    :param client: The client to get the attribute from.
    :param guild: The guild to get a potential discord.Role from.
    :param attribute_key: The key of the attribute type to parse it to.
    :param attribute_value: The attribute value to parse.
    :param invalid_arguments: An optional dictionary tracking previously
     unparseable arguments.
    :return: The parsed value, or None if not found.
    :raise ParseError: If the attribute could not be parsed or is of the
     wrong type.
    """
    attribute_type, _ = get_attribute_type(attribute_key)
    if attribute_type is None:
        raise ParseError(f"No type found for attribute key {attribute_key}")

    def is_attribute_type(val: type):
        f = any(
            val in typing.get_args(i.__value__)
            if type(i) is TypeAliasType
            else val is i
            for i in attribute_type
        )
        return f

    funcs: set[Callable[[int], GuildAttributeType | None]] = set()

    if is_attribute_type(discord.Guild):
        funcs.add(client.get_guild)
    if (is_attribute_type(discord.abc.GuildChannel)
            or is_attribute_type(discord.Thread)):
        # Could use isinstance(), but I feel like it should only
        #  parse if the type matches exactly.
        funcs.add(guild.get_channel_or_thread)
    if is_attribute_type(discord.abc.Messageable):
        funcs.add(client.get_channel)
    if is_attribute_type(discord.TextChannel):
        funcs.add(client.get_channel)
    if is_attribute_type(discord.User):
        funcs.add(client.get_user)
    if is_attribute_type(discord.Role):
        funcs.add(guild.get_role)
    if is_attribute_type(discord.CategoryChannel):
        # I think it's safe to assume the stored value was an object of
        #  the correct type in the first place. As in, it's a
        #  CategoryChannel id, not a VoiceChannel id.
        funcs.add(client.get_channel)
    if is_attribute_type(discord.channel.VoiceChannel):
        funcs.add(client.get_channel)
    if is_attribute_type(discord.Emoji):
        funcs.add(guild.get_emoji)
    if is_attribute_type(int):
        def get_int(x: int) -> int:
            """Helper to just return the already-parsed int object."""
            # this function exists because apparently `lambda x: x` is
            #  bad for tracebacks or something.
            return x
        # the value should already be an int anyway
        funcs.add(get_int)
    if is_attribute_type(str):
        if attribute_value is None:
            return attribute_value
        return str(attribute_value)

    if len(funcs) == 0:
        raise ParseError(
            f"Type '{attribute_type}' of attribute "
            f"{attribute_key} could not be parsed. "
            f"(Attribute value: '{attribute_value}')"
        )

    if attribute_value is None:
        # to prevent TypeError from int(None) later.
        return None
    try:
        # all of these require a <object>.id (or the attribute itself
        #  is an int)
        attribute_value_id = int(attribute_value)
    except ValueError:
        return None

    parsed_attribute = None
    for func in funcs:
        parsed_attribute = parse_id_generic(
            func,
            attribute_value_id,
        )
        if parsed_attribute is not None:
            break

    if parsed_attribute is None and invalid_arguments is not None:
        invalid_arguments[attribute_key] = str(attribute_value_id)

    return parsed_attribute


class ParseError(ValueError):
    def __init__(self, message):
        self.message = message


class ServerSettingData(TypedDict):
    guild_id: int
    enabled_modules: EnabledModules
    attribute_ids: ServerAttributeIds


NameAndIdData = tuple[str | None, int | None]


class ServerSettings:
    DATABASE_KEY = "server_settings"

    @staticmethod
    def get_original(
            attribute: T | list[T]
    ) -> T | NameAndIdData | list[T | NameAndIdData]:
        """Get the name and id of the attribute (or attributes)"""
        def get_name_or_id_maybe(attribute1: T) -> T | NameAndIdData:
            """Helper to get the name and id attribute of an object.

            If both name and id are none, it will return the given
            object.
            """
            name = getattr(attribute1, "name", None)
            a_id = getattr(attribute1, "id", None)
            if name or a_id:
                return name, a_id
            else:
                return attribute1

        if isinstance(attribute, list):
            output = []
            for att in attribute:
                output.append(get_name_or_id_maybe(att))
            return output
        return get_name_or_id_maybe(attribute)

    @staticmethod
    async def get_entry(
            async_rina_db: motor.core.AgnosticDatabase,
            guild_id: int
    ) -> ServerSettingData | None:
        """
        Retrieve a database entry for the given guild ID.

        :param async_rina_db: The database with which to retrieve
         the entry.
        :param guild_id: The guild id of the guild to retrieve the
         entry for.
        :return A ServerSettingData or None if there is no entry for
         the given guild.
        """
        collection = async_rina_db[ServerSettings.DATABASE_KEY]
        query = {"guild_id": guild_id}
        result: ServerSettingData | None = await collection.find_one(query)
        return result

    # @staticmethod
    # async def migrate(async_rina_db: motor.core.AgnosticDatabase):
    #     """
    #     Migrate all data from the old guildInfo database to the new
    #     server_settings database.
    #
    #     :param async_rina_db: The database to reference to look up the
    #      old and store the new database.
    #     :raise IndexError: No online database of the old version
    #      was found.
    #     """
    #     old_collection = async_rina_db["guildInfo"]
    #     new_collection = async_rina_db[ServerSettings.DATABASE_KEY]
    #     new_settings = []
    #     async for old_setting in old_collection.find():
    #         guild_id, attributes = convert_old_settings_to_new(
    #             old_setting)
    #         new_setting = ServerSettingData(
    #             guild_id=guild_id,
    #             attribute_ids=attributes,
    #             enabled_modules=EnabledModules(),
    #         )
    #         new_settings.append(new_setting)
    #
    #     if new_settings:
    #         await new_collection.insert_many(new_settings)

    @staticmethod
    async def set_attribute(
            async_rina_db: motor.core.AgnosticDatabase,
            guild_id: int,
            parameter: str,
            value: Any
    ) -> tuple[bool, bool]:
        if "." in parameter or parameter.startswith("$"):
            raise ValueError(
                f"Parameters are not allowed to contain '.' or "
                f"start with '$'! (parameter: '{parameter}')"
            )  # todo: check if i sanitize the input when responding.
        if parameter not in ServerAttributeIds.__annotations__:
            raise KeyError(f"'{parameter}' is not a valid Server Attribute.")

        collection = async_rina_db[ServerSettings.DATABASE_KEY]
        query = {"guild_id": guild_id}
        update = {"$set": {f"attribute_ids.{parameter}": value}}

        result = await collection.update_one(query, update, upsert=True)
        # result.did_upsert -> if yes, make new ServerSettings?
        # result.raw_result
        return result.modified_count > 0, result.did_upsert

    @staticmethod
    async def remove_attribute(
            async_rina_db: motor.core.AgnosticDatabase,
            guild_id: int,
            parameter: str
    ) -> tuple[bool, bool]:
        if "." in parameter or parameter.startswith("$"):
            raise ValueError(
                f"Parameters are not allowed to contain '.' or "
                f"start with '$'! (parameter: '{parameter}')"
            )  # todo: check if i sanitize the input when responding.
        collection = async_rina_db[ServerSettings.DATABASE_KEY]
        query = {"guild_id": guild_id}
        update = {"$unset": {f"attribute_ids.{parameter}": ""}}
        # value ("") is not used by MongoDB when unsetting.

        result = await collection.update_one(query, update, upsert=True)
        return result.modified_count > 0, result.did_upsert

    @staticmethod
    async def set_module_state(
            async_rina_db: motor.core.AgnosticDatabase,
            guild_id: int,
            module: str,
            value: bool
    ) -> tuple[bool, bool]:
        """
        Set the state of the given module.

        :param async_rina_db: The database to edit the module state.
        :param guild_id: The id of the guild whose module state you want
         to change.
        :param module: The name of the module to set.
        :param value: The (new) value of the module.
        :return: A tuple of booleans: whether any documents were
         changed, and whether any new documents were created.
        """
        if "." in module or module.startswith("$"):
            raise ValueError(f"Parameters are not allowed to contain '.'"
                             f" or start with '$'! (parameter: '{module}')")
        if module not in EnabledModules.__annotations__:
            raise KeyError(f"'{module}' is not a valid Module.")
        if type(value) is not bool:
            raise TypeError(
                f"'{module}' must be a boolean, not "
                f"'{type(value).__name__}'."
            )

        collection = async_rina_db[ServerSettings.DATABASE_KEY]
        query = {"guild_id": guild_id}
        update = {"$set": {f"enabled_modules.{module}": value}}

        result = await collection.update_one(query, update, upsert=True)
        # result.did_upsert -> if yes, make new ServerSettings?
        # result.raw_result
        return result.modified_count > 0, result.did_upsert

    @staticmethod
    async def fetch_all(client: Bot) -> dict[int, ServerSettings]:
        """
        Load all server settings from database and format into a
        ServerSettings object.

        :param client: The bot to use to retrieve matching attribute
         objects from ids, and for async_rina_db
        :return: A dictionary of guild_id and a tuple of the server's
         enabled modules and attributes.
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
                debug(
                    f"ParseError for {setting["guild_id"]}:\n"
                    + ex.message
                    + "\n",
                    DebugColor.lightred,
                )

        return server_settings

    @staticmethod
    async def fetch(client: Bot, guild_id: int) -> ServerSettings:
        """
        Load a given guild_id's settings from database and format into
        a ServerSettings object.

        :param client: The bot to use to retrieve matching attributes
         from ids, and for async_rina_db.
        :param guild_id: The guild_id to look up.

        :return: A ServerSettings object, corresponding to the
         given guild_id.

        :raise KeyError: If the given guild_id has no data yet.
        :raise ParseError: If values from the database could not
         be parsed.
        """
        result = await ServerSettings.get_entry(client.async_rina_db, guild_id)
        if result is None:
            raise KeyError(f"Guild '{guild_id}' has no data yet!")

        return await ServerSettings.load(client, result)

    @staticmethod
    async def load(
            client: Bot,
            settings: ServerSettingData
    ) -> ServerSettings:
        """
        Load all server settings from database and format into a
        ServerSettings object.

        .. note::

            This function is async only to send a crash log to the server
            in question.

        :param client: The client to use to retrieve matching attribute
         objects from ids.
        :param settings: The settings object to load.

        :return A ServerSettings object with the setting's retrieved
         guild, enabled modules, and attributes.

        :raise ParseError: If attributes in the data object could not
         be parsed.
        """
        guild_id = settings["guild_id"]
        enabled_modules = settings["enabled_modules"]
        attribute_ids = ServerAttributeIds(**settings["attribute_ids"])
        guild, attributes = await ServerSettings.get_attributes(
            client, guild_id, attribute_ids
        )
        return ServerSettings(
            guild=guild,
            enabled_modules=enabled_modules,
            attributes=attributes
        )

    # todo: perhaps a repair function to remove unknown/migrated keys
    #  from the database?

    @staticmethod
    async def get_attributes(
            client: Bot,
            guild_id: int,
            attributes: ServerAttributeIds
    ) -> tuple[discord.Guild, ServerAttributes]:
        """
        Load the guild and all attributes from the given ids, using
        the given client.

        .. note::

            This function is async only to send a crash log to the server
            in question.

        :param client: The client to use to retrieve matching attribute
         objects from ids.
        :param guild_id: The guild id of the guild of the server
         attributes.
        :param attributes: The ids of the attributes to load.

        :return A tuple of the loaded guild and its attributes,
         corresponding with the given ids.

        :raise ParseError: The given ServerAttributeIds contains
         ids that can't be converted to their corresponding
         ServerAttributes object.
        """
        invalid_arguments: dict[str, str] = {}
        guild = client.get_guild(guild_id)
        if guild is None:
            raise ParseError(
                f"Guild id could not be parsed:\n"
                f"- guild_id: {guild_id}"
            )

        new_settings: dict[str, Any | None] = {
            k: [] if (typing.get_origin(v) is list
                      or type(v) is list)
            else None
            for k, v in ServerAttributes.__annotations__.items()
        }

        for attribute, attribute_value in attributes.items():
            if type(attribute_value) is list:
                parsed_values = []
                for value in attribute_value:
                    parsed_value = parse_attribute(
                        client, guild, attribute, value,
                        invalid_arguments=invalid_arguments)
                    if parsed_value is not None:
                        parsed_values.append(parsed_value)
                new_settings[attribute] = parsed_values
            else:
                assert isinstance(attribute_value, (str, int, type(None))), (
                    f"Expected attribute {attribute} to have value type str "
                    f"or int, but `{attribute_value}` was of type "
                    f"`{type(attribute_value)}`"
                )
                parsed_value = parse_attribute(
                    client, guild, attribute, attribute_value,
                    invalid_arguments=invalid_arguments)
                if parsed_value is not None:
                    new_settings[attribute] = parsed_value

        if invalid_arguments:
            if "log_channel" in invalid_arguments:
                raise ParseError(
                    "Some server settings could not be parsed:\n- "
                    + '\n- '.join(
                        [f"{k}: {v}" for k, v in invalid_arguments.items()]
                    )
                )
            else:
                from resources.utils.utils import log_to_guild
                await log_to_guild(
                    client,
                    guild_id,
                    msg="Some server settings could not be parsed:\n- "
                    + '\n- '.join(
                        [f"{k}: {v}" for k, v in invalid_arguments.items()]
                    ),
                )
                debug(
                    f"ParseError for {guild_id}:\n"
                    "Some server settings could not be parsed:\n- "
                    + '\n- '.join(
                        [f"{k}: {v}" for k, v in invalid_arguments.items()]
                    ),
                    DebugColor.lightred
                )

        # Mostly validation before casting it.
        for key, value in new_settings.items():
            assert isinstance(key, str), f"Key `{key}` was not a string!"
            expected_type = ServerAttributes.__annotations__[key]
            if (type(expected_type) is list
                    or typing.get_origin(expected_type) is list):
                assert type(value) is list and value is not None, (
                    f"Value for `{key}` should be a list, but it was "
                    f"{type(value)} instead!"
                )
            else:
                assert type(value) is not list, (
                    f"Value for `{key}` should be `{expected_type}`, but it "
                    f"was `{type(value)}` instead: {value}!"
                )
        attribute_dict: ServerAttributes = typing.cast(
            ServerAttributes, new_settings)

        return guild, ServerAttributes(**attribute_dict)

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
        Reload the server settings object to fetch and parse the latest
        server attribute ids from the database.

        :param client: The client with which to get roles and fetch
         from the database.
        :raise ParseError: If attributes in the data object could
         not be parsed.
        """
        state = await ServerSettings.fetch(client, self.guild.id)
        self.guild = state.guild  # just get the latest stuff, I guess.
        self.attributes = state.attributes
        self.enabled_modules = state.enabled_modules

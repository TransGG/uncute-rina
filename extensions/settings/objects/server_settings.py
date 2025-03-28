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


def get_channel_argument(
        invalid_arguments: dict[str, str],
        invalid_argument_name: str,
        client: Bot,
        channel_id: ChannelId,
) -> (
        discord.VoiceChannel |
        discord.StageChannel |
        discord.ForumChannel |
        discord.TextChannel |
        discord.CategoryChannel |
        discord.Thread |
        discord.abc.PrivateChannel |
        None
):
    """
    Try to get the channel corresponding to a channel id. If the channel is not found, add the argument name to
    invalid_arguments.

    Parameters
    -----------
    invalid_arguments :class:`dict[str, str]`:
        A dictionary of previous invalid arguments with which to add the argument name if the requested channel is
        not found.
    invalid_argument_name :class:`str`:
        The argument name to add to the invalid_arguments dictionary, if the requested channel is not found.
    client :class:`Bot`:
        The client with which to fetch the channel from the channel id.
    channel_id :class:`int`:
        The id of the channel to look up (and if not found, to add to the invalid_arguments dictionary)

    Returns
    --------
    The channel matching the given channel_id, or None if not found.

    Regards
    --------
    Since invalid_arguments is a dictionary, it will be passed as reference. It is updated inside the function, but
    it will also update the original dictionary object.
    """
    channel = None
    if channel_id is not None:
        channel = client.get_channel(channel_id)
        if channel is None:
            invalid_arguments[invalid_argument_name] = str(channel_id)
    return channel


def get_role_argument(
        invalid_arguments: dict[str, str],
        invalid_argument_name: str,
        server: discord.Guild | None,
        role_id: RoleId,
) -> discord.Role:
    """
    Try to get the role corresponding to a role id. If the channel is not found, add the argument name to
    invalid_arguments.

    Parameters
    -----------
    invalid_arguments :class:`dict[str, str]`:
        A dictionary of previous invalid arguments with which to add the argument name if the requested role is
        not found.
    invalid_argument_name :class:`str`:
        The argument name to add to the invalid_arguments dictionary, if the requested role is not found.
    server :class:`discord.Guild | None`:
        The guild with which to fetch the role from the role id. If this is None, the role won't be added to the
        invalid_arguments dictionary, but will still return None.
    role_id :class:`int`:
        The id of the role to look up (and if not found, to add to the invalid_arguments dictionary)

    Returns
    --------
    The role matching the given role_id, or None if not found or if `server` is None.

    Regards
    --------
    Since invalid_arguments is a dictionary, it will be passed as reference. It is updated inside the function, but
    it will also update the original dictionary object.
    """
    role = None
    if role_id is not None and server is not None:
        role = server.get_role(role_id)
        if role is None:
            invalid_arguments[invalid_argument_name] = str(role_id)
    return role


def get_user_argument(
        invalid_arguments: dict[str, str],
        invalid_argument_name: str,
        client: Bot,
        user_id: UserId | None,
) -> discord.User:
    user = None
    if user_id is not None:
        user = client.get_user(user_id)
        if user is None:
            invalid_arguments[invalid_argument_name] = str(user_id)
    return user


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

def get_roles_in_list(
        invalid_arguments: dict[str, str],
        invalid_argument_name: str,
        server: discord.Guild,
        role_ids: list[RoleId] | None,
) -> list[discord.Role]:
    roles = []
    if role_ids is None:
        # Return early
        return roles

    invalid_role_ids: list[str] = []
    for role_id in role_ids and server is not None:
        role = server.get_role(role_id)
        if role is None:
            invalid_role_ids.append(str(role_id))
        else:
            roles.append(role)
    invalid_arguments.append(invalid_argument_name + f": [{','.join(invalid_role_ids)}]")
    return roles


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
    async def migrate(async_rina_db: motor.code.AgnosticDatabase):
        """

        :param async_rina_db: The database to reference to look up the old and store the new database
        :return: Dunno yet lol
        :raises IndexError: No online database of the old version was found
        """
        old_collection: motor.MotorCollection = await async_rina_db["guildInfo"]
        all_settings = old_collection.find()
        new_collection: motor.MotorCollection = await async_rina_db[""]
        new_settings = []
        async for guild_id in all_settings:
            old_setting = all_settings[guild_id]
            new_setting = convert_old_settings_to_new(old_setting)
            new_settings.append(new_setting)

        await new_collection.insert_many(new_settings)

    @staticmethod
    async def load_all(async_rina_db: motor.core.AgnosticDatabase) -> list[ServerSettings]:
        collection: motor.MotorCollection = await async_rina_db[ServerSettings.database_key]
        all_settings = await collection.find()
        # todo: implement. lol
        if all_settings is None:
            return []
        return []

    @staticmethod
    async def load(client: Bot, async_rina_db: motor.core.AgnosticDatabase, server_id: int) -> ServerSettings:
        collection: motor.MotorCollection = await async_rina_db[ServerSettings.database_key]
        query = {"guild_id": server_id}
        result = await collection.find_one(query)
        if result is None:
            # todo: implement. lol
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

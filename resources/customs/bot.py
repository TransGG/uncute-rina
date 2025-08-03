from __future__ import annotations

import discord  # for main discord bot functionality
import discord.ext.commands as commands
import discord.app_commands as app_commands

from apscheduler.schedulers.asyncio import AsyncIOScheduler
# ^ for scheduling Reminders
from datetime import datetime
# ^ for startup and crash logging, and Reminders
from typing import TYPE_CHECKING, TypeVar
import motor.core as motorcore  # for typing
from pymongo.database import Database as PyMongoDatabase
# ^ for MongoDB database typing

from extensions.settings.objects import (
    AttributeKeys,
    EnabledModules,
    ServerAttributes,
    MessageableGuildChannel,
    GuildAttributeType,
)
from .api_token_dict import ApiTokenDict

if TYPE_CHECKING:
    from extensions.settings.objects import ServerSettings


T = TypeVar('T')
G = TypeVar('G')


class Bot(commands.Bot):
    # bot uptime start, used in /version in cmd_staffaddons
    startup_time = datetime.now().astimezone()

    commandList: list[discord.app_commands.AppCommand]
    log_channel: MessageableGuildChannel
    bot_owner: discord.User  # for AllowedMentions in on_appcommand_error()
    sched: AsyncIOScheduler  # for Reminders

    def __init__(
            self,
            api_tokens: ApiTokenDict,
            version: str,
            rina_db: PyMongoDatabase,
            async_rina_db: motorcore.AgnosticDatabase,
            *args, **kwargs
    ):
        self.api_tokens: ApiTokenDict = api_tokens
        self.version: str = version
        self.rina_db: PyMongoDatabase = rina_db
        self.async_rina_db: motorcore.AgnosticDatabase = async_rina_db
        self.server_settings: dict[int, ServerSettings] | None = None
        super().__init__(*args, **kwargs)

    def get_command_mention(self, command_string: str) -> str:
        """
        Turn a string (/reminders remindme) into a command mention
        (</reminders remindme:43783756372647832>)

        :param command_string: Command you want to convert into a
         mention (without slash in front of it).
        :return: The command mention, or the input (*command_string*)
         if no command with the name was found.
        """
        args = command_string.split(" ") + [None, None]
        command_name, subcommand, subcommand_group = args[0:3]
        # returns one of the following:
        # </COMMAND:COMMAND_ID>
        # </COMMAND SUBCOMMAND:ID>
        # </COMMAND SUBCOMMAND_GROUP SUBCOMMAND:ID>
        #              /\- is posed as 'subcommand', to make searching easier
        for command in self.commandList:
            if command.name != command_name:
                continue
            if subcommand is None:
                return command.mention

            for subgroup in command.options:
                if subgroup.name != subcommand:
                    continue
                if isinstance(subgroup, app_commands.Argument):
                    raise ValueError(
                        f"You can't mention command arguments! (Interpreted "
                        f"{subgroup.name} as argument of {command.name} "
                        f"instead of subcommand or subcommand group!)"
                    )
                if subcommand_group is None:
                    return subgroup.mention

                # now it technically searches subcommand in
                #  subcmdgroup.options but to remove additional
                #  renaming of variables, it stays as is.
                # subcmdgroup = subgroup  # hm
                for subcmdgroup in subgroup.options:
                    if isinstance(subcmdgroup, app_commands.Argument):
                        raise ValueError(
                            f"You can't mention command arguments! "
                            f"(Interpreted {subcmdgroup.name} as an argument "
                            f"of `/{command.name} {subgroup.name}` instead of "
                            f"a subcommand!)"
                        )
                    if subcmdgroup.name == subcommand_group:
                        return subcmdgroup.mention
        # no command found.
        return "/" + command_string

    def get_command_mention_with_args(
            self,
            command_string: str,
            **kwargs: str
    ) -> str:
        """
        Turn a string into a command mention and format passed arguments.
        :param command_string: Command you want to convert into a
         mention (without slash in front of it).
        :param kwargs: Additional arguments and their values to pass to
         the command.
        :return:
        """
        command_mention = self.get_command_mention(command_string)
        for key, value in kwargs.items():
            command_mention += f" `{key}:{value}`"

        return command_mention

    def get_guild_attribute(
            self,
            guild: discord.Guild | int,
            *args: str,
            default: T = None
    ) -> GuildAttributeType | T | list[GuildAttributeType | T]:
        """
        Get ServerSettings attributes for the given guild.

        :param guild: The guild or guild id of the server you want to
         get attributes for.
        :param args: The attribute(s) to get the values of. Must be keys
         of ServerAttributes.
        :param default: The value to return if attribute was not found.
        :return: A single or list of values matching the requested
         attributes, with *default* if attributes are not found.
        """
        if type(guild) is discord.Guild:
            guild_id: int = guild.id
        else:
            assert type(guild) is int  # why doesn't the interpreter see this?
            guild_id: int = guild

        if len(args) == 0:
            raise ValueError("You must provide at least one argument!")

        if (
                self.server_settings is None
                or guild_id not in self.server_settings
        ):
            # If settings have not been fetched yet, or if the guild
            #  doesn't have any settings (perhaps the bot was recently
            #  added).
            if len(args) > 1:
                return [default for _ in args]
            return default

        attributes = self.server_settings[guild_id].attributes

        output: list[GuildAttributeType | T] = []

        parent_server = attributes[AttributeKeys.parent_server]  # type: ignore

        for arg in args:
            if arg not in attributes:
                assert arg not in ServerAttributes.__annotations__
                raise ValueError(
                    f"Attribute '{arg}' is not a valid attribute!")

            att_value = attributes[arg]  # type:ignore
            if att_value is not None:
                output.append(att_value)
            elif parent_server is not None:
                maybe_the_parent_server_has_it = self.get_guild_attribute(
                    parent_server, arg, default=default)
                output.append(maybe_the_parent_server_has_it)
            else:
                output.append(default)

        if len(output) == 1:
            return output[0]
        return output

    def is_module_enabled(
            self, guild_id: discord.Guild | int | None, *args: str
    ) -> bool | list[bool]:
        """
        Check if a module is enabled for the given server.

        :param guild_id: The server to check the module state for.
        :param args: The module key(s) to get the state for.

        :return: The enabled/disabled state of the module as boolean, or
         a list of booleans matching the list of module keys given.
        """
        if type(guild_id) is discord.Guild:
            guild_id: int = guild_id.id

        if (
                self.server_settings is None
                or guild_id not in self.server_settings
        ):
            # If settings have not been fetched yet, or if the guild
            #  doesn't have any settings (perhaps the bot was recently
            #  added).
            return False

        modules = self.server_settings[guild_id].enabled_modules

        output: list[bool] = []
        for arg in args:
            if arg in modules:
                output.append(modules[arg])  # type: ignore
            elif arg not in EnabledModules.__annotations__:
                raise ValueError(f"Module '{arg}' is not a valid module!")
            else:
                output.append(False)

        if len(output) == 1:
            return output[0]
        return output

    def is_me(self, user_id: discord.Member | discord.User | int) -> bool:
        """
        Check whether the given user is the bot.

        :param user_id: The user or user id to check.
        :return: ``True`` if the given user is the bot, otherwise ``False``.
        """
        if (isinstance(user_id, discord.User)
                or isinstance(user_id, discord.Member)):
            user_id = user_id.id
        # Could also use hasattr(user_id, "id") for a more generic approach...
        #  But this should work fine enough.
        return self.user.id == user_id

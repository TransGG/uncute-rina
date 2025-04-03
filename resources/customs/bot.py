from __future__ import annotations
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # for scheduling Reminders
from datetime import datetime  # for startup and crash logging, and Reminders
from typing import TYPE_CHECKING, TypeVar

import discord  # for main discord bot functionality
import discord.ext.commands as commands

import motor.core as motorcore  # for typing
from pymongo.database import Database as PyMongoDatabase  # for MongoDB database typing

from extensions.settings.objects import (
    AttributeKeys, EnabledModules, ServerAttributes)
from .api_token_dict import ApiTokenDict

if TYPE_CHECKING:
    from extensions.settings.objects import ServerSettings


T = TypeVar('T')
G = TypeVar('G')


class Bot(commands.Bot):
    startup_time = datetime.now().astimezone()  # bot uptime start, used in /version in cmd_staffaddons

    commandList: list[discord.app_commands.AppCommand]
    log_channel: discord.TextChannel | discord.Thread
    bot_owner: discord.User  # for AllowedMentions in on_appcommand_error()
    sched: AsyncIOScheduler  # for Reminders
    running_on_production = True

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
        Turn a string (/reminders remindme) into a command mention (</reminders remindme:43783756372647832>)

        :param command_string: Command you want to convert into a mention (without slash in front of it).

        :return: The command mention, or the input (*command_string*) if no command with the name was found.
        """
        args = command_string.split(" ") + [None, None]
        command_name, subcommand, subcommand_group = args[0:3]
        # returns one of the following:
        # </COMMAND:COMMAND_ID>
        # </COMMAND SUBCOMMAND:ID>
        # </COMMAND SUBCOMMAND_GROUP SUBCOMMAND:ID>
        #              /\- is posed as 'subcommand', to make searching easier
        for command in self.commandList:
            if command.name == command_name:
                if subcommand is None:
                    return command.mention
                for subgroup in command.options:
                    if subgroup.name == subcommand:
                        if subcommand_group is None:
                            return subgroup.mention
                        # now it techinically searches subcommand in subcmdgroup.options
                        # but to remove additional renaming of variables, it stays as is.
                        # subcmdgroup = subgroup # hm
                        for subcmdgroup in subgroup.options:
                            if subcmdgroup.name == subcommand_group:
                                return subcmdgroup.mention
                                # return f"</{command.name} {subgroup.name} {subcmdgroup.name}:{command.id}>"
        return "/" + command_string

    def get_guild_attribute(
            self,
            guild_id: discord.Guild | int,
            *args: str,
            default: T = None
    ) -> object | list[object] | T:
        """
        Get ServerSettings attributes for the given guild.

        :param guild_id: The guild or guild id of the server you want to
         get attributes for.
        :param args: The attribute(s) to get the values of. Must be keys
         of ServerAttributes.
        :param default: The value to return if attribute was not found.
        :return: A single or list of values matching the requested attributes,
         with *default* if attributes are not found.
        """
        if type(guild_id) is discord.Guild:
            guild_id: int = guild_id.id
        if len(args) == 0:
            raise ValueError("You must provide at least one argument!")

        if (self.server_settings is None or  # settings have not been fetched yet.
                guild_id not in self.server_settings):  # return early
            if len(args) > 1:
                return [default] * len(args)
            return default

        attributes = self.server_settings[guild_id].attributes

        output: list[discord.Guild | T | list[discord.Guild] |
                     discord.abc.Messageable | discord.CategoryChannel |
                     discord.User | discord.Role | list[discord.Role] |
                     str | discord.VoiceChannel | int |
                     list[discord.abc.Messageable] | discord.Emoji] = []

        parent_server = attributes[AttributeKeys.parent_server]  # type: ignore

        for arg in args:
            if arg not in attributes:
                assert arg not in ServerAttributes.__annotations__
                raise ValueError(f"Attribute '{arg}' is not a valid attribute!")

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

        :return: The enabled/disabled state of the module as boolean, or a list of booleans matching the list of
         module keys given.
        """
        if type(guild_id) is discord.Guild:
            guild_id: int = guild_id.id

        if (self.server_settings is None or  # settings have not been fetched yet.
                guild_id not in self.server_settings):  # return early
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

        return output

    def is_me(self, user_id: discord.Member | discord.User | int) -> bool:
        """
        Check whether the given user is the bot.

        :param user_id: The user or user id to check.
        :return: ``True`` if the given user is the bot, otherwise ``False``.
        """
        if isinstance(user_id, discord.User) or isinstance(user_id, discord.Member):
            user_id = user_id.id
        # Could also use hasattr(user_id, "id") for a more generic approach...
        #  But this should work fine enough.
        return self.user.id == user_id

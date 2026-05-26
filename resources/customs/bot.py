from __future__ import annotations

import discord  # for main discord bot functionality
import discord.ext.commands as commands
import discord.app_commands as app_commands

from apscheduler.schedulers.asyncio import AsyncIOScheduler
# ^ for scheduling Reminders
from datetime import datetime
# ^ for startup and crash logging, and Reminders
from typing import TYPE_CHECKING, Any
import motor.core as motorcore  # for typing
from pymongo.database import Database as PyMongoDatabase
# ^ for MongoDB database typing

from extensions.settings.objects import (
    EnabledModules,
    ServerAttributes,
)
from extensions.settings.objects.server_attributes import default_server_attributes
from resources.abc import (
    ApiTokenDict,
    MessageableGuildChannel,
)

if TYPE_CHECKING:
    from extensions.settings.objects import ServerSettings


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
            *args: Any,  # noqa: ANN401
            **kwargs: Any,  # noqa: ANN401
    ) -> None:
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
        args = [*command_string.split(" "), None, None]
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

    # Type checking with the class is effectively impossible,
    #  as the key dictates the type, and any union we would emit
    #  would then need to be explicitly ignored in a type check.
    def get_guild_attributes[Default](
            self,
            guild: discord.Guild | int,
            default: Default = None,
    ) -> ServerAttributes:
        """
        Get ServerSettings attributes for the given guild.

        Uses a main guild's attributes as baseplate, and then
        recursively looks at the guild's parent to fill in unset
        attribute values.

        :param guild: The guild or guild id of the server you want to
         get attributes for.
        :param default: The value to fill if an attribute isn't found.
        :return: A newly made ServerAttributes object with attributes
         from the asked guild and its parents.
        """
        if isinstance(guild, discord.Guild):
            guild_id: int = guild.id
        else:
            guild_id: int = guild

        if (
                self.server_settings is None
                or guild_id not in self.server_settings
        ):
            # If settings have not been fetched yet, or if the guild
            #  doesn't have any settings (perhaps the bot was recently
            #  added).
            return default_server_attributes(default)

        attributes = self.server_settings[guild_id].attributes

        unset_keys = [
            key
            for key, val in ServerAttributes.__annotations__.items()
            if val is None
        ]

        # Fill unset attributes with parent values
        parent_attributes = attributes  # set to self to prepare iterative recursion
        while len(unset_keys) > 0 and (parent := parent_attributes["parent_server"]) is not None:
            parent_attributes = self.server_settings[parent.id].attributes
            for key in list(unset_keys):  # clone the list because we're editing it inside the loop
                if getattr(parent_attributes, key, None) is not None:  # type: ignore[literal-required] # noqa: E501
                    # Ignore the string literal warning, I guess.
                    # `key` is always a string, and should also always be
                    #  a key of the TypedDict ServerAttributes.
                    attributes[key] = parent_attributes[key]  # type: ignore[literal-required] # noqa: E501
                    unset_keys.remove(key)

        return attributes

    def is_module_enabled(
            self, guild: discord.Guild | int | None, *args: str
    ) -> bool | list[bool]:
        """
        Check if a module is enabled for the given server.

        :param guild: The server to check the module state for.
        :param args: The module key(s) to get the state for.

        :return: The enabled/disabled state of the module as boolean, or
         a list of booleans matching the list of module keys given.
        """
        if isinstance(guild, discord.Guild):
            guild_id: int = guild.id
        elif isinstance(guild, int):
            guild_id: int = guild
        else:  # guild is None
            return False

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

    def is_me(self, user: discord.Member | discord.User | int) -> bool:
        """
        Check whether the given user is the bot.

        :param user: The user or user id to check.
        :return: ``True`` if the given user is the bot, otherwise ``False``.
        """
        user_id: int
        if isinstance(user, (discord.User, discord.Member)):
            user_id = user.id
        else:
            user_id = user
        # Could also use hasattr(user_id, "id") for a more generic approach...
        #  But this should work fine enough.
        return self.user is not None and self.user.id == user_id

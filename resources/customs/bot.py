from __future__ import annotations
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # for scheduling Reminders
from datetime import datetime  # for startup and crash logging, and Reminders
from typing import TypedDict, TYPE_CHECKING, TypeVar

import discord  # for main discord bot functionality
import discord.ext.commands as commands

import motor.core as motorcore  # for typing
from pymongo.database import Database as PyMongoDatabase  # for MongoDB database typing

if TYPE_CHECKING:
    from extensions.settings.objects import ServerSettings, ServerAttributes, EnabledModules, AttributeKeys

ApiTokenDict = TypedDict('ApiTokenDict',
                         {'MongoDB': str, 'Open Exchange Rates': str, 'Wolfram Alpha': str, 'Equaldex': str})

T = TypeVar('T')


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
            rina_db: PyMongoDatabase, async_rina_db: motorcore.AgnosticDatabase,
            *args, **kwargs
    ):
        self.api_tokens: ApiTokenDict = api_tokens
        self.version: str = version
        self.rina_db: PyMongoDatabase = rina_db
        self.async_rina_db: motorcore.AgnosticDatabase = async_rina_db
        self.server_settings: dict[int, ServerSettings] | None = None
        super().__init__(*args, **kwargs)

    @property
    def custom_ids(self):
        production_ids = {
            "staff_server_id": 981730502987898960,
            "staff_qotw_channel": 1019706498609319969,
            "staff_dev_request": 982351285959413811,
            "staff_watch_channel": 989638606433968159,
            "badeline_bot": 981710253311811614,
            "staff_logs_category": 1025456987049312297,
            "staff_reports_channel": 981730694202023946,
            "active_staff_role": 996802301283020890,
            "staff_developer_role": 982274122920902656,
            "transplace_server_id": 959551566388547676,
            "enbyplace_server_id": 1087014898199969873,
            "transonance_server_id": 638480381552754730,
            "transplace_ticket_channel_id": 995343855069175858,
            "enbyplace_ticket_channel_id": 1186054373986537522,
            "transonance_ticket_channel_id": 1108789589558177812,
            "ban_appeal_webhook_ids": [1120832140758745199],
            "vctable_prefix": "[T] ",
            "aegis_ping_role_id": 1331313288000307371,
        }
        development_ids = {
            "staff_server_id": 985931648094834798,
            "staff_qotw_channel": 1260504768611352637,
            "staff_dev_request": 1260504504743362574,
            "staff_watch_channel": 1143642388670202086,
            "badeline_bot": 979057304752254976,  # Rina herself
            "staff_logs_category": 1143642220231131156,
            "staff_reports_channel": 1260505477364711547,
            "active_staff_role": 986022587756871711,  # @Developers
            "staff_developer_role": 986022587756871711,
            "transplace_server_id": 985931648094834798,  # - private dev server
            "enbyplace_server_id": 981615050664075404,  # + public dev server
            "transonance_server_id": 981615050664075404,  # + public dev server
            "transplace_ticket_channel_id": 1175669542412877824,  # - private dev server channel
            "enbyplace_ticket_channel_id": 1125108250426228826,  # + public dev server channel
            "transonance_ticket_channel_id": 1125108250426228826,  # + public dev server channel
            "ban_appeal_webhook_ids": [979057304752254976],
            "vctable_prefix": "[T] ",
            "aegis_ping_role_id": 1350538597366894662
        }
        assert [i for i in production_ids] == [i for i in development_ids]  # all keys match

        if self.running_on_production:
            return production_ids
        else:
            return development_ids

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

    async def get_guild_info(
            self, guild_id: discord.Guild | int, *args: str, log: tuple[discord.Interaction, str] | None = None
    ):
        """
        Get a guild's server settings (from /editguildinfo, in cmd_customvcs).

        :param guild_id: The guild or id from which you want to get the guild info / settings.
        :param args: The setting(s) that you want to fetch.
        :param log: A tuple of an interaction and error_message. The command will reply this error message to the
         given interaction if any of the arguments could not be found.

        :return: (whichever is given in the database)

        :raise KeyError: If guild is None, does not have data, or not the requested data.
        """
        if guild_id is None:
            raise KeyError(f"'{guild_id}' is not a valid guild or id!")
        if isinstance(guild_id, discord.Guild):
            guild_id = guild_id.id
        try:
            collection = self.rina_db["guildInfo"]
            query = {"guild_id": guild_id}
            guild_data = collection.find_one(query)
            if guild_data is None:
                raise KeyError(str(guild_id) + " does not have data in the guildInfo database!")
            if len(args) == 0:
                return guild_data
            output = []
            unavailable = []
            for key in args:
                try:
                    output.append(guild_data[key])
                except KeyError:
                    unavailable.append(key)
            if unavailable:
                raise KeyError("Guild " + str(guild_id) + " does not have data for: " + ', '.join(unavailable))
            if len(output) == 1:  # prevent outputting [1] (one item as list)
                return output[0]
            return output
        except KeyError:
            if log is None:
                raise
            await log[0].response.send_message(log[1], ephemeral=True)
            raise

    def get_guild_attribute(
            self, guild_id: discord.Guild | int, *args: str, default: T = None
    ) -> object | T | list[object | T]:
        """
        Get ServerSettings attributes for the given guild.

        :param guild_id: The guild or guild id of the server you want to get attributes for.
        :param args: The attribute(s) to get the values of. Must be keys of ServerAttributes.
        :param default: The default value to return if the attribute is not found. If multiple args were provided,

        :return: A single or list of values matching the requested attributes, with *default* if
         attributes are not found.
        """
        if type(guild_id) is discord.Guild:
            guild_id: int = guild_id.id

        if (self.server_settings is None or  # settings have not been fetched yet.
                guild_id not in self.server_settings):  # return early
            if type(args) is list:
                return [default] * len(args)
            return default

        print(self.server_settings[guild_id])
        for attr, val in self.server_settings[guild_id].attributes.items():
            print(attr, val)

        attributes = self.server_settings[guild_id].attributes

        output: list[discord.Guild | None | list[discord.Guild] | discord.abc.Messageable | discord.CategoryChannel |
                     discord.User | discord.Role | list[discord.Role] | str | discord.VoiceChannel | int |
                     list[discord.abc.Messageable] | discord.Emoji] = []

        parent_server = attributes[AttributeKeys.parent_server]

        for arg in args:
            if arg in attributes:
                output.append(attributes[arg])  # type: ignore
            elif arg not in ServerAttributes.__annotations__:
                raise ValueError(f"Attribute '{arg}' is not a valid attribute!")
            elif parent_server is not None:
                maybe_the_parent_server_has_it = self.get_guild_attribute(parent_server, arg)
                output.append(maybe_the_parent_server_has_it)
            else:
                output.append(default)

        if len(output) == 1:
            return output[0]
        return output

    def is_module_enabled(
            self, guild_id: discord.Guild | int, *args: str
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
        # could also use hasattr(user_id, "id") for a more generic approach... but this should work fine enough.
        return self.user.id == user_id

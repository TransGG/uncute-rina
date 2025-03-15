from datetime import datetime  # for startup and crash logging, and Reminders

import discord  # for main discord bot functionality
import discord.ext.commands as commands
import motor.core as motorcore  # for typing
from apscheduler.schedulers.asyncio import AsyncIOScheduler  # for scheduling Reminders
from pymongo.database import Database as PyMongoDatabase  # for MongoDB database typing
from typing import Literal, TypedDict


ApiTokenDict = TypedDict('ApiTokenDict',
                         {'MongoDB': str, 'Open Exchange Rates': str, 'Wolfram Alpha': str, 'Equaldex': str})


class Bot(commands.Bot):
    startup_time = datetime.now()  # bot uptime start, used in /version in cmd_staffaddons

    commandList: list[discord.app_commands.AppCommand]
    log_channel: discord.TextChannel | discord.Thread
    bot_owner: discord.User  # for AllowedMentions in on_appcommand_error()
    reminder_scheduler: AsyncIOScheduler  # for Reminders
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
            "vctable_prefix": "[T] "
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
            "vctable_prefix": "[T] "
        }
        assert [i for i in production_ids] == [i for i in development_ids]  # all keys match

        if self.running_on_production:
            return production_ids
        else:
            return development_ids

    def get_command_mention(self, command_string: str) -> str:
        """
        Turn a string (/reminders remindme) into a command mention (</reminders remindme:43783756372647832>)

        Parameters
        -----------
        command_string: :class:`str`
            Command you want to convert into a mention (without slash in front of it).

        Returns
        --------
        :class:`str`
            The command mention, or the input (:param:`command_string`) if no command with the name was found.
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
            self, guild_id: discord.Guild | int, *args: str, log: list[discord.Interaction | str] | None = None
    ):
        """
        Get a guild's server settings (from /editguildinfo, in cmd_customvcs).

        Parameters
        -----------
        guild_id: :class:`discord.Guild` | :class:`int`
            The guild or id from which you want to get the guild info / settings.
        *args: :class:`str`
            settings (or multiple) that you want to fetch.
        log: :class:`list[discord.Interaction, str]` | :class:`None`, optional
            A list of [itx, error_message], and will reply this error message to the given interaction if there's a
             KeyError. Default: None.

        Returns
        --------
        :class:`Any`
            (whichever is given in the database)

        Raises
        -------
        :class:`KeyError`
            if guild is None, does not have data, or not the requested data.
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

    def is_me(self, user_id: discord.Member | discord.User | int):
        if isinstance(user_id, discord.User) or isinstance(user_id, discord.Member):
            user_id = user_id.id
        return self.user.id == user_id
import discord, discord.ext.commands as commands # for main discord bot functionality
from pymongo.database import Database as pydb # for MongoDB database
import motor.motor_asyncio as motor # for making Mongo run asynchronously (during api calls)
from datetime import datetime # for startup and crash logging, and Reminders
from apscheduler.schedulers.asyncio import AsyncIOScheduler # for scheduling Reminders


class Bot(commands.Bot):
    def __init__(self, api_tokens: dict, version: str, 
                 RinaDB: pydb, asyncRinaDB: motor.core.AgnosticDatabase,
                 *args, **kwargs):
        self.api_tokens: dict = api_tokens
        self.version: str = version
        self.RinaDB: pydb = RinaDB
        self.asyncRinaDB: motor.core.AgnosticDatabase = asyncRinaDB
        super().__init__(*args, **kwargs)

    startup_time = datetime.now() # bot uptime start, used in /version in cmd_staffaddons

    commandList: list[discord.app_commands.AppCommand]
    log_channel: discord.TextChannel
    custom_ids = {
        "staff_server_id": 981730502987898960,
        "staff_qotw_channel": 1019706498609319969,
        "staff_dev_request": 982351285959413811,
        "staff_watch_channel": 989638606433968159,
        "badeline_bot": 981710253311811614,
        "staff_logs_category": 1025456987049312297,
        "staff_reports_channel": 981730694202023946,
        "active_staff_role": 996802301283020890,
        "transplace_server_id": 959551566388547676,
        "enbyplace_server_id": 1087014898199969873,
        "transonance_server_id": 638480381552754730,
        "transplace_ticket_channel_id": 995343855069175858,
        "enbyplace_ticket_channel_id": 1186054373986537522,
        "transonance_ticket_channel_id": 1108789589558177812
    }
    # custom_ids = {
    #     "staff_server_id": 985931648094834798,
    #     "staff_qotw_channel": 1019706498609319969,
    #     "staff_dev_request": 982351285959413811,
    #     "staff_watch_channel": 1143642388670202086,
    #     "badeline_bot": 979057304752254976,
    #     "staff_logs_category": 1143642220231131156,
    #     "staff_reports_channel": 981730694202023946,
    #     "active_staff_role": 986022587756871711
    # }
    bot_owner: discord.User # for AllowedMentions in on_appcommand_error()
    reminder_scheduler: AsyncIOScheduler # for Reminders
    
    def get_command_mention(self, command_string: str):
        """
        Turn a string (/reminders remindme) into a command mention (</reminders remindme:43783756372647832>)

        ### Parameters
        --------------
        command_string:  :class:`str`
            Command you want to convert into a mention (without slash in front of it)
        ### Returns
        -----------
        command mention: :class:`str`
            The command mention, or input if not found
        """

        args = command_string.split(" ")+[None, None]
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
                        #now it techinically searches subcommand in subcmdgroup.options
                        #but to remove additional renaming of variables, it stays as is.
                        # subcmdgroup = subgroup # hm
                        for subcmdgroup in subgroup.options:
                            if subcmdgroup.name == subcommand_group:
                                return subcmdgroup.mention
                                # return f"</{command.name} {subgroup.name} {subcmdgroup.name}:{command.id}>"
        return "/"+command_string

    async def get_guild_info(self, guild_id: discord.Guild | int, *args: str, log: list[discord.Interaction | str] | None = None):
        """
        Get a guild's server settings (from /editguildinfo, in cmd_customvcs)

        ### Arguments:
        --------------
        guild_id: :class:`discord.Guild` or :class:`int`
            guild or id from which you want to get the guild info / settings
        *args: :class:`str`
            settings (or multiple) that you want to fetch
        log (optional): :class:`list[discord.Interaction, str]`
            A list of [itx, error_message], and will reply this error message to the given interaction if there's a KeyError.

        ### Returns:
        ------------
        `any` (whichever is given in the database)

        ### Raises:
        -----------
        `KeyError` if guild is None, does not have data, or not the requested data.
        """
        if guild_id is None:
            raise KeyError(f"'{guild_id}' is not a valid guild or id!")
        if isinstance(guild_id, discord.Guild):
            guild_id = guild_id.id
        try:
            collection = self.RinaDB["guildInfo"]
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
            if len(output) == 1: # prevent outputting [1] (one item as list)
                return output[0]
            return output
        except KeyError:
            if log is None:
                raise
            await log[0].response.send_message(log[1], ephemeral=True)
            raise
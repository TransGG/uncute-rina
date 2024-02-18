from import_modules import *

BOT_VERSION = "1.2.7.16"
TESTING_ENVIRONMENT = 2 # 1 = public test server (Supporter server) ; 2 = private test server (transplace staff only)
appcommanderror_cooldown = 0

class Bot(commands.Bot):
    def __init__(self, api_tokens: dict, version: str, 
                 RinaDB: pydb, asyncRinaDB: motor.core.AgnosticDatabase,
                 *args, **kwargs):
        self.api_tokens: dict = api_tokens
        self.version: str = version
        self.RinaDB: pydb = RinaDB
        self.asyncRinaDB: motor.core.AgnosticDatabase = asyncRinaDB
        super().__init__(*args, **kwargs)

    startup_time = datetime.now() # used in /version in cmd_staffaddons

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

# Permission requirements:
#   server members intent,
#   message content intent,
#   guild permissions:
#       send messages
#       attach files (for image of the member joining graph thing)
#       read channel history (locate previous starboard message, for example)
#       move users between voice channels (custom vc)
#       manage roles (for removing NPA and NVA roles)
#       manage channels (Global: You need this to be able to set the position of CustomVCs in a category, apparently) NEEDS TO BE GLOBAL?
#           Create and Delete voice channels
#       use embeds (for starboard)
#       use (external) emojis (for starboard, if you have external starboard reaction...?)

def get_token_data() -> tuple[str, dict, pydb, motor.core.AgnosticDatabase]:
    """
    Ensures the api_keys.json file contains all of the bot's required keys, and uses these keys to start a link to the MongoDB.

    Returns:
    --------
    `tuple[discord_token, synchronous_db_connection, async_db_connection]` tuple of discord bot token and database client cluster connections
    """
    debug(f"[#+   ]: Loading api keys..." + " " * 30, color="light_blue", end='\r')
    # debug(f"[+     ]: Loading server settings" + " " * 30, color="light_blue", end='\r')
    try:
        with open("api_keys.json","r") as f:
            api_keys = json.loads(f.read())
        tokens = {}
        bot_token: str = api_keys['Discord']
        for key in ['MongoDB', 'Open Exchange Rates', 'Wolfram Alpha']:
            # copy every other key to new dictionary to check if every key is in the file.
            tokens[key] = api_keys[key]
    except json.decoder.JSONDecodeError:
        raise SyntaxError("Invalid JSON file. Please ensure it has correct formatting.").with_traceback(None)
    except KeyError as ex:
        raise KeyError("Missing API key for: " + str(ex)).with_traceback(None)
    # mongoURI = open("mongo.txt","r").read()
    debug(f"[##+  ]: Loading database clusters..." + " " * 30, color="light_blue", end='\r')
    cluster = MongoClient(tokens['MongoDB'])
    RinaDB = cluster["Rina"]
    cluster = motor.AsyncIOMotorClient(tokens['MongoDB'])
    asyncRinaDB = cluster["Rina"]
    debug(f"[###+ ]: Loading version..." + " " * 30, color="light_blue", end='\r')
    return (bot_token, tokens, RinaDB, asyncRinaDB)

def get_version() -> str:
    """
    Dumb code for cool version updates. Reads version file and matches with current version string. Updates file if string is newer, and adds another ".%d" for how often the bot has been started in this version.

    Returns:
    --------
    `str` Current version/instance of the bot.
    """
    fileVersion = BOT_VERSION.split(".")
    try:
        with open("version.txt", "r") as f:
            version = f.read().split(".")
    except FileNotFoundError:
        version = ["0"]*len(fileVersion)
    # if testing, which environment are you in?
    # 1: private dev server; 2: public dev server (TransPlace [Copy])
    for v in range(len(fileVersion)):
        if int(fileVersion[v]) > int(version[v]):
            version = fileVersion + ["0"]
            break
    else:
        version[-1] = str(int(version[-1])+1)
    version = '.'.join(version)
    with open("version.txt","w") as f:
        f.write(f"{version}")
    return version

def create_client(tokens: dict, RinaDB: pydb, asyncRinaDB: motor.core.AgnosticDatabase, version: str) -> discord.Client:
    debug(f"[#### ]: Loading Bot" + " " * 30, color="light_blue", end='\r')

    intents = discord.Intents.default()
    intents.members = True #apparently this needs to be additionally defined cause it's not included in Intents.default()?
    intents.message_content = True #apparently it turned off my default intent or something: otherwise i can't send 1984, ofc.
    #setup default discord bot client settings, permissions, slash commands, and file paths

    debug(f"[#      ]: Loaded bot" + " " * 30, color="green")
    debug(f"[#+     ]: Starting Bot...", color="light_blue", end='\r')
    discord.VoiceClient.warn_nacl = False   
    return Bot(
            api_tokens=tokens,
            version=version,
            RinaDB=RinaDB,
            asyncRinaDB=asyncRinaDB,

            intents=intents,
            command_prefix="/!\"@:\\#", #unnecessary, but needs to be set so.. uh.. yeah. Unnecessary terminal warnings avoided.
            case_insensitive=True,
            activity=discord.Game(name="with slash (/) commands!"),
            allowed_mentions=discord.AllowedMentions(everyone=False)
    )

if __name__ == '__main__':
    (TOKEN, tokens, RinaDB, asyncRinaDB) = get_token_data()
    version = get_version()
    client = create_client(tokens, RinaDB, asyncRinaDB, version)

    #region Client events
    @client.event
    async def on_ready():
        debug(f"[#######]: Logged in as {client.user}, in version {version} (in {datetime.now()-program_start})",color="green")
        await client.log_channel.send(f":white_check_mark: **Started Rina** in version {version}")


        debug(f"[+]: Pre-loading all watchlist threads", color="light_blue",end="\r")
        watchlist_channel = client.get_channel(client.custom_ids["staff_watch_channel"])
        if watchlist_channel is not None: # if running on prod
            await get_watchlist_index(watchlist_channel)
        debug(f"[#]: Loaded watchlist threads."+" "*15, color="green")
        
    @client.event
    async def setup_hook():
        start = datetime.now()
        logger = logging.getLogger("apscheduler")
        logger.setLevel(logging.WARNING)
        # remove annoying 'Scheduler started' message on sched.start()
        client.sched = AsyncIOScheduler(logger=logger)
        client.sched.start()

        ## cache server settings into client, to prevent having to load settings for every extension
        debug(f"[##     ]: Started Bot"+" "*30,color="green")
        ## activate the extensions/programs/code for slash commands
        extensions = [
            "cmd_addons",
            "cmd_compliments",
            "cmd_customvcs",
            "cmd_emojistats",
            "cmd_getmemberdata",
            "cmd_pronouns",
            "cmd_qotw",
            "cmd_staffaddons",
            "cmd_tags",
            "cmd_termdictionary",
            "cmd_todolist",
            "cmd_toneindicator",
            "cmd_vclogreader",
            "cmd_watchlist",
            "cmdg_nameusage",
            "cmdg_reminders",
            "cmdg_starboard",
        ]

        for extID in range(len(extensions)):
            debug(f"[{'#'*extID}+{' '*(len(extensions)-extID-1)}]: Loading {extensions[extID]}"+" "*15,color="light_blue",end='\r')
            await client.load_extension(extensions[extID])
        debug(f"[###    ]: Loaded extensions successfully (in {datetime.now()-start})",color="green")

        debug(f"[###+   ]: Loading server settings"+ " "*30,color="light_blue",end='\r')
        try:
            client.log_channel = await client.fetch_channel(988118678962860032)
        except (discord.errors.InvalidData, discord.errors.HTTPException, discord.errors.NotFound, discord.errors.Forbidden): #one of these
            if TESTING_ENVIRONMENT == 1:
                client.log_channel = await client.fetch_channel(986304081234624554)
            else:
                client.log_channel = await client.fetch_channel(1062396920187863111)
        client.bot_owner = await client.fetch_user(262913789375021056)#(await client.application_info()).owner
        #                   can't use the commented out code because Rina is owned by someone else in the main server than the dev server (=not me).

        debug(f"[####   ]: Loaded server settings"+" "*30,color="green")
        debug(f"[####+  ]: Restarting ongoing reminders"+" "*30,color="light_blue",end="\r")
        collection = RinaDB["reminders"]
        query = {}
        db_data = collection.find(query)
        for user in db_data:
            try:
                for reminder in user['reminders']:
                    creationtime = datetime.fromtimestamp(reminder['creationtime'])#, timezone.utc)
                    remindertime = datetime.fromtimestamp(reminder['remindertime'])#, timezone.utc)
                    ReminderObject(client, creationtime, remindertime, user['userID'], reminder['reminder'], user, continued=True)
            except KeyError:
                pass
        debug(f"[#####  ]: Finished setting up reminders"+" "*30,color="green")
        debug(f"[#####+ ]: Caching bot's command names and their ids",color="light_blue",end='\r')
        commandList = await client.tree.fetch_commands()
        client.commandList = commandList
        debug(f"[###### ]: Cached bot's command names and their ids"+" "*30,color="green")
        debug(f"[######+]: Starting..."+" "*30,color="light_blue",end='\r')

        # debug(f"[{'#'*extID}{' '*(len(extensions)-extID-1)} ]: Syncing command tree"+ " "*30,color="light_blue",end='\r')
        # await client.tree.sync()

    @client.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return
        # kill switch, see cmd_addons for other on_message events. (and a few other extensions)
        if message.author.id == client.bot_owner.id:
            cool_keys = [
                ":restart",
                ":sudo restart",
                ":sudo reboot",
                ":sudo shutdown",
            ]
            if message.content == ":kill now please stop" or any([message.content.startswith(item) for item in cool_keys]):
                await message.add_reaction("🔄")
                sys.exit(0)
                # quitting the program also 
        # this will only run if it hasn't already quit, of course
        if message.content.startswith(":sudo "): 
            await message.reply("Cleo.CommandManager.InsufficientPermissionError: Could not run command: No permission\nTryin to be part of the cool kids? Try reading this:\n1 4M 4 V3RY C001 K16!")
            await message.add_reaction("⚠")
        elif message.content.lower().startswith("i am a very cool kid"):
            await message.channel.send("Yes. Yes you are.")
    #endregion
    
    #region Crash event handling
    async def send_crash_message(error_type: str, traceback_text: str, error_source: str, color: discord.Colour, itx: discord.Interaction=None):
        """
        Sends crash message to Rina's main logging channel

        ### Parameters
        error_type: :class:`str`
            Is it an 'Error' or an 'AppCommand Error'
        traceback_text: :class:`str`
            What is the traceback?
        error_source: :class:`str`
            Name of the error source, displayed at the top of the message. Think of event or command.
        color: :class:`discord.Colour`
            Color of the discord embed
        itx (optional): :class:`discord.Interaction`
            Interaction with a potential guild. This might allow Rina to send the crash log to that guild instead
        """

        log_guild: discord.Guild
        try:
            log_guild = itx.guild
            vcLog = await client.get_guild_info(itx.guild, "vcLog")
        except (AttributeError, KeyError): # no guild settings, or itx -> 'NoneType' has no attribute '.guild'
            try:
                log_guild = await client.fetch_guild(959551566388547676)
            except discord.errors.NotFound:
                if TESTING_ENVIRONMENT == 1:
                    log_guild = await client.fetch_guild(985931648094834798)
                else:
                    log_guild = await client.fetch_guild(981615050664075404)

            try:
                vcLog = await client.get_guild_info(log_guild, "vcLog")
            except KeyError:
                return # prevent infinite logging loops, i guess
        
        error_caps = error_type.upper()
        debug_message = f"\n\n\n\n[{datetime.now().strftime('%H:%M:%S.%f')}] [{error_caps}]: {error_source}\n\n{traceback_text}\n"
        debug(f"{debug_message}",add_time=False)

        channel = await log_guild.fetch_channel(vcLog) #crashes if none
        msg = debug_message.replace("``", "`` ")#("\\", "\\\\").replace("*", "\\*").replace("`", "\\`").replace("_", "\\_").replace("~~", "\\~\\~")
        msg = "```" + msg + "```"
        embed = discord.Embed(color=color, title = error_type +' Log', description=msg)
        await channel.send(f"{client.bot_owner.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(users=[client.bot_owner]))

    @client.event
    async def on_error(event: str, *_args, **_kwargs):
        # msg = '\n\n          '.join([repr(i) for i in args])+"\n\n"
        # msg += '\n\n                   '.join([repr(i) for i in kwargs])
        msg = traceback.format_exc()
        await send_crash_message("Error", msg, event, discord.Colour.from_rgb(r=255, g=77, b=77))

    @client.tree.error
    async def on_app_command_error(itx: discord.Interaction, error):
        global appcommanderror_cooldown
        if int(mktime(datetime.now().timetuple())) - appcommanderror_cooldown < 60:
            # prevent extra log (prevent excessive spam and saving myself some large mentioning chain) if within 1 minute
            return
        
        async def reply(itx: discord.Interaction, message: str):
            if itx.response.is_done():
                await itx.followup.send(message, ephemeral=True)
            else:
                await itx.response.send_message(message, ephemeral=True)
        
        if isinstance(error, discord.app_commands.errors.CommandNotFound):
            cmd_mention = client.get_command_mention("update")
            await reply(itx, f"This command doesn't exist! Perhaps the commands are unsynced. Ask {client.bot_owner} ({client.bot_owner.mention}) if she typed {cmd_mention}!")
        elif isinstance(error, discord.app_commands.errors.CommandSignatureMismatch):
            await reply(itx, f"Error: CommandSignatureMismatch. Either Mia used GroupCog instead of Cog, or this command is out of date (try /update)")
        else:
            if hasattr(error, 'original'):
                error_reply = "Error "
                if hasattr(error.original, 'status'):
                    error_reply += str(error.original.status)
                    # if error.original.status == "403":
                    #     await reply(itx, f"Error 403: It seems like I didn't have permissions for this action! If you believe this is an error, please message or ping {client.bot_owner}} :)")
                if hasattr(error.original, 'code'):
                    error_reply += "(" + str(error.original.code) + "). "
                await reply(itx, error_reply + f"Please report the error and details to {client.bot_owner} ({client.bot_owner.mention}) by pinging her or sending her a DM")
            else:
                await reply(itx, "Something went wrong executing your command!\n    " + repr(error)[:1700])

        try:
            msg = f"    Executor details: {itx.user} ({itx.user.id})\n"
        except Exception as ex:
            msg = f"    Executor details: couldn't get interaction details: {repr(ex)}\n"
            #   f"    command: {error.command}\n" + \
            #   f"    arguments: {error.args}\n"
        if hasattr(error, 'original'):
            if hasattr(error.original, 'code'):
                msg += f"    code: {error.original.code}\n"
            if hasattr(error.original, 'status'):
                msg += f"    original error: {error.original.status}: {error.original.text}\n\n"
                    #    f"   error response:     {error.original.response}\n\n"
        msg += traceback.format_exc()
        await send_crash_message("AppCommand Error", msg, f"</{itx.command.name}:{itx.data.get('id')}>", discord.Colour.from_rgb(r=255, g=121, b=77), itx=itx)
        appcommanderror_cooldown = int(mktime(datetime.now().timetuple()))

    try:
        client.run(TOKEN, log_level=logging.WARNING)
    except SystemExit:
        print("Exited the program forcefully using the kill switch")
    #endregion

#region TODO:
# - Translator
# - (Unisex) compliment quotes
# - Add error catch for when dictionaryapi.com is down
# - make more three-in-one commands have optional arguments, explaining what to do if you don't fill in the optional argument
        
#endregion
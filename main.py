from datetime import datetime # for startup and crash logging, and Reminders
program_start = datetime.now() # first startup time datetime; for logging startup duration
from time import mktime # to convert datetime to unix epoch time to store in database
import discord # for main discord bot functionality
import json # for loading the API keys file
import sys # to stop the program (and automatically restart, thanks to pterodactyl)
import logging # to set logging level to not DEBUG and hide unnecessary logs
import traceback # for crash logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler # for scheduling Reminders
from pymongo.database import Database as pymongodatabase # for MongoDB database typing
from pymongo import MongoClient
import motor.motor_asyncio as motorasync # for making Mongo run asynchronously (during api calls)
import motor.core as motorcore # for typing

from resources.utils.utils import debug # for logging crash messages
from resources.customs.bot import Bot
from resources.customs.reminders import ReminderObject # Reminders (/reminders remindme)
from resources.customs.watchlist import get_or_fetch_watchlist_index # for fetching all watchlists on startup


BOT_VERSION = "1.2.9.13"
TESTING_ENVIRONMENT = 2 # 1 = public test server (Supporter server) ; 2 = private test server (transplace staff only)
appcommanderror_cooldown = 0

EXTENSIONS = [
    "cmd_addons",
    "cmd_ban_appeal_reactions",
    "cmd_compliments",
    "cmd_customvcs",
    "cmd_emojistats",
    "cmd_help",
    "cmd_getmemberdata",
    #"cmd_pronouns", # depreciated
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
    "cmd_starboard",
]

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

def get_token_data() -> tuple[str, dict[str, str], pymongodatabase, motorcore.AgnosticDatabase]:
    """
    Ensures the api_keys.json file contains all of the bot's required keys, and uses these keys to start a link to the MongoDB.

    Returns
    --------
    :class:`tuple[discord_token, other_api_keys, synchronous_db_connection, async_db_connection]`:
        Tuple of discord bot token and database client cluster connections.

    Raises
    -------
    :class:`FileNotFoundError`:
        if the api_keys.json file does not exist.
    :class:`json.decoder.JSONDecodeError`:
        if the api_keys.json file is not in correct JSON format.
    :class:`KeyError`:
        if the api_keys.json file is missing the api key for an api used in the program.
    """
    debug(f"[#+   ]: Loading api keys..." + " " * 30, color="light_blue", end='\r')
    # debug(f"[+     ]: Loading server settings" + " " * 30, color="light_blue", end='\r')
    try:
        with open("api_keys.json","r") as f:
            api_keys = json.loads(f.read())
        tokens = {}
        bot_token: str = api_keys['Discord']
        missing_tokens: list[str] = []
        for key in ['MongoDB', 'Open Exchange Rates', 'Wolfram Alpha']:
            # copy every other key to new dictionary to check if every key is in the file.
            if key not in api_keys:
                missing_tokens.append(key)
                continue
            tokens[key] = api_keys[key]
    except FileNotFoundError:
        raise
    except json.decoder.JSONDecodeError:
        raise json.decoder.JSONDecodeError("Invalid JSON file. Please ensure it has correct formatting.").with_traceback(None)
    if missing_tokens:
        raise KeyError("Missing API key for: " + ', '.join(missing_tokens))
    
    debug(f"[##+  ]: Loading database clusters..." + " " * 30, color="light_blue", end='\r')
    cluster: MongoClient = MongoClient(tokens['MongoDB'])
    RinaDB: pymongodatabase = cluster["Rina"]
    cluster: motorcore.AgnosticClient = motorasync.AsyncIOMotorClient(tokens['MongoDB'])
    asyncRinaDB: motorcore.AgnosticDatabase = cluster["Rina"]
    debug(f"[###+ ]: Loading version..." + " " * 30, color="light_blue", end='\r')
    return (bot_token, tokens, RinaDB, asyncRinaDB)

def get_version() -> str:
    """
    Dumb code for cool version updates. Reads version file and matches with current version string. Updates file if string is newer, and adds another ".%d" for how often the bot has been started in this version.

    Returns
    --------
    :class:`str`:
        Current version/instance of the bot.
    """
    fileVersion = BOT_VERSION.split(".")
    try:
        with open("outputs/version.txt", "r") as f:
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
    with open("outputs/version.txt","w") as f:
        f.write(f"{version}")
    return version

def create_client(tokens: dict, RinaDB: pymongodatabase, asyncRinaDB: motorcore.AgnosticDatabase, version: str) -> Bot:
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
            await get_or_fetch_watchlist_index(watchlist_channel)
        debug(f"[#]: Loaded watchlist threads."+" "*15, color="green")
    
    @client.event
    async def setup_hook():
        logger = logging.getLogger("apscheduler")
        logger.setLevel(logging.WARNING)
        # remove annoying 'Scheduler started' message on sched.start()
        client.sched = AsyncIOScheduler(logger=logger)
        client.sched.start()

        ## cache server settings into client, to prevent having to load settings for every extension
        debug(f"[##     ]: Started Bot"+" "*30,color="green")
        ## activate the extensions/programs/code for slash commands

        extension_loading_start_time = datetime.now()
        for extID in range(len(EXTENSIONS)):
            debug(f"[{'#'*extID}+{' '*(len(EXTENSIONS)-extID-1)}]: Loading {EXTENSIONS[extID]}"+" "*15,color="light_blue",end='\r')
            await client.load_extension("extensions."+EXTENSIONS[extID])
        debug(f"[###    ]: Loaded extensions successfully (in {datetime.now()-extension_loading_start_time})",color="green")

        debug(f"[###+   ]: Loading server settings"+ " "*30,color="light_blue",end='\r')
        try:
            client.log_channel = await client.fetch_channel(988118678962860032)
        except (discord.errors.InvalidData, discord.errors.HTTPException, discord.errors.NotFound, discord.errors.Forbidden): #one of these
            client.running_on_production = False
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
    async def send_crash_message(
            error_type: str,
            traceback_text: str,
            error_source: str,
            color: discord.Colour,
            itx: discord.Interaction | None = None
    ) -> None:
        """
        Sends crash message to Rina's main logging channel

        Parameters
        -----------
        error_type: :class:`str`
            Is it an 'Error' or an 'AppCommand Error'
        traceback_text: :class:`str`
            The traceback to send.
        error_source: :class:`str`
            Name of the error source, displayed at the top of the message. Think of event or command.
        color: :class:`discord.Colour`
            Color of the discord embed.
        itx: :class:`discord.Interaction` | :class:`None`, optional
            Interaction with a potential guild. This might allow Rina to send the crash log to that guild instead. Default: None.
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
        embed = discord.Embed(color=color, title = error_type +' Log', description=msg[:4095]) # max length of 4096 chars
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
        
        cmd_mention = client.get_command_mention("update")
        if isinstance(error, discord.app_commands.errors.CommandNotFound):
            await reply(itx, f"This command doesn't exist! Perhaps the commands are unsynced. Ask {client.bot_owner} ({client.bot_owner.mention}) if she typed {cmd_mention}!")
        elif isinstance(error, discord.app_commands.errors.CommandSignatureMismatch):
            await reply(itx, f"Error: CommandSignatureMismatch. Either Mia used GroupCog instead of Cog, or this command is out of date (try {cmd_mention})")
        else:
            if hasattr(error, 'original'):
                error_reply = "Error"
                if hasattr(error.original, 'status'):
                    error_reply += " " + str(error.original.status)
                    # if error.original.status == "403":
                    #     await reply(itx, f"Error 403: It seems like I didn't have permissions for this action! If you believe this is an error, please message or ping {client.bot_owner}} :)")
                if hasattr(error.original, 'code'):
                    error_reply += " (" + str(error.original.code) + ")"
                await reply(itx, error_reply + f". Please report the error and details to {client.bot_owner} ({client.bot_owner.mention}) by pinging her or sending her a DM")
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
        # details: /help `page:1` `param2:hey`
        command_details = f"</{itx.command.name}:{itx.data.get('id')}> " + ' '.join([f"`{k}:{v}`" for k, v in itx.namespace.__dict__.items()])
        await send_crash_message("AppCommand Error", msg, command_details, discord.Colour.from_rgb(r=255, g=121, b=77), itx=itx)
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

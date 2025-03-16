from apscheduler.schedulers.asyncio import AsyncIOScheduler  # for scheduling Reminders
from datetime import datetime  # for startup and crash logging, and Reminders
import json  # for loading the API keys file
import logging  # to set logging level to not DEBUG and hide unnecessary logs
import motor.motor_asyncio as motorasync  # for making Mongo run asynchronously (during api calls)
import motor.core as motorcore  # for typing
import os  # for creating outputs/ directory
from pymongo.database import Database as PyMongoDatabase  # for MongoDB database typing
from pymongo import MongoClient
from time import mktime  # to convert datetime to unix epoch time to store in database
from typing import Literal, TypedDict

import discord  # for main discord bot functionality

from resources.customs.bot import Bot, ApiTokenDict
from resources.utils.utils import debug, TESTING_ENVIRONMENT  # for logging crash messages

from extensions.reminders.objects import ReminderObject  # Reminders (/reminders remindme)
from extensions.watchlist.watchlistfunctions import get_or_fetch_watchlist_index
# ^ for fetching all watchlists on startup


program_start = datetime.now()  # startup time after local imports

BOT_VERSION = "1.3.0.5"

EXTENSIONS = [
    "addons",
    "aegis_ping_reactions",
    "ban_appeal_reactions",
    "compliments",
    "crashhandling",
    "customvcs",
    "emojistats",
    "help",
    "getmemberdata",
    # "pronouns", # depreciated
    "qotw",
    "staffaddons",
    "tags",
    "termdictionary",
    "todolist",
    "toneindicator",
    "vclogreader",
    "watchlist",
    "starboard",
    "nameusage",
    "reminders",
    # "testing_commands",
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
#       manage channels (Global: You need this to be able to set the position of CustomVCs in a category, apparently)
#           NEEDS TO BE GLOBAL?
#           Create and Delete voice channels
#       use embeds (for starboard)
#       use (external) emojis (for starboard, if you have external starboard reaction...?)

def get_token_data() -> tuple[
    str,
    ApiTokenDict,
    PyMongoDatabase,
    motorcore.AgnosticDatabase
]:
    """
    Ensures the api_keys.json file contains all the bot's required keys, and
    uses these keys to start a link to the MongoDB.

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
        with open("api_keys.json", "r") as f:
            api_keys = json.loads(f.read())
        tokens = {}
        bot_token: str = api_keys['Discord']
        missing_tokens: list[str] = []
        for key in ApiTokenDict.__required_keys__:
            # copy every other key to new dictionary to check if every key is in the file.
            if key not in api_keys:
                missing_tokens.append(key)
                continue
            tokens[key] = api_keys[key]
    except FileNotFoundError:
        raise
    except json.decoder.JSONDecodeError as ex:
        raise json.decoder.JSONDecodeError(
            "Invalid JSON file. Please ensure it has correct formatting.", ex.doc, ex.pos).with_traceback(None)
    if missing_tokens:
        raise KeyError("Missing API key for: " + ', '.join(missing_tokens))

    debug(f"[##+  ]: Loading database clusters..." + " " * 30, color="light_blue", end='\r')
    cluster: MongoClient = MongoClient(tokens['MongoDB'])
    rina_db: PyMongoDatabase = cluster["Rina"]
    cluster: motorcore.AgnosticClient = motorasync.AsyncIOMotorClient(tokens['MongoDB'])
    async_rina_db: motorcore.AgnosticDatabase = cluster["Rina"]
    debug(f"[###  ]: Loaded database clusters" + " " * 30, color="green", end='r')
    return bot_token, tokens, rina_db, async_rina_db


def get_version() -> str:
    """
    Dumb code for cool version updates. Reads version file and matches with current version string. Updates file if
    string is newer, and adds another ".%d" for how often the bot has been started in this version.

    Returns
    --------
    :class:`str`:
        Current version/instance of the bot.
    """
    debug(f"[###+ ]: Loading version..." + " " * 30, color="light_blue", end='\r')
    file_version = BOT_VERSION.split(".")
    try:
        os.makedirs("outputs", exist_ok=True)
        with open("outputs/version.txt", "r") as f:
            rina_version = f.read().split(".")
    except FileNotFoundError:
        rina_version = ["0"] * len(file_version)
    # if testing, which environment are you in?
    # 1: private dev server; 2: public dev server (TransPlace [Copy])
    for v in range(len(file_version)):
        if int(file_version[v]) > int(rina_version[v]):
            rina_version = file_version + ["0"]
            break
    else:
        rina_version[-1] = str(int(rina_version[-1]) + 1)
    rina_version = '.'.join(rina_version)
    with open("outputs/version.txt", "w") as f:
        f.write(f"{rina_version}")
    debug(f"[#### ]: Loaded version" + " " * 30, color="green", end='\r')
    return rina_version


def create_client(
        tokens: ApiTokenDict,
        rina_db: PyMongoDatabase,
        async_rina_db: motorcore.AgnosticDatabase,
        version: str
) -> Bot:
    debug(f"[####+]: Creating bot" + " " * 30, color="light_blue", end='\r')

    intents = discord.Intents.default()
    intents.members = True  # apparently this needs to be defined because it's not included in Intents.default()?
    intents.message_content = True  # to send 1984, and to otherwise read message content.
    # setup default discord bot client settings, permissions, slash commands, and file paths

    discord.VoiceClient.warn_nacl = False
    bot: Bot = Bot(
        api_tokens=tokens,
        version=version,
        rina_db=rina_db,
        async_rina_db=async_rina_db,

        intents=intents,
        command_prefix="/!\"@:\\#",
        #  unnecessary, but needs to be set so... uh... yeah. Unnecessary terminal warnings avoided.
        case_insensitive=True,
        activity=discord.Game(name="with slash (/) commands!"),
        allowed_mentions=discord.AllowedMentions(everyone=False)
    )
    debug(f"[#      ]: Created Bot" + " " * 30, color="green")
    return bot


def start_app():
    (token, tokens, rina_db, async_rina_db) = get_token_data()
    version = get_version()
    client = create_client(tokens, rina_db, async_rina_db, version)
    debug(f"[#+     ]: Starting Bot...", color="light_blue", end='\r')

    # this can probably be done better
    # region Client events
    @client.event
    async def on_ready():
        debug(f"[#######]: Logged in as {client.user}, in version {version} (in {datetime.now() - program_start})",
              color="green")
        await client.log_channel.send(f":white_check_mark: **Started Rina** in version {version}")

        debug(f"[+]: Pre-loading all watchlist threads", color="light_blue", end="\r")
        watchlist_channel = client.get_channel(client.custom_ids["staff_watch_channel"])
        if watchlist_channel is not None:  # if running on prod
            await get_or_fetch_watchlist_index(watchlist_channel)
        debug(f"[#]: Loaded watchlist threads." + " " * 15, color="green")

    @client.event
    async def setup_hook():
        debug(f"[##     ]: Started Bot" + " " * 30, color="green")
        debug(f"[##+    ]: Load extensions and scheduler", color="light_blue", end="\r")
        logger = logging.getLogger("apscheduler")
        logger.setLevel(logging.WARNING)
        # remove annoying 'Scheduler started' message on sched.start()
        client.sched = AsyncIOScheduler(logger=logger)
        client.sched.start()

        # Cache server settings into client, to prevent having to load settings for every extension
        # Activate the extensions/programs/code for slash commands

        extension_loading_start_time = datetime.now()
        for extID in range(len(EXTENSIONS)):
            debug(f"[{'#' * extID}+{' ' * (len(EXTENSIONS) - extID - 1)}]: Loading {EXTENSIONS[extID]}" + " " * 15,
                  color="light_blue", end='\r')
            await client.load_extension("extensions." + EXTENSIONS[extID] + ".module")
        debug(f"[###    ]: Loaded extensions successfully (in {datetime.now() - extension_loading_start_time})",
              color="green")

        debug(f"[###+   ]: Loading server settings" + " " * 30, color="light_blue", end='\r')
        try:
            client.log_channel = await client.fetch_channel(988118678962860032)
        except (discord.errors.InvalidData, discord.errors.HTTPException, discord.errors.NotFound,
                discord.errors.Forbidden):  # one of these
            client.running_on_production = False
            if TESTING_ENVIRONMENT == 1:
                client.log_channel = await client.fetch_channel(986304081234624554)
            else:
                client.log_channel = await client.fetch_channel(1062396920187863111)
        client.bot_owner = await client.fetch_user(262913789375021056)  # (await client.application_info()).owner
        # can't use the commented out code because Rina is owned by someone else in the main server than
        # the dev server (=not me).

        debug(f"[####   ]: Loaded server settings" + " " * 30, color="green")
        debug(f"[####+  ]: Restarting ongoing reminders" + " " * 30, color="light_blue", end="\r")
        collection = rina_db["reminders"]
        query = {}
        db_data = collection.find(query)
        for user in db_data:
            try:
                for reminder in user['reminders']:
                    creation_time = datetime.fromtimestamp(reminder['creationtime'])  # , timezone.utc)
                    reminder_time = datetime.fromtimestamp(reminder['remindertime'])  # , timezone.utc)
                    ReminderObject(client, creation_time, reminder_time, user['userID'], reminder['reminder'], user,
                                   continued=True)
            except KeyError:
                pass
        debug(f"[#####  ]: Finished setting up reminders" + " " * 30, color="green")
        debug(f"[#####+ ]: Caching bot's command names and their ids", color="light_blue", end='\r')
        client.commandList = await client.tree.fetch_commands()
        debug(f"[###### ]: Cached bot's command names and their ids" + " " * 30, color="green")
        debug(f"[######+]: Starting..." + " " * 30, color="light_blue", end='\r')

    # endregion

    client.run(token, log_level=logging.WARNING)


try:
    start_app()
except SystemExit:
    print("Exited the program forcefully using the kill switch")

# region TODO:
# - Translator
# - (Unisex) compliment quotes
# - Add error catch for when dictionaryapi.com is down
# - make more three-in-one commands have optional arguments, explaining what to do if you don't
#       fill in the optional argument

# endregion

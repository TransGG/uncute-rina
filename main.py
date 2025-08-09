#!/usr/bin/env python3
import typing

from apscheduler.schedulers.asyncio import AsyncIOScheduler
# ^ for periodic timers
from datetime import datetime  # for startup and crash logging
import json  # for loading the API keys file
import logging  # to set logging level to not DEBUG and hide unnecessary logs
import motor.motor_asyncio as motorasync
# ^ for making Mongo run asynchronously (during api calls)
import motor.core as motorcore  # for typing
import os  # for creating outputs/ directory
from pymongo.database import Database as PyMongoDatabase
# ^ for MongoDB database typing
from pymongo import MongoClient

import discord  # for main discord bot functionality

from extensions.reminders.objects import \
    relaunch_ongoing_reminders
from extensions.settings.objects import ServerSettings, MessageableGuildChannel
from extensions.starboard.local_starboard import fetch_all_starboard_messages
from extensions.tags.local_tag_list import fetch_all_tags
from extensions.watchlist.local_watchlist import fetch_all_watchlists
# ^ for fetching all watchlists on startup

from resources.customs import Bot, ProgressBar
from resources.customs import ApiTokenDict
from resources.utils import debug, codec_options, DebugColor

program_start = datetime.now().astimezone()  # startup time after local imports
BOT_VERSION = "2.0.3.4"

# noinspection SpellCheckingInspection
EXTENSIONS = [
    "addons",
    "changechannel",
    "compliments",
    "crashhandling",
    "customvcs",
    "emojistats",
    "getmemberdata",
    "help",
    "message_reactions",
    "nameusage",
    "qotw",
    "reminders",
    "settings",
    "staff_polls_channel",
    "staffaddons",
    "starboard",
    "tags",
    "termdictionary",
    # "testing_commands",
    "todolist",
    "toneindicator",
    "vclogreader",
    "watchlist",
]

load_progress = ProgressBar(5)
start_progress = ProgressBar(7)


# Permission requirements:
#   server members intent,
#   message content intent,
#   guild permissions:
#       send messages
#       attach files (for image of the member joining graph thing)
#       read channel history (locate previous starboard message, for example)
#       move users between voice channels (custom vc)
#       manage roles (for removing NPA and NVA roles)
#       manage channels (Global: You need this to be able to set the
#        position of CustomVCs in a category, apparently)
#           NEEDS TO BE GLOBAL?
#           Create and Delete voice channels
#       use embeds (for starboard)
#       use (external) emojis (for starboard, if you have external
#        starboard reaction...?)


def get_token_data() -> tuple[
    str,
    ApiTokenDict,
    PyMongoDatabase,
    motorcore.AgnosticDatabase
]:
    """
    Ensures the api_keys.json file contains all the bot's required
    keys, and uses these keys to start a link to the MongoDB.

    :return: Tuple of discord bot token, other api tokens, and a sync
    and async database client cluster connection.

    :raise FileNotFoundError: If the api_keys.json file does not exist.
    :raise json.decoder.JSONDecodeError: If the api_keys.json file is
     not in the correct JSON format.
    :raise KeyError: If the api_keys.json file is missing the api key
     for an api used in the program.
    """
    load_progress.begin("Loading api keys...")
    try:
        with open("api_keys.json", "r") as f:
            api_keys = json.loads(f.read())
        tokens = {}
        bot_token: str = api_keys['Discord']
        missing_tokens: list[str] = []
        for key in ApiTokenDict.__annotations__:
            # copy every other key to a new dictionary to check if every
            #  key is in the file.
            if key not in api_keys:
                missing_tokens.append(key)
                continue
            tokens[key] = api_keys[key]
        tokens = ApiTokenDict(**tokens)
    except FileNotFoundError:
        raise
    except json.decoder.JSONDecodeError as ex:
        raise json.decoder.JSONDecodeError(
            "Invalid JSON file. Please ensure it has correct formatting.",
            ex.doc,
            ex.pos
        ).with_traceback(None)
    if missing_tokens:
        raise KeyError("Missing API key for: " + ', '.join(missing_tokens))

    load_progress.begin("Loading database clusters...")
    mongo_client: MongoClient = MongoClient(tokens['MongoDB'])
    rina_db: PyMongoDatabase = mongo_client["Rina"]
    cluster: motorcore.AgnosticClient = motorasync.AsyncIOMotorClient(
        tokens['MongoDB'])
    async_rina_db: motorcore.AgnosticDatabase  # = cluster["Rina"]
    async_rina_db = cluster.get_database("Rina", codec_options=codec_options)
    load_progress.complete("Loaded database clusters", newline=False)

    return bot_token, tokens, rina_db, async_rina_db


def get_version() -> str:
    """
    Get the bot's version as dot-separated string, like 1.0.2.0.0

    Dumb code for cool version updates. It reads the version file and matches
    it with the current version string. Updates file if string is newer, and
    adds another ".%d" for how often the bot has been started in this version.

    :return: Current version/instance of the bot.
    """
    load_progress.begin("Loading version...")
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
    load_progress.complete("Loaded version", newline=False)
    return rina_version


def create_client(
        tokens: ApiTokenDict,
        rina_db: PyMongoDatabase,
        async_rina_db: motorcore.AgnosticDatabase,
        version: str
) -> Bot:
    load_progress.begin("Creating bot")

    intents = discord.Intents.default()
    intents.members = True
    # ^ apparently this needs to be defined because it's not included
    #  in Intents.default()?
    intents.message_content = True
    # to send 1984, and to otherwise read message content.

    # setup default discord bot client settings, permissions,
    #  slash commands, and file paths
    discord.VoiceClient.warn_nacl = False
    bot: Bot = Bot(
        api_tokens=tokens,
        version=version,
        rina_db=rina_db,
        async_rina_db=async_rina_db,

        intents=intents,
        command_prefix="/!\"@:\\#",
        # Unnecessary, but needs to be set so... uh... yeah. Unnecessary
        #  terminal warnings avoided.
        case_insensitive=True,
        activity=discord.Game(name="with slash (/) commands!"),
        allowed_mentions=discord.AllowedMentions(everyone=False),
    )
    start_progress.complete("Created Bot")
    return bot


def start_app():
    (token, tokens, rina_db, async_rina_db) = get_token_data()
    version = get_version()
    client = create_client(tokens, rina_db, async_rina_db, version)
    start_progress.begin("Starting Bot...")

    # this can probably be done better
    # region Client events
    @client.event
    async def on_ready():
        text = (f"Logged in as {client.user}, in version {version} "
                f"(in {datetime.now().astimezone() - program_start})")
        try:
            start_progress.complete(text)
        except OverflowError:
            debug(text, color=DebugColor.green)

        await client.log_channel.send(
            f":white_check_mark: **Started Rina** in version {version}")

        post_startup_progress = ProgressBar(4)

        post_startup_progress.begin("Loading all server settings...")
        client.server_settings = await ServerSettings.fetch_all(client)
        post_startup_progress.complete("Loaded server settings.")

        post_startup_progress.begin("Loading all server tags...")
        try:
            _ = await fetch_all_tags(client.async_rina_db)
        except Exception as ex:
            debug(
                f"Loading tags failed!\n"
                f"Reason: {ex}",
                color=DebugColor.red
            )
        else:
            post_startup_progress.complete("Loaded server tags.")

        post_startup_progress.begin("Loading all watchlist threads...")
        try:
            _ = await fetch_all_watchlists(client.async_rina_db)
        except Exception as ex:
            debug(
                f"Loading watchlists failed!\n"
                f"Reason: {ex}",
                color=DebugColor.red
            )
        else:
            post_startup_progress.complete("Loaded watchlist threads.")

        post_startup_progress.begin("Loading all starboard messages...")
        try:
            _ = await fetch_all_starboard_messages(client.async_rina_db)
        except Exception as ex:
            debug(
                f"Loading starboard failed!\n"
                f"Reason: {ex}",
                color=DebugColor.red
            )
        else:
            post_startup_progress.complete("Loaded starboard messages.")

    @client.event
    async def setup_hook():
        start_progress.complete("Started Bot")
        start_progress.begin("Caching bot's command names and their ids")
        client.commandList = await client.tree.fetch_commands()
        start_progress.complete("Cached bot's command names and their ids")
        start_progress.begin("Load extensions and scheduler")
        logger = logging.getLogger("apscheduler")
        logger.setLevel(logging.WARNING)
        # remove annoying 'Scheduler started' message on sched.start()
        client.sched = AsyncIOScheduler(logger=logger)
        client.sched.start()

        # Cache server settings into client, to prevent having to load
        #  settings for every extension.
        # Activate the extensions/programs/code for slash commands

        extension_loading_start_time = datetime.now().astimezone()
        extension_load_progress = ProgressBar(len(EXTENSIONS))
        for extID in range(len(EXTENSIONS)):
            extension_load_progress.begin(f"Loading {EXTENSIONS[extID]}")
            await client.load_extension(
                "extensions." + EXTENSIONS[extID] + ".module")
        start_progress.complete(
            f"Loaded extensions successfully (in "
            f"{datetime.now().astimezone() - extension_loading_start_time})"
        )
        start_progress.begin("Loading server settings...")
        try:
            log_channel = await client.fetch_channel(988118678962860032)
        except discord.errors.Forbidden:
            # client.log_channel = \
            #     await client.fetch_channel(986304081234624554)
            log_channel = await client.fetch_channel(1062396920187863111)
        if not isinstance(log_channel, MessageableGuildChannel.__value__):
            raise TypeError(
                f"Backup log channel expected a messageable guild channel, "
                f"but got {type(log_channel)} instead!"
            )
        log_channel = typing.cast(MessageableGuildChannel, log_channel)
        client.log_channel = log_channel
        client.bot_owner = await client.fetch_user(262913789375021056)
        # client.bot_owner = (await client.application_info()).owner
        # ^ or client.owner / client.owner_id :P
        # can't use the commented out code because Rina is owned by
        # someone else in the main server than the dev server (=not me).
        start_progress.complete("Loaded server settings")
        start_progress.begin("Restarting ongoing reminders...")
        await relaunch_ongoing_reminders(client)
        start_progress.complete("Finished setting up reminders")
        start_progress.begin("Starting...")

    # endregion

    client.run(token, log_level=logging.WARNING)


if __name__ == "__main__":
    try:
        start_app()
    except SystemExit:
        print("Exited the program forcefully using the kill switch")


# region TODO:
# - Translator
# - (Unisex) compliment quotes
# - Add error catch for when dictionaryapi.com is down
# - make more three-in-one commands have optional arguments, explaining
#   what to do if you don't fill in the optional argument.

# endregion

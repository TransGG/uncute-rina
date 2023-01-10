import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *
# import signal # save files when receiving KeyboardInterrupt
# import sys # exit program after Keyboardinterrupt signal is noticed

from datetime import datetime, timedelta, timezone
from time import mktime # for unix time code
import random # for very uncute responses

import pymongo # for online database
from pymongo import MongoClient

import sys # kill switch for rina (search for :kill)

mongoURI = open("mongo.txt","r").read()
cluster = MongoClient(mongoURI)
RinaDB = cluster["Rina"]

# Dependencies:
#   server members intent,
#   message content intent,
#   permissions:
#       send messages
#       attach files (for image of the member joining graph thing)
#       read channel history (find previous Table messages from a specific channel afaik)
#       create and delete voice channels
#       move users between voice channels
#       manage roles (for adding/removing table roles)
#       manage channels (Global: You need this to be able to set the position of CustomVCs in a category, apparently) NEEDS TO BE GLOBAL?

# dumb code for cool version updates
fileVersion = "1.1.4.10".split(".")
try:
    version = open("version.txt", "r").read().split(".")
except:
    version = ["0"]*len(fileVersion)
# if testing, which environment are you in?
# 1: private dev server; 2: public dev server (TransPlace [Copy])
testing_environment = 2

for v in range(len(fileVersion)):
    if int(fileVersion[v]) > int(version[v]):
        version = fileVersion + ["0"]
        break
else:
    version[-1] = str(int(version[-1])+1)
version = '.'.join(version)
open("version.txt","w").write(f"{version}")


intents = discord.Intents.default()
intents.members = True #apparently this needs to be additionally defined cause it's not included in Intents.default()?
intents.message_content = True #apparently it turned off my default intent or something: otherwise i can't send 1984, ofc.
#setup default discord bot client settings, permissions, slash commands, and file paths

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    commandList: list[discord.app_commands.AppCommand]
    logChannel: discord.TextChannel

    def getCommandMention(self, _command):
        args = _command.split(" ")+[None, None]
        command_name, subcommand, subcommand_group = args[0:3]
        # returns one of the following:
        # </COMMAND:COMMAND_ID>
        # </COMMAND SUBCOMMAND:ID>
        #              \/- is posed as 'subcommand', to make searching easier
        # </COMMAND SUBCOMMAND_GROUP SUBCOMMAND:ID>
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
        return "/"+_command

client = Bot(
        intents=intents,
        command_prefix="/!\"@:\\#", #unnecessary, but needs to be set so.. uh.. yeah. Unnecessary terminal warnings avoided.
        case_insensitive=True,
        activity=discord.Game(name="with slash (/) commands!"),
        allowed_mentions=discord.AllowedMentions(everyone=False)
    )
program_start = datetime.now()
debug("Program started")

# Client events begin
@client.event
async def on_ready():
    debug(f"[#####] Logged in as {client.user}, in version {version} (in {datetime.now()-program_start})",color="green")
    await client.logChannel.send(f":white_check_mark: **Started Rina** in version {version}")

@client.event
async def setup_hook():
    start = datetime.now()

    ## cache server settings into client, to prevent having to load settings for every extension
    debug(f"[+    ]: Loading server settings"+" "*30,color="light_blue",end='\r')
    client.RinaDB = RinaDB
    debug(f"[#    ]: Loaded server settings"+" "*30,color="green")
    ## activate the extensions/programs/code for slash commands
    extensions = [
        "cmd_addons",
        "cmd_customvcs",
        "cmd_emojistats",
        "cmd_getmemberdata",
        "cmd_pronouns",
        "cmd_qotw",
        "cmd_termdictionary",
        "cmd_todolist",
        "cmd_toneindicator",
        "cmdg_Reminders",
        "cmdg_Starboard",
        # "cmdg_Table", # Disabled: it was never used. Will keep file in case of future projects
    ]

    for extID in range(len(extensions)):
        debug(f"[{'#'*extID}{' '*(len(extensions)-extID-1)} ]: Loading {extensions[extID]}"+" "*15,color="light_blue",end='\r')
        await client.load_extension(extensions[extID])
    debug(f"[##   ]: Loaded extensions successfully (in {datetime.now()-start})",color="green")

    ## activate the buttons in the table message
    ## Disabled: it was never used. Will keep file in case of future projects
    # debug(f"[##+   ]: Updating table message"+ " "*30,color="light_blue",end='\r')
    try:
        client.logChannel = await client.fetch_channel(988118678962860032)
    except (discord.errors.InvalidData, discord.errors.HTTPException, discord.errors.NotFound, discord.errors.Forbidden): #one of these
        if testing_environment == 1:
            client.logChannel = await client.fetch_channel(986304081234624554)
        else:
            client.logChannel = await client.fetch_channel(1062079367653630033)
    # 
    # from cmdg_Table import Table
    # class Interaction:
    #     async def set(self):
    #         guild = client.logChannel.guild
    #         self.guild = guild
    #         self.guild_id = guild.id
    # itx = Interaction()
    # await itx.set()
    # await Table.tablemsgupdate(Table, itx)
    # debug(f"[###   ]: Updated table message"+ " "*30,color="green")
    debug(f"[##+  ]: Restarting ongoing reminders"+" "*30,color="light_blue",end="\r")
    from cmdg_Reminders import Reminders
    collection = RinaDB["reminders"]
    query = {}
    db_data = collection.find(query)
    for user in db_data:
        try:
            for reminder in user['reminders']:
                creationtime = datetime.fromtimestamp(reminder['creationtime'])#, timezone.utc)
                remindertime = datetime.fromtimestamp(reminder['remindertime'])#, timezone.utc)
                Reminders.Reminder(client, creationtime, remindertime, user['userID'], reminder['reminder'], user, continued=True)
        except KeyError:
            pass
    debug(f"[###  ]: Finished setting up reminders"+" "*30,color="green")
    debug(f"[###+ ]: Caching bot's command names and their ids",color="light_blue",end='\r')
    commandList = await client.tree.fetch_commands()
    client.commandList = commandList
    debug(f"[#### ]: Cached bot's command names and their ids"+" "*30,color="green")
    debug(f"[####+]: Starting..."+" "*30,color="light_blue",end='\r')

    # debug(f"[{'#'*extID}{' '*(len(extensions)-extID-1)} ]: Syncing command tree"+ " "*30,color="light_blue",end='\r')
    # await client.tree.sync()

@client.event
async def on_message(message):
    # kill switch, see cmd_addons for other on_message events.
    if message.author.id == 262913789375021056:
        if message.content == ":kill now please okay u need to stop.":
            sys.exit(0)

# Bot commands begin

@client.tree.command(name="version",description="Get bot version")
async def botVersion(itx: discord.Interaction):
    await itx.response.send_message(f"Bot is currently running on v{version}")

@client.tree.command(name="update",description="Update slash-commands")
async def updateCmds(itx: discord.Interaction):
    if not isStaff(itx):
        await itx.response.send_message("Only Staff can update the slash commands (to prevent ratelimiting)", ephemeral=True)
        return
    await client.tree.sync()
    commandList = await client.tree.fetch_commands()
    client.commandList = commandList
    await itx.response.send_message("Updated commands")

@client.event
async def on_error(event, *args, **kwargs):
    import traceback #, logging
    collection = RinaDB["guildInfo"]
    try:
        logGuild = await client.fetch_guild(959551566388547676)
    except discord.errors.Forbidden:
        if testing_environment == 1:
            logGuild = await client.fetch_guild(985931648094834798)
        else:
            logGuild = await client.fetch_guild(1046086050029772840)

    query = {"guild_id": logGuild.id}
    guild = collection.find_one(query)
    if guild is None:
        debug("Not enough data is configured to do this action! Please fix this with `/editguildinfo`!",color="red")
        return
    vcLog      = guild["vcLog"]
    #message = args[0]
    msg = ""
    msg += f"\n\n\n\n[{datetime.now().strftime('%H:%M:%S.%f')}] [ERROR]: {event}\n\n"
    msg += traceback.format_exc()
    debug(f"{msg}",addTime=False)

    # msg += '\n\n          '.join([repr(i) for i in args])+"\n\n"
    # msg += '\n\n                   '.join([repr(i) for i in kwargs])
    msg = msg.replace("\\","\\\\").replace("*","\\*").replace("`","\\`").replace("_","\\_").replace("~~","\\~\\~")
    channel = await logGuild.fetch_channel(vcLog)
    embed = discord.Embed(color=discord.Colour.from_rgb(r=181, g=69, b=80), title='Error log', description=msg)
    await channel.send("<@262913789375021056>", embed=embed)

try:
    client.run(open('token.txt',"r").read())
except SystemExit:
    print("Exited the program forcefully using the kill switch")

# todo
# - Translator
# - (Unisex) compliment quotes

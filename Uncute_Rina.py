import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *
# from discord.utils import get #dunno what this is for tbh.
# import json # json used for settings files
# import pickle # pickle used for reactionmsgs file
# import signal # save files when receiving KeyboardInterrupt
# import sys # exit program after Keyboardinterrupt signal is noticed

from datetime import datetime, timedelta
from time import mktime # for unix time code
import random # for very uncute responses

import pymongo # for online database
from pymongo import MongoClient

import asyncio # for threading the extension imports
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

# dumb code for cool version updates
fileVersion = "1.1.1.2".split(".")
try:
    version = open("version.txt", "r").read().split(".")
except:
    version = ["0"]*len(fileVersion)

for v in range(len(fileVersion)):
    if int(fileVersion[v]) > int(version[v]):
        version = fileVersion + ["0"]
        break
else:
    version[-1] = str(  int( version[-1] )+1  )
version = '.'.join(version)
open("version.txt","w").write(f"{version}")


intents = discord.Intents.default()
intents.members = True #apparently this needs to be additionally defined cause it's not included in Intents.default()?
intents.message_content = True #apparently it turned off my default intent or something: otherwise i can't send 1984, ofc.
#setup default discord bot client settings, permissions, slash commands, and file paths
client = commands.Bot(
        intents = intents,
        command_prefix = "/!\"@:\#", #unnecessary, but needs to be set so.. uh.. yeah. Unnecessary terminal warnings avoided.
        case_insensitive=True,
        activity = discord.Game(name="with slash (/) commands!"),
        allowed_mentions = discord.AllowedMentions(everyone = False)
    )
debug("Program started")

# Client events begin
@client.event
async def on_ready():
    debug(f"[####] Logged in as {client.user}, in version {version}",color="green")

@client.event
async def setup_hook():
    start = datetime.now()

    ## cache server settings into client, to prevent having to load settings for every extension
    debug(f"[+   ]: Loading server settings"+ " "*30,color="light_blue",end='\r')
    client.RinaDB = RinaDB
    debug(f"[#   ]: Loaded server settings"+ " "*30,color="green")
    ## activate the extensions/programs/code for slash commands
    extensions = [
        "cmd_addons",
        "cmd_customvcs",
        "cmd_emojistats",
        "cmd_getmemberdata",
        "cmd_pronouns",
        "cmd_todolist",
        "cmd_termdictionary",
        "cmd_toneindicator",
        "cmdg_Table",
        "cmdg_Starboard",
    ]
    for extID in range(len(extensions)):
        debug(f"[{'#'*extID}{' '*(len(extensions)-extID-1)} ]: Loading {extensions[extID]}"+ " "*15,color="light_blue",end='\r')
        await client.load_extension(extensions[extID])
    debug(f"[##  ]: Loaded extensions successfully (in {datetime.now()-start})",color="green")

    ## activate the buttons in the table message
    debug(f"[##+ ]: Updating table message"+ " "*30,color="light_blue",end='\r')
    from cmdg_Table import Table
    class Itx:
        async def set(self):
            try:
                guild = await client.fetch_guild(959551566388547676)
            except discord.errors.Forbidden:
                guild = await client.fetch_guild(985931648094834798)
            self.guild = guild
            self.guild_id = guild.id
    itx = Itx()
    await itx.set()
    await Table.tablemsgupdate(Table, itx)
    debug(f"[### ]: Updated table message"+ " "*30,color="green")
    debug(f"[###+]: Starting..."+ " "*30,color="light_blue")

    # debug(f"[{'#'*extID}{' '*(len(extensions)-extID-1)} ]: Syncing command tree"+ " "*30,color="light_blue",end='\r')
    # await client.tree.sync()

@client.event
async def on_message(message):
    # global last1984msg
    if message.author.bot:
        return
    #random cool commands
    # if message.content.startswith(":say "):
    #     await message.channel.send(message.content.split(" ",1)[1].replace("[[del]]",""))
    #     return
    if client.user.mention in message.content.split():
        msg = message.content.lower()
        if ((("cute" or "cutie" in msg) and "not" in msg) or "uncute" in msg) and "not uncute" not in msg:
            await message.add_reaction("<:this:960916817801535528>")
        elif "cutie" in msg or "cute" in msg:
            responses = [
                "I'm not cute >_<",
                "Nyaa~",
                "Who? Me? No you're mistaken.",
                "I very much deny the cuteness of someone like myself",
                "If you think I'm cute, then you must be uber-cute!!",
                "I don't think so.",
                "Haha. Good joke. Tell me another tomorrow",
                "Ehe, cutie what do u need help with?",
                "No, I'm !cute.",
                "You too!",
                "No, you are <3",
                "[shocked] Wha- w. .. w what?? .. NOo? no im nott?\nwhstre you tslking about?",
                "Oh you were talking to me? I thought you were talking about everyone else here,",
                "Nope. I doubt it. There's no way I can be as cute as you",
                "Maybe.. Maybe I am cute.",
                "If the sun was dying, would you still think I was cute?",
                "Awww. Thanks sweety, but you've got the wrong number",
                ":joy: You *reaaally* think so? You've gotta be kidding me.",
                "If you're gonna be spamming this, .. maybe #general isn't the best channel for that.",
                "You gotta praise those around you as well. "+(message.author.nick or message.author.name)+", for example, is very cute.",
                "Oh by the way, did I say "+(message.author.nick or message.author.name)+" was cute yet? I probably didn't. "+(message.author.nick or message.author.name)+"? You're very cute",
                "Such nice weather outside, isn't it? What- you asked me a question?\nNo you didn't, you're just talking to youself.",
                "".join(random.choice("acefgilrsuwnopacefgilrsuwnopacefgilrsuwnop;;  ") for i in range(random.randint(10,25))), # 3:2 letters to symbols
                "Oh I heard about that! That's a way to get randomized passwords from a transfem!",
                "Cuties are not gender-specific. For example, my cat is a cutie!\nOh wait, species aren't the same as genders. Am I still a catgirl then? Trans-species?",
                "...",
                "Hey that's not how it works!",
                "Hey my lie detector said you are lying.",
                "You know i'm not a mirror, right?",
                "*And the oscar for cutest responses goes to..  YOU!!*",
                "No I am not cute",
                "k",
                (message.author.nick or message.author.name)+", stop lying >:C",
                "BAD!",
                "You're also part of the cuties set",
                "https://cdn.discordapp.com/emojis/920918513969950750.webp?size=4096&quality=lossless",
                "[Checks machine]; Huh? Is my lie detector broken? I should fix that..",
                "Hey, you should be talking about yourself first! After all, how do you keep up with being such a cutie all the time?"]
            respond = random.choice(responses)
            if respond == "BAD!":
                await message.channel.send("https://cdn.discordapp.com/emojis/902351699182780468.gif?size=56&quality=lossless", allowed_mentions=discord.AllowedMentions.none())
            await message.channel.send(respond, allowed_mentions=discord.AllowedMentions.none())
        else:
            await message.channel.send("I use slash commands! Use /command  and see what cool things might pop up! or something\nPS: If you're trying to call me cute: no, i'm not", delete_after=8)

    # if message.content.endswith("🥺"):
    #     for reaction in ["😳","🥺","<:shy:964724545946800218>","👉","👈","<:bwushy:966885955346763867>","<:animeblush:968335608118378586>"]:
    #
    #         await message.add_reaction(reaction)
    #     await message.channel.send(message.content, allowed_mentions=discord.AllowedMentions.none())
    if message.author.id == 262913789375021056:
        if message.content == ":kill now please okay u need to stop.":
            sys.exit(0)
    await client.process_commands(message)

@client.event
async def on_raw_reaction_add(reaction):
    # global reactionmsgs
    pass
    #get the message id from reaction.message_id through the channel (with reaction.channel_id) (oof lengthy process)
    # message = await client.get_channel(reaction.channel_id).fetch_message(reaction.message_id)
    # if message.author == client.user:
    #     if reaction.emoji.name == '❌' and reaction.member != client.user:
    #         await message.delete()

    # if message.author == client.user:
    #     if reaction.member != client.user and str(message.id) in reactionmsgs:
    #         voteMsg = reactionmsgs[str(message.id)]
    #         try:
    #             voteMsg.vote(reaction.member.id, reaction.emoji.name)
    #             message.id = voteMsg.message_id
    #             await message.edit(content=voteMsg.getMessage())
    #         except:
    #             pass
    #         await message.remove_reaction(reaction.emoji.name, reaction.member)

# Bot commands begin

@client.tree.command(name="version",description="Get bot version")
async def botVersion(itx: discord.Interaction):
    await itx.response.send_message(f"Bot is currently running on v{version}")

@client.tree.command(name="update",description="Update slash-commands")
async def updateCmds(itx: discord.Interaction):
    if not isStaff(itx):
        await itx.response.send_message("Only Staff can update the slash commands", ephemeral=True)
        return
    await client.tree.sync()
    await itx.response.send_message("Updated commands")

@client.event
async def on_error(event, *args, **kwargs):
    import traceback, logging
    collection = RinaDB["guildInfo"]
    try:
        logGuild = await client.fetch_guild(959551566388547676)
    except discord.errors.Forbidden:
        logGuild = await client.fetch_guild(985931648094834798)

    query = {"guild_id": logGuild.id}
    guild = collection.find(query)
    try:
        guild = guild[0]
    except IndexError:
        debug("Not enough data is configured to do this action! Please fix this with `/editguildinfo`!",color="red")
        return
    vcLog      = guild["vcLog"]
    #message = args[0]
    msg =  ""
    msg += f"\n\n\n\n[{datetime.now().strftime('%H:%M:%S.%f')}] [ERROR]: {event}\n\n"
    msg += traceback.format_exc()
    msg = msg.replace("Floris","Mia").replace("floris","mia")
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

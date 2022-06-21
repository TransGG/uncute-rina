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
fileVersion = "1.0.2.2".split(".")
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

dataTemplate = {
    "joined"       :{    },
    "left"         :{    },
    "verified"     :{    },
    "totalMembers" :{    }, #todo
    "totalVerified":{    }}
newVcs = {} # make your own vcs!
# last1984msg = 0

print("                            <<<\n"*6+f"[{datetime.now().strftime('%H:%M:%S.%f')}] [INFO]: Program started")

# Client events begin

@client.event
async def on_ready():
    # await client.load_extension("cmd_getmemberdata")
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] [INFO]: Logged in as {client.user}, in version {version}")
    # await client.tree.sync()

@client.event
async def setup_hook():
    await client.load_extension("cmd_getmemberdata")
    await client.load_extension("cmd_toneindicator")
    await client.load_extension("cmdg_Table")
    print("setup_hook complete")

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
                "Hey, you should be talking about yourself first! After all, how do you keep up with being such a cute girl all the time?"]
            respond = random.choice(responses)
            if respond == "BAD!":
                await message.channel.send("https://cdn.discordapp.com/emojis/902351699182780468.gif?size=56&quality=lossless", allowed_mentions=discord.AllowedMentions.none())
            #fix mention permissions # todo
            await message.channel.send(respond)
        else:
            await message.channel.send("Pinging me is fine, and has no consequences, but ```cs\n[ Please don't do it with other bots on this server. ]```You may unintentionally catch the attention of / anger the staff team with it.\nPs: I have slash commands, and no, i'm not cute",delete_after=16)

    if message.content.endswith("🥺"):
        for reaction in ["😳","🥺","<:shy:964724545946800218>","👉","👈","<:bwushy:966885955346763867>","<:animeblush:968335608118378586>"]:

            await message.add_reaction(reaction)
        await message.channel.send(message.content)

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

@client.event
async def on_voice_state_update(member, before, after):
    global newVcs
    collection = RinaDB["guildInfo"]
    query = {"guild_id": member.guild.id}
    guild = collection.find(query)
    try:
        guild = guild[0]
    except IndexError:
        print("Not enough data is configured to do this action! Please fix this with `/editguildinfo`!")
        return
    vcHub      = guild["vcHub"]
    vcLog      = guild["vcLog"]
    vcNoMic    = guild["vcNoMic"]
    vcCategory = guild["vcCategory"]
    if after.channel is not None:
        if after.channel.id == vcHub:
            after.channel.category.id = vcCategory
            defaultName = "Untitled voice chat"
            vc = await after.channel.category.create_voice_channel(defaultName)
            await member.move_to(vc,reason=f"Opened a new voice channel through the vc hub thing.")
            nomicChannel = client.get_channel(vcNoMic)
            await nomicChannel.send(f"Voice channel <#{vc.id}> ({vc.id}) created by <@{member.id}> ({member.id}). Use `/editvc` to edit the name/user limit.", allowed_mentions=discord.AllowedMentions.none())
            logChannel = client.get_channel(vcLog)
            await logChannel.send(content=f"{member.nick or member.name} joined voice channel {vc.id} (with the default name).", allowed_mentions=discord.AllowedMentions.none())
    if before.channel is None:
        print(debug()+f"{member} joined a (new) voice channel but wasn't in one before")
        return
    if before.channel in before.channel.guild.voice_channels:
        if before.channel.category.id not in [vcCategory]:
            print(debug()+"some user left a voice channel that wasn't in the 'deleting vcs' category, u know")
            return
        if before.channel.id == vcHub: # avoid deleting the hub channel
            print(debug()+f"{member} left the vc hub thing")
            return
        if len(before.channel.members) == 0:
            # cmdChannel = discord.utils.find(lambda r: r.name == 'no-mic', before.channel.category.text_channels)
            # await cmdChannel.send(f"{member.nick or member.name} left voice channel \"{before.channel.name}\", and was the last one in it, so it was deleted. ({member.id})",delete_after=32, allowed_mentions = discord.AllowedMentions.none())
            await before.channel.delete()
            try:
                del newVcs[before.channel.id]
            except KeyError:
                pass #haven't edit the channel yet
            logChannel = client.get_channel(vcLog)
            await logChannel.send(f"{member.nick or member.name} ({member.id}) left voice channel \"{before.channel.name}\" ({before.channel.name}), and was the last one in it, so it was deleted.", allowed_mentions=discord.AllowedMentions.none())

# Bot commands begin

@client.tree.command(name="version",description="Get bot version")
async def botVersion(itx: discord.Interaction):
    await itx.response.send_message(f"Bot is currently running on v{version}")

@client.tree.command(name="update",description="Update slash-commands")
@app_commands.describe(reload="Reload commands or update all?")
async def updateCmds(itx: discord.Interaction, reload: bool = False):
    if not isStaff(itx):
        await itx.response.send_message("Only Staff can update the slash commands", ephemeral=True)
        return
    if not reload:
        await client.tree.sync()
        await itx.response.send_message("Updated slash-commands")
    else:
        await client.reload_extension("cmd_getmemberdata")
        await client.reload_extension("cmd_toneindicator")
        await client.reload_extension("cmdg_Table")
        await itx.response.send_message("Reloaded successfully")

@client.tree.command(name="editvc",description="Edit your voice channel name or user limit")
@app_commands.describe(name="Give your voice channel a name!",
                       limit="Give your voice channel a user limit!")
async def editVc(itx: discord.Interaction, name: str, limit: int = 0):
    global newVcs
    collection = RinaDB["guildInfo"]
    query = {"guild_id": itx.guild_id}
    guild = collection.find(query)
    try:
        guild = guild[0]
    except IndexError:
        await itx.response.send_message("Not enough data is configured to do this action! Please ask an admin to fix this with `/editguildinfo`!",ephemeral=True)
        return
    vcHub = guild["vcHub"]
    vcLog = guild["vcLog"]
    vcCategory = guild["vcCategory"]
    # vcHub      = guildInfo[str(itx.guild.id)]["vcHub"]
    # vcLog      = guildInfo[str(itx.guild.id)]["vcLog"]
    # vcCategory = guildInfo[str(itx.guild.id)]["vcCategory"]
    if not isVerified(itx):
        await itx.response.send_message("You don't have the right role to be able to execute this command! (sorrryyy)\n  (This project is still in early stages, if you think this is an error, please message MysticMia#7612)",ephemeral=True) #todo
        return
    if itx.user.voice is None:
        print(debug()+f"{itx.user} tried to make a new vc channel but isn't connected to a voice channel")
        await itx.response.send_message("You must be connected to a voice channel to use this command",ephemeral=True)
        return
    channel = itx.user.voice.channel
    if channel.category.id not in [vcCategory] or channel.id == vcHub:
        await itx.response.send_message("You can't change that voice channel's name!",ephemeral=True)
        return
    if len(name) < 4:
        await itx.response.send_message("Your voice channel name needs to be at least 4 letters long!",ephemeral=True)
        return
    if len(name) > 35:
        await itx.response.send_message("Please don't make your voice channel name more than 35 letters long! (gets cut off/unreadable)",ephemeral=True)
        return
    if limit < 2 and limit != 0:
        await itx.response.send_message("The user limit of your channel must be a positive amount of people... (at least 2; or 0)",ephemeral=True)
        return
    if limit > 99:
        await itx.response.send_message("I don't think you need to prepare for that many people... (max 99, or 0 for infinite)\nIf you need to, message Mia to change the limit",ephemeral=True)
        return
    if name == "Untitled voice chat":
        await itx.response.send_message("Are you really going to change it to that..",ephemeral=True)

    if channel.id in newVcs:
        # if you have made 2 renames in the past 10 minutes already
        if len(newVcs[channel.id]) < 2:
            #ignore but still continue the command
            pass
        elif newVcs[channel.id][0]+600 > mktime(datetime.now().timetuple()):
            await itx.response.send_message("You can't edit your channel more than twice in 10 minutes! (bcuz discord :P)\n"+
            f"You can rename it again <t:{newVcs[channel.id][0]+600}:R> (<t:{newVcs[channel.id][0]+600}:t>).")
            # ignore entirely, don't continue command
            return
        else:
            # clear and continue command
            newVcs[channel.id] = []
    else:
        # create and continue command
        newVcs[channel.id] = []
    newVcs[channel.id].append(int(mktime(datetime.now().timetuple())))
    category = discord.utils.find(lambda r: r.name == 'VC'      , itx.guild.categories)
    verified = discord.utils.find(lambda r: r.name == 'Verifier', itx.guild.roles)
    limitInfo = [" with a user limit of "+str(limit) if limit > 0 else ""][0]
    logChannel = client.get_channel(vcLog)
    oldName = channel.name
    await channel.edit(reason=f"Voice channel renamed from \"{channel.name}\" to \"{name}\"{limitInfo}", user_limit=limit,name=name)
    await logChannel.send(f"Voice channel ({channel.id}) renamed from \"{oldName}\" to \"{name}\" (by {itx.user.nick or itx.user.name}, {itx.user.id}){limitInfo}", allowed_mentions=discord.AllowedMentions.none())
    await itx.response.send_message(f"Voice channel successfully renamed from \"{oldName}\" to \"{name}\""+limitInfo, ephemeral=True)#allowed_mentions=discord.AllowedMentions.none())

@client.tree.command(name="editguildinfo",description="Edit guild settings (staff only)")
@app_commands.describe(vc_hub="Mention the voice channel that should make a new voice channel when you join it",
                       vc_log="Mention the channel in which logs should be posted",
                       vc_category="Mention the category in which new voice channels should be created",
                       vc_nomic="Mention the channel in which guide messages are sent ([x] joined, use /editvc to rename ur vc)")
async def editGuildInfo(itx: discord.Interaction, vc_hub: discord.VoiceChannel = None, vc_log: discord.TextChannel = None, vc_category: discord.CategoryChannel = None, vc_nomic: discord.TextChannel = None):
    if not isAdmin(itx):
        await itx.response.send_message("You don't have the right role to be able to execute this command! (sorrryyy)",ephemeral=True) #todo
        return

    query = {"guild_id": itx.guild_id}
    collection = RinaDB["guildInfo"]
    guildInfo = collection.find(query)

    # if str(itx.guild.id) not in guildInfo:
    #     guildInfo[str(itx.guild_id)] = {}
    if vc_hub is not None:
        collection.update_one(query, {"$set":{"vcHub":vc_hub.id}}, upsert=True)
        # guildInfo[str(itx.guild_id)]["vcHub"] = vc_hub.id
    if vc_log is not None:
        collection.update_one(query, {"$set":{"vcLog":vc_log.id}}, upsert=True)
        # guildInfo[str(itx.guild_id)]["vcLog"] = vc_log.id
    if vc_category is not None:
        collection.update_one(query, {"$set":{"vcCategory":vc_category.id}}, upsert=True)
        # guildInfo[str(itx.guild_id)]["vcCategory"] = vc_category.id
    if vc_nomic is not None:
        collection.update_one(query, {"$set":{"vcNoMic":vc_nomic.id}}, upsert=True)
        # guildInfo[str(itx.guild_id)]["vcNoMic"] = vc_nomic.id
    await itx.response.send_message("Edited the settings.",ephemeral=True)

# @client.tree.command(name="send1984",description="Send annoying message")
# async def send1984(itx: discord.Interaction):
#     if not isStaff(itx):
#         await itx.response.send_message("You don't have the right role to be able to execute this command! (sorrryyy) (it would be too spammy otherwise)",ephemeral=True) #todo
#         return
# #     if ("1984" in message.content or "nineteeneightyfour" in message.content.lower().replace(" ","").replace("-","")) and "@" not in message.content:
# #         if last1984msg > mktime(datetime.utcnow().timetuple())-10*60:
# #             return
# #         await message.reply(content="1984 is about a dictatorship where you are not allowed \
# # to think your own thoughts, and any time you even think differently, the police come for you. \
# # Our server is not like this as we give you freedom to think and do as you like, however, this \
# # does not mean anarchy. Rules are in place to protect the users and ourselves from certain \
# # consequences. **If you would like to know more, please read the book**\n\
# # https://www.planetebook.com/1984/")
#     await itx.channel.send("1984 is a book by George Orwell about a dictatorship where you are not allowed to think \
# your own thoughts, which is drastically different from any situation that can arise on Discord.\n\n\
# **More information:** <https://planetebook.com/1984>")
#     await itx.response.send_message("Sent.",ephemeral=True)

@client.event
async def on_error(event, *args, **kwargs):
    import traceback, logging
    #message = args[0]
    msg =  ""
    msg += f"\n\n\n\n[{datetime.now().strftime('%H:%M:%S.%f')}] [ERROR]: {event}\n\n"
    msg += traceback.format_exc()
    msg += '\n\n          '.join([repr(i) for i in args])+"\n\n"
    msg += '\n\n                   '.join([repr(i) for i in kwargs])
    #channel = await client.get_channel(981623359043407932)
    print(f"{msg}")

# def signal_handler(signal, frame):
#     # try to save files. if they haven't been loaded in yet (discord hasn't started on_read() yet;
#     # and the files are empty, don't save the empty variables into them!) Then exit the program using sys.exit(0)
#     print("📉 Disconnecting...")
#     try:
#         sys.exit(0)
#     except RuntimeError as ru:
#         print("Excepted the runtime error, please ignore everything lol")
#         try:
#             sys.exit(0)
#         except:
#             print("double runtime error?")
#
# signal.signal(signal.SIGINT, signal_handler) #notice KeyboardInterrupt, and run closing code (save files and exit)
client.run(open('token.txt',"r").read())

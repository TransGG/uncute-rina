# dumb code for cool version updates
path = "" # dunno if i should delete this. Could be used if your files are not in the same folder as this program.
fileVersion = "1.0.1.1".split(".")
try:
    version = open("version.txt", "r").read().split(".")
except:
    version = ["0"]*len(fileVersion)

# version =     "0.1.10.2"
for v in range(len(fileVersion)):
    if int(fileVersion[v]) > int(version[v]):
        version = fileVersion + ["0"]
        break
else:
    version[-1] = str(  int( version[-1] )+1  )
version = '.'.join(version)
open("version.txt","w").write(f"{version}")

import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
# from discord_slash import SlashCommand, SlashContext # required for making slash commands
# #from discord_slash.utils.manage_commands import create_permission # limit commands to roles/users
# #from discord_slash.model import SlashCommandPermissionType # limit commands to roles/users
# from discord_slash.utils.manage_commands import create_option, create_choice # set command argument limitations (string/int/bool)
# from discord_slash.context import ComponentContext # button responses

# from discord.utils import get #dunno what this is for tbh.
# import json # json used for settings files
# import pickle # pickle used for reactionmsgs file
# import signal # save files when receiving KeyboardInterrupt
# import sys # exit program after Keyboardinterrupt signal is noticed


import asyncio # used for asyncio.sleep() for debugging purposes (temporary, or at least, it should be- when i wrote this)

from datetime import datetime, timedelta
from time import mktime # for unix time code
import random # for very uncute responses

import pymongo # for online database
from pymongo import MongoClient

# mongoURI = open("mongo.txt","r").read()
# cluster = MongoClient(mongoURI)
# db = cluster["Rina"]
# collection = db["Rina"]
#
# post = {"text": 1, "score": 1}
# collection.insert_one(post)

post = {
        "guild_id":"960962996828516382",
        "joined": {},
        "left": {},
        "verified": {},
        "totalMembers": {},
        "totalVerified": {}
    }
# for y in data[str(itx.guild_id)]:

mongoURI = open("mongo.txt","r").read()
cluster = MongoClient(mongoURI)
RinaDB = cluster["Rina"]
# collection = RinaDB["any"]

# collection.insert_one(post)

# query = {"guild_id": "960962996828516382"}
# guild = collection.find(query)
# print(guild[0])
# collection.update_one(query, {"$set":{"userid232":"timeunix334"}}, upsert=True)
# ['_Cursor__collection', '_Cursor__collname', '_Cursor__data', '_Cursor__dbname',
# '_Cursor__id',]

# for result in user:
#     score = result["score"]
# score = score + 1
# collection.update_one({"guild":1}, {"$set":{"score":score}})

#

#

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

print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] [INFO]: Program started")


def getTableStatus(table):
    status = {
        "msg":{
            "new":"new",
            "open":"join",
            "locked":"lock"
        },
        "label":{
            "new":" Create ",
            "open":" Join ",
            "locked":" Locked "
        }
    }
    msg = status["msg"][ table["status"] ]
    label = status["label"][  table["status"]  ]
    if table["status"] == "locked":
        disabled = True
    else:
        disabled = False
    return disabled,msg,label

def debug():
    return f"{datetime.now().strftime('%H:%M:%S.%f')}] [INFO]:"

def isVerified(itx: discord.Interaction):
    roles = [discord.utils.find(lambda r: r.name == 'Verified', itx.guild.roles)]
    return len(set(roles).intersection(itx.user.roles)) > 0 or isStaff(itx)

# def isVerifier(itx: discord.Interaction):
#     roles = [discord.utils.find(lambda r: r.name == 'Verifier', itx.guild.roles)]
#     return len(set(roles).intersection(itx.user.roles)) > 0 or isAdmin(itx)

def isStaff(itx: discord.Interaction):
    roles = [discord.utils.find(lambda r: r.name == 'Core Staff', itx.guild.roles),
             discord.utils.find(lambda r: r.name == 'Moderator' , itx.guild.roles),
             discord.utils.find(lambda r: r.name == 'Chat Mod'  , itx.guild.roles)]
    return len(set(roles).intersection(itx.user.roles)) > 0 or isAdmin(itx)

def isAdmin(itx: discord.Interaction):
    roles = [discord.utils.find(lambda r: r.name == 'Full Admin', itx.guild.roles),
             discord.utils.find(lambda r: r.name == 'Head Staff', itx.guild.roles),
             discord.utils.find(lambda r: r.name == 'Admin'     , itx.guild.roles)]
    return len(set(roles).intersection(itx.user.roles)) > 0 or itx.user.id == 262913789375021056

# Client events begin

@client.event
async def on_ready():
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] [INFO]: Logged in as {client.user}, in version {version}")
    await client.tree.sync()

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

    await client.process_commands(message)

### Member data storing begins
async def addToData(member, type):
    collection = RinaDB["data"]
    query = {"guild_id": member.guild.id}
    data = collection.find(query)
    try:
        data = data[0]
    except IndexError:
        collection.insert_one(query)
        data = collection.find(query)[0]
    try:
        #see if this user already has data, if so, add a new joining time to the list
        data[type][str(member.id)].append(mktime(datetime.utcnow().timetuple()))
    except IndexError:
        data[type][str(member.id)] = [mktime(datetime.utcnow().timetuple())]
    except KeyError:
        data[type] = {}
        data[type][str(member.id)] = [mktime(datetime.utcnow().timetuple())]
    collection.update_one(query, {"$set":{f"{type}.{member.id}":data[type][str(member.id)]}}, upsert=True)
    # print("Successfully added new data to "+repr(type))

@client.event
async def on_member_join(member):
    await addToData(member,"joined")

@client.event
async def on_member_remove(member):
    await addToData(member,"left")

@client.event
async def on_member_update(before, after):
    role = discord.utils.find(lambda r: r.name == 'Verified', before.guild.roles)
    if role not in before.roles and role in after.roles:
        await addToData(after,"verified")
### Member data storing ends

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
async def updateCmds(itx: discord.Interaction):
    if not isStaff(itx):
        await itx.response.send_message("Only Staff can update the slash commands", ephemeral=True)
        return
    await client.tree.sync()
    await itx.response.send_message(f"Updated slash-commands")

@client.tree.command(name="getmemberdata",description="See joined, left, and recently verified users in x days")
@app_commands.describe(period="Get data from [period] days ago",
                       doubles="If someone joined twice, are they counted double? (y/n or 1/0)")
async def getMemberData(itx: discord.Interaction, period: str, doubles: str = "false"):
    if not isStaff(itx):
        await itx.response.send_message("You don't have the right role to be able to execute this command! (sorrryyy)",ephemeral=True) #todo
        return
    try:
        period = float(period)
        if period <= 0:
            await itx.response.send_message("Your period (data in the past [x] days) has to be above 0!",hidden=True)
            return
    except ValueError:
        await itx.response.send_message("Your period has to be an integer for the amount of days that have passed",hidden=True)
        return

    values = {
        0:["false",'0','n','no','nah','nope','never','nein',"don't"],
        1:['true','1','y','ye','yes','okay','definitely','please']
    }
    for val in values:
        if str(doubles).lower() in values[val]:
            doubles = val
    if doubles not in [0,1]:
        await itx.response.send_message("Your value for Doubles is not a boolean or binary (true/1 or false/0)!",ephemeral=True)
    accuracy = period*2400 #divide graph into 36 sections
    period *= 86400 # days to seconds
    # Get a list of people (in this server) that joined at certain times. Maybe round these to a certain factor (don't overstress the x-axis)
    # These certain times are in a period of "now" and "[period] seconds ago"
    totals = []
    results = {}
    currentTime = mktime(datetime.utcnow().timetuple()) #  todo: globalize the time # maybe fixed with .utcnow() ?
    minTime = int((currentTime-period)/accuracy)*accuracy
    maxTime = int(currentTime/accuracy)*accuracy

    collection = RinaDB["data"]
    query = {"guild_id": itx.guild_id}
    data = collection.find(query)
    try:
        data = data[0]
    except IndexError:
        await itx.response.send_message("Not enough data is configured to do this action! Please hope someone joins sometime soon lol",ephemeral=True)
        return

    for y in data:
        if type(data[y]) is not dict: continue
        column = []
        results[y] = {}
        for member in data[y]:
            for time in data[y][member]:
                #if the current time minus the amount of seconds in every day in the period since now, is still older than more recent joins, append it
                if currentTime-period < time:
                    column.append(time)
                    if doubles == 0:
                        break
        totals.append(len(column))
        for time in range(len(column)):
            column[time] = int(column[time]/accuracy)*accuracy
            if column[time] in results[y]:
                results[y][column[time]] += 1
            else:
                results[y][column[time]] = 1

        #minTime = sorted(column)[0]
        # minTime = int((currentTime-period)/accuracy)*accuracy
        # maxTime = int(currentTime/accuracy)*accuracy
        if len(column) == 0:
            print(f"There were no '{y}' users found for this time period.")
        else:
            timeList = sorted(column)
            if minTime > timeList[0]:
                minTime = timeList[0]
            if maxTime < timeList[-1]:
                maxTime = timeList[-1]
    minTimeDB = minTime
    for y in data:
        if type(data[y]) is not dict: continue
        minTime = minTimeDB
        # print(y)
        # print(data[str(ctx.guild.id)][y])
        while minTime < maxTime:
            if minTime not in results[y]:
                results[y][minTime] = 0
            minTime += accuracy

    result = {}
    for i in results:
        result[i] = {}
        for j in sorted(results[i]):
            result[i][j]=results[i][j]
        results[i] = result[i]

    import matplotlib.pyplot as plt
    import pandas as pd
    try:
        d = {
            "time": [i for i in results["joined"]],
            "joined":[results["joined"][i] for i in results["joined"]],
            "left":[results["left"][i] for i in results["left"]],
            "verified":[results["verified"][i] for i in results["verified"]]
        }
    except KeyError as ex:
        await itx.response.send_message(f"{ex} did not have data, thus could not make the graph.", ephemeral=True)
        return
    df = pd.DataFrame(data=d)
    # print(df)
    fig, (ax1) = plt.subplots(1,1)
    fig.suptitle(f"Member +/-/verif (r/g/b) in the past {period/86400} days")
    fig.tight_layout(pad=1.0)
    ax1.plot(df['time'], df["joined"], 'b')
    ax1.plot(df['time'], df["left"], 'r')
    ax1.plot(df['time'], df["verified"], 'g')
    ax1.set_ylabel("# of players")

    tickLoc = [i for i in df['time'][::3]]
    if period/86400 <= 1:
        tickDisp = [datetime.fromtimestamp(i).strftime('%H:%M') for i in tickLoc]
    else:
        tickDisp = [datetime.fromtimestamp(i).strftime('%Y-%m-%dT%H:%M') for i in tickLoc]

    # plt.xticks(tickLoc, tickDisp, rotation='vertical')
    # plt.setp(tickDisp, rotation=45, horizontalalignment='right')
    ax1.set_xticks(tickLoc,
            labels=tickDisp,
            horizontalalignment = 'right',
            minor=False,
            rotation=30)
    ax1.grid(visible=True, which='major', axis='both')
    fig.subplots_adjust(bottom=0.180, top=0.90, left=0.1, hspace=0.1)
    plt.savefig('userJoins.png')
    await itx.response.send_message(f"In the past {period/86400} days, `{totals[0]}` members joined, `{totals[1]}` left, and `{totals[2]}` were verified. (with{'out'*(1-doubles)} doubles)",file=discord.File('userJoins.png') )

    # print(results)
    # await ctx.send(f"In the past {period/86400} days, `{totals[0]}` members joined, `{totals[1]}` left, and `{totals[2]}` were verified. (with{'out'*(1-doubles)} doubles)",hidden=True)

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

@client.tree.command(name="toneindicator",description="Look for the definition of a tone indicator")
@app_commands.describe(mode="Choose a search method, eg. /p -> platonic; or vice versa",
                       string="This is your search query. What do you want to look for?",
                       public="Do you want to share the search results with the rest of the channel, or keep it hidden")
@app_commands.choices(mode=[
    discord.app_commands.Choice(name='definition', value=1),
    discord.app_commands.Choice(name='exact acronym', value=2),
    discord.app_commands.Choice(name='rough acronym', value=3),
])
async def toneindicator(itx: discord.Interaction, mode: int, string: str, public: bool = False):
    toneIndicators = {
        #
        "excited" : ["/!","/exc"],
        "alterous" : ["/a","/ars"],
        "affectionate" : ["/a","/aff"],
        "an order" : ["/ao"],
        "ask to tag" : ["/att"],
        "a vent" : ["/av"],
        "at you" : ["/ay"],
        "bitter / bitterly" : ["/b"],
        "bragging / flex" : ["/br","/fx"],
        "copypasta" : ["/c","/copy"],
        "calm / calmly" : ["/calm"],
        "clickbait" : ["/cb"],
        "celebratory" : ["/cel"],
        "coping joke" : ["/cj"],
        "comforting" : ["/co","/cf"],
        "concerned" : ["/co"],
        "curious/curiously" : ["/curi"],
        "content warning" : ["/cw"],
        "direct" : ["/dir"],
        "do not comment" : ["/dnc"],
        "do not interract" : ["/dni"],
        "educational" : ["/edu"],
        "exageration" : ["/ex"],
        "fake" : ["/f"],
        "familial (affectionate)" : ["/fam"],
        "fiction / fictional" : ["/fic"],
        "flirting" : ["/fl"],
        "gentle / gently" : ["/gentle"],
        "genuine" : ["/gen","/genq","/g","/gq"],
        "genuine suggestion" : ["/gs","/gens"],
        "half-joking" : ["/hj"],
        "half jokingly overreacting" : ["/hjov"],
        "half serious" : ["/hsrs"],
        "hyperbole" : ["/hyp","/hyb","/hy"],
        "inside joke" : ["/ij"],
        "irrelevant" : ["/irre"],
        "information or informing" : ["/in","/info"],
        "indirect" : ["/ind"],
        "joke / joking" : ["/j"],
        "just kidding" : ["/jk"],
        "jokingly prideful" : ["/jpr"],
        "half jokingly prideful" : ["/hjpr"],
        "joke question" : ["/jq"],
        "jokingly overreacting" : ["/jov"],
        "just wondering" : ["/jw"],
        "keysmash semhsakakeysmamshma" : ["/key"],
        "lyrics" : ["/l","/ly","/lyr"],
        "lying / not (telling) the truth" : ["/lying"],
        "literally" : ["/li"],
        "light-hearted" : ["/lh"],
        "light-hearted sarcasm" : ["/lhs"],
        "a little upset" : ["/lu"],
        "lovingly" : ["/lv"],
        "metaphorically / metaphor" : ["/m"],
        "mad" : ["/m","/mad"],
        "messing around" : ["/ma"],
        "major joke" : ["/mj"],
        "not a brag / flex" : ["/nabr","/nafx"],
        "not an order" : ["/nao"],
        "not a question / statement" : ["/naq","/st","/state"],
        "not a vent" : ["/nav"],
        "not at you" : ["/nay"],
        "for when you're vagueposting or venting, but it's directed at nobody here (none of your followers)" : ["/nbh"],
        "not being rude" : ["/nbr"],
        "nobody specific" : ["/nbs"],
        "nobody you know" : ["/nbyk"],
        "not flirting" : ["/nfl"],
        "negative connotation" : ["/neg","/nc"],
        "neutral connotation" : ["/neu"],
        "not fake" : ["/nf"],
        "not forced to answer" : ["/nfta","/nf"],
        "not flirting" : ["/nfl"],
        "not mad" : ["/nm"],
        "not mad at you, to specify that someone isnt mad at someone else" : ["/nmay"],
        "not passive aggressive" : ["/npa"],
        "not prideful" : ["/npr"],
        "not subtweeting" : ["/nsb", "/nst"],
        "non-sexual intent" : ["/nsx","/nx","/nsxs"],
        "not mad" : ["/nm"],
        "non-serious / not serious" : ["/nsrs"],
        "not a serious question" : ["/nsrsq"],
        "not yelling" : ["/ny"],
        "observation" : ["/ob"],
        "off topic" : ["/ot"],
        "it's okay to ask for reassurance" : ["/otr"],
        "it's okay to laugh" : ["/otl"],
        "it's okay to interract" : ["/oti"],
        "outraged" : ["/outr"],
        "platonic" : ["/p"],
        "passive aggressive" : ["/pa"],
        "playful" : ["/pf"],
        "playfully mad" : ["/pm"],
        "prideful" : ["/pr"],
        "half prideful" : ["/hpr"],
        "passive agressive" : ["/pa"],
        "please interract" : ["/pi"],
        "please laugh" : ["/pl"],
        "paraphrase" : ["/para"],
        "positive connotation" : ["/pos","/pc"],
        "quote" : ["/q"],
        "queerplatonic" : ["/qp"],
        "romantic" : ["/r"],
        "random" : ["/ra"],
        "reference" : ["/ref"],
        "rhetorical question" : ["/rh","/rt","/rtq"],
        "sarcastic / sarcasm / sarcastically" : ["/s","/sarc"],
        "safe" : ["/safe"],
        "for when you're vagueposting or venting, but it's directed at somebody here (x of your followers)" : ["/sbh"],
        "subtweeting" : ["/sbtw"],
        "serious" : ["/srs"],
        "sexual intent" : ["/sx","/x","/xxx"],
        "teasing" : ["/t"],
        "tangent" : ["/tan"],
        "threat" : ["/th"],
        "tic, for when something typed out was unintentional due to being a tic" : ["/tic"],
        "to self" : ["/ts"],
        "trigger warning" : ["/tw"],
        "upset" : ["/u"],
        "unintentional" : ["/unin"],
        "unrelated" : ["/unre"],
        "vague" : ["/v","/vague"],
        "very upset" : ["/vu"],
        "warm / warmth" : ["/w"],
    }

    result = False
    results = []
    resultStr = ""
    if mode == 1:
        for key in toneIndicators:
            if string.replace("-"," ") in key.replace("-"," "):
                overlaps = []
                overlapper = ""
                for key1 in toneIndicators:
                    if key == key1:
                        continue
                    for indicator1 in toneIndicators[key1]:
                        if indicator1 in toneIndicators[key]:
                            overlapper = indicator1
                            overlaps.append(key1)
                            break
                results.append([key,toneIndicators[key],overlapper,overlaps])
                result = True
        if result == True:
            resultStr += f"I found {len(results)} result{'s'*(len(results)>1)} with '{string}' in:\n"
        for x in results:
            y=""
            if len(x[3]) > 0:
                y = f"\n   + {len(x[3])} overlapper{'s'*(len(x[3])>1)}:\n    [ {x[2]}: {', '.join(x[3])} ]"
            resultStr += f"> \"{x[0]}\": {', '.join(x[1])}"+y+"\n"
        # print(" > "+', '.join(toneIndicators[key]))
    elif mode == 2:
        for key in toneIndicators:
            for indicator in toneIndicators[key]:
                if string.replace("/","") == indicator.replace("/",""):
                    results.append([indicator,key])
                    result = True
        if result == True:
            resultStr += f"I found {len(results)} result{'s'*(len(results)>1)}:\n"
        maxLen = 0
        for x in results:
            if len(x[0]) > maxLen:
                maxLen = len(x[0])
        for x in results:
            resultStr += f"> '{x[0]}',{' '*(maxLen-len(x[0]))} meaning {x[1]}\n"
    elif mode == 3:
        for key in toneIndicators: # "lyrics" : ["/l","/ly","/lyr"]
            for indicator in toneIndicators[key]: # ["/l","/ly","/lyr"]
                if len(string.replace("/","")) > len(indicator.replace("/","")):
                    continue
                lastInd = 0
                for strIndex in range(len(string.replace("/",""))): # "/lr" -> "lr" -> "l" "r"
                    res = False
                    for indIndex in range(lastInd,len(indicator)): # "/lyr", "/" "l" "y" "r"
                        if string.replace("/","")[strIndex] == indicator[indIndex]:
                            res = True
                            lastInd = indIndex
                            break
                    if res == False:
                        break
                else:
                    results.append([indicator,key])
                    result = True
        if result == True:
            resultStr += f"I found {len(results)} result{'s'*(len(results)>1)}:\n"
        maxLen = 0
        for x in results:
            if len(x[0]) > maxLen:
                maxLen = len(x[0])
        for x in results:
            resultStr += f"> '{x[0]}',{' '*(maxLen-len(x[0]))} meaning {x[1]}\n"
    if result == False:
        resultStr += f"No information found for '{string}'...\nIf you believe this to be a mistake, message a staff member (ask for Mia)"

    if len(resultStr.split("\n")) > 6:
        public = False
        resultStr += "\nDidn't send your message as public cause it would be spammy, having this many results."
    await itx.response.send_message(resultStr,ephemeral=(public==False))


#
#     1984 is about a dictatorship where you are not allowed \
# to think your own thoughts, and any time you even think differently, the police come for you. \
# Our server is not like this as we give you freedom to think and do as you like, however, this \
# does not mean anarchy. Rules are in place to protect the users and ourselves from certain \
# consequences. **If you would like to know more, please read the book**\n\
# https://www.planetebook.com/1984/")


class Table(app_commands.Group):
    class TableButton(discord.ui.Button):
        async def callback(self, itx: discord.Interaction):
            query = {"guild_id": itx.guild_id}
            collection = RinaDB["tableInfo"]
            tableInfo = collection.find(query)
            try:
                tableInfo = tableInfo[0]
            except IndexError:
                await itx.response.send_message("Not enough data is configured to do this action! Please ask an admin to fix this with `/table admin build`!",ephemeral=True)
                return
            print(debug()+f"Button {self.custom_id} pressed by {itx.user}")
            if itx.message.id == tableInfo["message"]:
                # check if user has a table role
                # if user has no roles:
                #   if table is new, add owner role, open table
                #   if table is open, add member role
                # if user has owner role, say they have to close the table instead of losing their role
                # if user has member role, remove their role
                #   if table is locked, announce it too
                for tableId in tableInfo:
                    if type(tableInfo[tableId]) is not dict: continue
                    table = tableInfo[tableId]
                    for role in itx.user.roles:
                        #if you have a role of this table
                        if self.custom_id == tableId:
                            if role.id == table["owner"]:
                                await itx.response.send_message(f"You can't leave this table because you are the owner. As owner, close table {table['id']} (/table close), or transfer the ownership to someone else (/table newowner <User>).",ephemeral=True)
                                print(f"{itx.user} clicked {self.custom_id} but was already owner of Table {table['id']}")
                                return
                            elif role.id == table["member"]:
                                await itx.user.remove_roles(role,reason="Removed from table role after clicking on button.")
                                # send message in table chat
                                category = discord.utils.find(lambda r: r.id == table["category"], itx.guild.categories)
                                channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
                                await channel.send(f"{itx.user.nick or itx.user.name} ({itx.user.id}) left the table!", allowed_mentions=discord.AllowedMentions.none())
                                # send message to clicker
                                await itx.response.send_message(f"Successfully removed you from table {table['id']}",ephemeral=True)
                                print(f"{itx.user} clicked {self.custom_id} and left Table {table['id']} because they were a member")
                                return
                        #if you already have another table's role
                        if role.id == table["owner"] or role.id == table["member"]:
                            await itx.response.send_message(f"You can currently only join one table at a time. Leave Table {table['id']} first before you can join another!",ephemeral=True)
                            print(f"{itx.user} clicked {self.custom_id} but were already in Table {table['id']}, so weren't given a role")
                            return #todo; let them join multiple tables
                # doesn't have the role yet
                table, tableId = [tableInfo[self.custom_id], self.custom_id]
                if table["status"] == "new":
                    # give Member the table owner role; open table
                    # tableInfo[tableId]["status"] = "open"
                    collection.update_one(query, {"$set":{f"{tableId}.status":"open"}}, upsert=True)
                    await Table.tablemsgupdate(Table, itx)
                    role = discord.utils.find(lambda r: r.id == table["owner"], itx.guild.roles)
                    await itx.user.add_roles(role)
                    # send message in table chat
                    category = discord.utils.find(lambda r: r.id == table["category"], itx.guild.categories)
                    channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
                    await channel.send(f"This table was opened by {itx.user.nick or itx.user.name} ({itx.user.id}).", allowed_mentions=discord.AllowedMentions.none())
                    await channel.send(f"{itx.user.nick or itx.user.name} ({itx.user.id}) joined the table as Table Owner", allowed_mentions=discord.AllowedMentions.none())
                    # send message to clicker
                    await itx.response.send_message(f"Successfully created and joined table {table['id']}",ephemeral=True)
                    print(f"{itx.user} clicked {self.custom_id} so Table {table['id']} was created and the clicker was given the owner role")
                    return
                elif table["status"] == "open":
                    # give Member the table member role
                    role = discord.utils.find(lambda r: r.id == table["member"], itx.guild.roles)
                    await itx.user.add_roles(role)
                    # send message in table chat
                    category = discord.utils.find(lambda r: r.id == table["category"], itx.guild.categories)
                    channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
                    await channel.send(f"{itx.user.nick or itx.user.name} ({itx.user.id}) joined the table!", allowed_mentions=discord.AllowedMentions.none())
                    # send message to clicker
                    await itx.response.send_message(f"Successfully joined table {table['id']}",ephemeral=True)
                    print(f"{itx.user} clicked {self.custom_id} and were added as member to Table {table['id']}.")
                    return
                else:
                    await itx.response.send_message("I don't know how you did it.. But you can't join a locked table!",ephemeral=True)
                    print(f"{itx.user} tried to join a locked table (Table {table['id']}).. somehow?")
                    return
            print("It didn't make it through or something :(")

    async def tablemsg(self, itx: discord.Interaction,channel=None):
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find(query)
        try:
            tableInfo = tableInfo[0]
        except IndexError:
            await itx.response.send_message("Not enough data is configured to do this action! Please ask an admin to fix this with `/table admin build`!",ephemeral=True)
            return
        embed1 = discord.Embed(color=8481900, type='rich',description=" ")
        embed2 = discord.Embed(color=8481900, type='rich', title='Join a Table!',
            description="Click one of the buttons below to create or join a table!~")
        embed1.set_image(url="https://i.imgur.com/SBy90SG.png")
        embed2.set_image(url="https://i.imgur.com/t3zhm4k.png") # i feel like this doesn't do anything..

        components = [{  "type": 1,"components":[]  }]
        view = discord.ui.View()
        for x in tableInfo:
            x = tableInfo[x] #todo todo todo
            try:
                disabled,status,label = getTableStatus(x)
            except TypeError:
                continue
            embed2.add_field(name=f'{x["emoji"]} Table {x["id"]} ({status})',value=f'<@&{x["member"]}>')
            view.add_item(self.TableButton(label=f'{label} {x["id"]}', disabled=disabled,
                        custom_id="table"+x["id"], emoji=discord.PartialEmoji.from_str(x["emoji"])))
            # button = discord.ui.Button(style=discord.ButtonStyle.secondary, label=f'{label} {x["id"]}',
            #             disabled=disabled, custom_id="table"+x["id"], emoji=discord.PartialEmoji.from_str(x["emoji"]))
            # view.add_item(button)

        if channel:
            itx.channel_id, itx.channel.id = [channel.id,channel.id]
        warning = ""
        if "message" in tableInfo:
            print(f"I am looking for {tableInfo['message']}, most likely in {tableInfo['msgChannel']}")
            # await itx.response.defer(ephemeral=True)
            try:
                c = itx.guild.text_channels[0]
                c.id = tableInfo["msgChannel"]
                msg = await c.fetch_message(tableInfo["message"])
                await msg.delete()
            except:
                warning = "Couldn't find a message to delete...\n"

        msg = await itx.channel.send(embeds=[embed1,embed2],view=view)#,components=components)

        collection.update_one(query, {"$set":{
            "msgChannel": msg.channel.id,
            "message"   : msg.id}}, upsert=True)
        await itx.response.send_message(warning+"Sent message successfully.",ephemeral=True)

    async def tablemsgupdate(self, itx: discord.Interaction):
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find(query)
        try:
            tableInfo = tableInfo[0]
        except IndexError:
            await itx.response.send_message("Not enough data is configured to do this action! Please ask an admin to fix this with `/table admin build`!",ephemeral=True)
            return

        embed1 = discord.Embed(color=8481900, type='rich',description=" ")
        embed2 = discord.Embed(color=8481900, type='rich', title='Join a Table!',
            description="Click one of the buttons below to create or join a table!~")
        embed1.set_image(url="https://i.imgur.com/SBy90SG.png")
        embed2.set_image(url="https://i.imgur.com/t3zhm4k.png") # i feel like this doesn't do anything..
        view = discord.ui.View()
        components = [{  "type": 1,"components":[]  }]
        for x in tableInfo:
            x = tableInfo[x]
            try:
                disabled,status,label = getTableStatus(x)
            except TypeError:
                continue
            embed2.add_field(name=f'{x["emoji"]} Table {x["id"]} ({status})',value=f'<@&{x["member"]}>')
            view.add_item(self.TableButton(label=f'{label} {x["id"]}', disabled=disabled,
                        custom_id="table"+x["id"], emoji=discord.PartialEmoji.from_str(x["emoji"])))

        if "message" not in tableInfo:
            print("Couldn't find message in tableInfo")
            return False
        c = await client.fetch_channel(tableInfo["msgChannel"])
        msg = await c.fetch_message(tableInfo["message"])
        await msg.edit(embeds=[embed1,embed2],view=view)


    admin = app_commands.Group(name='admin', description='Edit a table system')

    @admin.command(name="sendmsg",description="Send initial table object message. developmental purposes only")
    @app_commands.describe(channel="Which channel do you want to send the message in?")
    async def tablemsgsend(self,itx: discord.Interaction, channel: discord.TextChannel = None):
        if not isAdmin(itx):
            await itx.response.send_message("You do not have permission to send this message (staff-only)",ephemeral=True)
            return
        await self.tablemsg(itx,channel)

    @admin.command(name="list",description="Get a list of tables in the table system")
    async def list(self,itx: discord.Interaction):
        if not isAdmin(itx):
            await itx.response.send_message("You do not have permission to add a new table",ephemeral=True)
            return

        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find(query)
        try:
            tableInfo = tableInfo[0]
        except IndexError:
            await itx.response.send_message("Not enough data is configured to do this action! Please ask an admin to fix this with `/table admin build`!",ephemeral=True)
            return
        tables = "List of tables:"
        for tableId in tableInfo:
            table = tableInfo[tableId]
            if type(table) is not dict:continue
            tables+=f"\nTable `{table['id']}`, Category:<#{table['category']}>, Owner: <@&{table['owner']}>, Member: <@&{table['member']}>, Emoji: {table['emoji']}, Status: {table['status']}"
        await itx.response.send_message(tables, allowed_mentions=discord.AllowedMentions.none())

    @admin.command(name="build",description="Link a new table to the table system")
    @app_commands.describe(id="Give the table a number: \"1\" for \"Table 1\", eg.",
                           category="Mention the table category",
                           owner="Ping/mention the table owner role",
                           member="Ping/mention the table (member) role",
                           emoji="Type the emoji (circle) for the table")
    async def build(self, itx: discord.Interaction, id: str, category: discord.CategoryChannel, owner: discord.Role, member: discord.Role, emoji: str):
        if not isAdmin(itx):
            await itx.response.send_message("You do not have permission to add a new table",ephemeral=True)
            return

        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find(query)
        try:
            tableInfo = tableInfo[0]
        except IndexError:
            collection.insert_one(query)
            tableInfo = collection.find(query)[0]

        warning = ""
        for table in tableInfo:
            if type(tableInfo[table]) is not dict: continue
            if id == tableInfo[table]["id"]:
                await itx.response.send_message("There is already a table with this ID. You can't add two tables with the same id.\nThat would make it difficult to link buttons and remove the table in the future :/.",ephemeral=True,allowed_mentions=discord.AllowedMentions.none())
                return
        for tableId in tableInfo:
            table = tableInfo[tableId]
            if type(table) is not dict: continue
            if category.id == table["category"]:
                warning += f"Warning: You already registered this category in table {table['id']}!\n"
            if owner.id == table["owner"]:
                warning += f"Warning: You already registered this owner role in table {table['id']}!\n"
            if member.id == table["member"]:
                warning += f"Warning: You already registered this member role in table {table['id']}!\n"
            if emoji == table["emoji"]:
                warning += f"Warning: You already registered this emoji in table {table['id']}!\n"

        tableData = {
            "id":id,
            "category":category.id,
            "owner":owner.id,
            "member":member.id,
            "emoji":emoji,
            "status":"new",
        }
        collection.update_one(query, {"$set":{"table"+id : tableData}}, upsert=True)
        await self.tablemsgupdate(itx)
        await itx.response.send_message(warning+f"┬─┬ ノ( ゜-゜ノ) Created `Table {id}` with category:<#{category.id}>, owner:<@&{owner.id}>, member:<@&{member.id}>, emoji:{emoji}",allowed_mentions=discord.AllowedMentions.none())

    @admin.command(name="force_close",description="Force close a table, so a new group can start.")
    @app_commands.describe(id="Give the table number: \"1\" for \"Table 1\", eg.")
    async def tableForceClose(self, itx: discord.Interaction, id: str):
        if not isAdmin(itx):
            await itx.response.send_message("You do not have permission to forcibly close a table",ephemeral=True)
            return
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find(query)
        try:
            tableInfo = tableInfo[0]
        except IndexError:
            await itx.response.send_message("Not enough data is configured to do this action! Please ask an admin to fix this with `/table admin build`!",ephemeral=True)
            return

        closable = ""
        if not "message" in tableInfo:
            await itx.response.send_message("There is no table message to update, thus I'm afraid you can't close the table.. Pleaes ask an admin to fix this with `/table admin sendmsg`",ephemeral=True)
            return
        for table in tableInfo:
            if type(tableInfo[table]) is not dict: continue
            if tableInfo[table]["id"] == id:
                closable = table
                break
        if closable == "":
            await itx.response.send_message("This id wasn't valid, thus couldn't close this table (for a list of tables, use /table admin list)!",ephemeral=True)
            return
        warning = ""
        if tableInfo[closable]["status"] == "new":
            warning += "This table is already closed... Closing anyway, I guess.\n"
        # remove every member and the owner from the table
        removedPeople = []
        ownerRole = discord.utils.find(lambda r: r.id == tableInfo[closable]["owner"], itx.guild.roles)
        for member in ownerRole.members:
            await member.remove_roles(ownerRole)
            removedPeople.append(f"{member.name or member.nick} ({member.id})")
        try:
            memberRole = discord.utils.find(lambda r: r.id == tableInfo[closable]["member"], itx.guild.roles)
            for member in memberRole.members:
                await member.remove_roles(memberRole)
                removedPeople.append(f"{member.name or member.nick} ({member.id})")
        except TypeError:
            print(f"Tried to remove all members from table {tableInfo[closable]['id']}, but there were none maybe?")

        collection.update_one(query, {"$set":{f"{closable}.status":"new"}}, upsert=True)
        # tableInfo[closable]["status"] = "new"
        # send update message in table chat
        category = discord.utils.find(lambda r: r.id == tableInfo[closable]["category"], itx.guild.categories)
        channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
        await channel.send(f"Removed users from table: {', '.join(removedPeople)}\nThis table was forcibly closed by a staff member. A new table can be created now.")
        await self.tablemsgupdate(itx)
        await itx.response.send_message(warning+"Closed successfully",ephemeral=True)

    @admin.command(name="destroy",description="Remove a table from the table system")
    @app_commands.describe(id="Give the table a number: \"1\" for \"Table 1\", eg.")
    async def destroy(self, itx: discord.Interaction, id: str):
        if not isStaff(itx):
            await itx.response.send_message("You do not have permission to delete a table",ephemeral=True)
            return

        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find(query)
        try:
            tableInfo = tableInfo[0]
        except IndexError:
            await itx.response.send_message("Not enough data is configured to do this action! Please ask an admin to fix this with `/table admin build`!",ephemeral=True)
            return

        for tableId in tableInfo:
            try:
                if tableInfo[tableId]["id"] == id:
                    collection.update_one(query, {"$unset":{f"{tableId}":""}}, upsert=True)
                    await itx.response.send_message(f"(╯°□°）╯︵ ┻━┻ Destroyed table {id} successfully. Happy now? ")
                    await self.tablemsgupdate(itx)
                    return
            except TypeError: #probably the message/channel info
                pass
        await itx.response.send_message(f"Finished command without any action, thus the id was likely incorrect",ephemeral=True)

    @app_commands.command(name="lock",description="Lock your table, so no new players can join.")
    async def tableLock(self, itx: discord.Interaction):
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find(query)
        try:
            tableInfo = tableInfo[0]
        except IndexError:
            await itx.response.send_message("Not enough data is configured to do this action! Please ask an admin to fix this with `/table admin build`!",ephemeral=True)
            return
        lockable = ""
        if not "message" in tableInfo:
            await itx.response.send_message("There is no table message to update, thus I'm afraid you can't lock your table..",ephemeral=True)
            return
        for table in tableInfo:
            if type(tableInfo[table]) is not dict: continue
            for role in itx.user.roles:
                if role.id == tableInfo[table]["owner"]:
                    lockable = table
            if lockable:
                break
        if lockable == "":
            await itx.response.send_message("You aren't a table owner, thus can't lock this table!",ephemeral=True)
            await self.tablemsgupdate(itx)
            return
        collection.update_one(query, {"$set":{f"{lockable}.status":"locked"}}, upsert=True)

        # send update message in table chat
        category = discord.utils.find(lambda r: r.id == tableInfo[lockable]["category"], itx.guild.categories)
        channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
        await channel.send("This table was locked by the table owner. No new players can join the table anymore.\nUse `/table unlock` as table owner to open the table again.")
        await self.tablemsgupdate(itx)
        await itx.response.send_message("Locked successfully",ephemeral=True)

    @app_commands.command(name="unlock",description="Unlock your table, so new players can join again.")
    async def tableUnlock(self, itx: discord.Interaction):
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find(query)
        try:
            tableInfo = tableInfo[0]
        except IndexError:
            await itx.response.send_message("Not enough data is configured to do this action! Please ask an admin to fix this with `/table admin build`!",ephemeral=True)
            return
        unlockable = ""
        if not "message" in tableInfo:
            await itx.response.send_message("There is no table message to update, thus I'm afraid you can't lock your table..",ephemeral=True)
            return
        for table in tableInfo:
            if type(tableInfo[table]) is not dict: continue
            for role in itx.user.roles:
                if role.id == tableInfo[table]["owner"]:
                    unlockable = table
            if unlockable:
                break
        if unlockable == "":
            await itx.response.send_message("You aren't a table owner, thus can't unlock this table!",ephemeral=True)
            return

        collection.update_one(query, {"$set":{f"{unlockable}.status":"open"}}, upsert=True)

        # send update message in table chat
        category = discord.utils.find(lambda r: r.id == tableInfo[unlockable]["category"], itx.guild.categories)
        channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
        await channel.send("This table was unlocked by the table owner. Players can join the table again.\nUse `/table lock` as table owner to lock the table.")
        await self.tablemsgupdate(itx)
        await itx.response.send_message("Unlocked successfully",ephemeral=True)

    @app_commands.command(name="close",description="Close your table, a new group can start.")
    async def tableClose(self, itx: discord.Interaction):
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find(query)
        try:
            tableInfo = tableInfo[0]
        except IndexError:
            await itx.response.send_message("Not enough data is configured to do this action! Please ask an admin to fix this with `/table admin build`!",ephemeral=True)
            return
        closable = ""
        if not "message" in tableInfo:
            await itx.response.send_message("There is no table message to update, thus I'm afraid you can't close your table..",ephemeral=True)
            return
        for table in tableInfo:
            if type(tableInfo[table]) is not dict: continue
            for role in itx.user.roles:
                if role.id == tableInfo[table]["owner"]:
                    closable = table
            if closable:
                break
        if closable == "":
            await itx.response.send_message("You aren't a table owner, thus can't close this table!",ephemeral=True)
            return
        # remove every member and the owner from the table
        removedPeople = []
        ownerRole = discord.utils.find(lambda r: r.id == tableInfo[closable]["owner"], itx.guild.roles)
        for member in ownerRole.members:
            await member.remove_roles(ownerRole)
            removedPeople.append(f"{member.name or member.nick} ({member.id})")
        try:
            memberRole = discord.utils.find(lambda r: r.id == tableInfo[closable]["member"], itx.guild.roles)
            for member in memberRole.members:
                await member.remove_roles(memberRole)
                removedPeople.append(f"{member.name or member.nick} ({member.id})")
        except TypeError:
            print(f"Tried to remove all members from table {tableInfo[closable]['id']}, but there were none maybe?")

        collection.update_one(query, {"$set":{f"{closable}.status":"new"}}, upsert=True)
        # send update message in table chat
        category = discord.utils.find(lambda r: r.id == tableInfo[closable]["category"], itx.guild.categories)
        channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
        await channel.send(f"Removed users from table: {', '.join(removedPeople)}\nThis table was closed by the table owner. A new table can be created now.")
        await self.tablemsgupdate(itx)
        await itx.response.send_message("Closed successfully",ephemeral=True)

    @app_commands.command(name="newowner",description="Transfer your ownership, in case you'd want someone else to have it instead.")
    @app_commands.describe(user="Mention the user who you want to become the new owner.")
    async def tableNewOwner(self, itx: discord.Interaction, user: discord.Member):
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find(query)
        try:
            tableInfo = tableInfo[0]
        except IndexError:
            await itx.response.send_message("Not enough data is configured to do this action! Please ask an admin to fix this with `/table admin build`!",ephemeral=True)
            return
        transfer = ""
        for table in tableInfo:
            if type(tableInfo[table]) is not dict: continue
            for role in itx.user.roles:
                if role.id == tableInfo[table]["owner"]:
                    transfer = table
            if transfer:
                break
        if transfer == "":
            await itx.response.send_message("You aren't a table owner, thus can't transfer your ownership of this table!",ephemeral=True)
            return
        if discord.utils.find(lambda r: r.id == tableInfo[transfer]["member"], user.roles) is None:
            await itx.response.send_message("To grant someone ownership, they must have joined the table first (have table member role)!",ephemeral=True)
            return
        # change owner roles
        ownerRole = discord.utils.find(lambda r: r.id == tableInfo[transfer]["owner"], itx.guild.roles)
        memberRole = discord.utils.find(lambda r: r.id == tableInfo[transfer]["member"], itx.guild.roles)
        for member in ownerRole.members:
            await member.add_roles(memberRole)
            await member.remove_roles(ownerRole)
        await user.add_roles(ownerRole)
        await user.remove_roles(memberRole)

        # send update message in table chat
        category = discord.utils.find(lambda r: r.id == tableInfo[transfer]["category"], itx.guild.categories)
        channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
        await channel.send(f"This table's ownership was transferred from {itx.user.nick or itx.user.name} ({itx.user.id}) to {user.nick or user.name} ({user.id}).",allowed_mentions=discord.AllowedMentions.none())
        await itx.response.send_message(f"Ownership transferred successfully", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)

client.tree.add_command(Table())

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

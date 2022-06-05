# dumb code for cool version updates
path = "" # dunno if i should delete this. Could be used if your files are not in the same folder as this program.
fileVersion = "0.1.11" .split(".")
version = open(path+"version.txt","r").read().split(".")
# version =     "0.1.10.2"
for v in range(len(fileVersion)):
    if int(fileVersion[v]) > int(version[v]):
        version = fileVersion + ["0"]
        break
else:
    version[-1] = str(  int( version[-1] )+1  )
version = '.'.join(version)
open(path+"version.txt","w").write(f"{version}")

import discord # It's dangerous to go alone! Take this. /ref
from discord.ext import commands # required for client bot making
from discord_slash import SlashCommand, SlashContext # required for making slash commands
#from discord_slash.utils.manage_commands import create_permission # limit commands to roles/users
#from discord_slash.model import SlashCommandPermissionType # limit commands to roles/users
from discord_slash.utils.manage_commands import create_option, create_choice # set command argument limitations (string/int/bool)
from discord_slash.context import ComponentContext # button responses

#from discord.utils import get #dunno what this is for tbh.
import json #json used for settings file
import pickle # pickle used for reactionmsgs file
import signal # save files when receiving KeyboardInterrupt
import sys # exit program after Keyboardinterrupt signal is noticed

import asyncio # used for asyncio.sleep() for debugging purposes (temporary, or at least, it should be- when i wrote this)

from datetime import datetime, timedelta
from time import mktime #for unix time code
import random #for very uncute responses

# Dependencies:
#   server members intent, message content intent,
#   permissions:
#       send messages
#       read messages
#       remove reactions on a message
#       create and delete voice channels
#       move users between voice channels
#       manage roles (for adding/removing table roles)

intents = discord.Intents.default()
intents.members = True #apparently this needs to be additionally defined cause it's not included in Intents.default()?
#setup default discord bot client settings, permissions, slash commands, and file paths
client =  commands.Bot(intents = intents
, command_prefix=commands.when_mentioned_or("/"), case_insensitive=True
, activity = discord.Game(name="with slash (/) commands!"),
allowed_mentions = discord.AllowedMentions(everyone = False))

slash = SlashCommand(client, sync_commands=True)
guild_ids = [960962996828516382]

#default defining before settings
settings = {}
data = {
# see example of the current data format below
# data = {
#   959551566388547676:{    # TransPlace
#     "joined":{
#        262913789375021056: [1653495322, 1653496268]
#        # MysticMia#7612   =  [joinTime1, joinTime2] #if they join twice
#     },
#     "left":{},
#       etc.
#   }
# }
}
dataTemplate = {
    "joined"       :{    },
    "left"         :{    },
    "verified"     :{    },
    "totalMembers" :{    }, #todo
    "totalVerified":{    }}
reactionmsgs = {}
newVcs = {} # make your own vcs!
tableInfo = { # join or create/host a table!
    # "table1":{
        # new: create new channel
        # open: can be joined. If it's open, will show up as "join"
        # locked: cannot be joined, has been locked by table owner
    # },
    # "message":""
}
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

print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] [INFO]: Program started")

@client.event
async def on_ready():
    global data, tableInfo, reactionmsgs
    #load the data file.
    fileId = 0
    if len(data) == 0:
        data = json.loads(open(path+"data.json","r").read())
        fileId += 1
    if len(tableInfo) == 0:
        tableInfo = json.loads(open(path+"tableInfo.json","r").read())
        fileId += 2
    if len(reactionmsgs) == 0:
        reactionmsgs = pickle.loads(open('reactionmsgs.txt', 'rb').read())
        fileId += 4
    print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] [INFO]: Files loaded ({fileId}/7) and logged in as {client.user}, in version {version}")

def debug():
    return f"{datetime.now().strftime('%H:%M:%S.%f')}] [INFO]:"

@client.event
async def on_message(message):
    if message.author.bot:
        return
    # random cool commands
    if message.content.startswith(":say "):
        await message.channel.send(message.content.split(" ",1)[1].replace("[[del]]",""))
        return
    if ("1984" in message.content or "nineteeneightyfour" in message.content.lower().replace(" ","").replace("-","")) and "@" not in message.content:
        await message.reply(content="1984 is about a dictatorship where you are not allowed \
to think your own thoughts, and any time you even think differently, the police come for you. \
Our server is not like this as we give you freedom to think and do as you like, however, this \
does not mean anarchy. Rules are in place to protect the users and ourselves from certain \
consequences. **If you would like to know more, please read the book**\n\
https://www.planetebook.com/1984/")
    if client.user.mention in message.content.split():
        if ("not" in message.content or "uncute" in message.content) and "not uncute" not in message.content:
            await message.add_reaction("<:this:960916817801535528>")
        elif "cutie" in message.content or "cute" in message.content:
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
    return

async def addToData(member, type):
    global data
    try:
        data[str(member.guild.id)]
    except:
        if len(data) == 0:
            #await ctx.send("Won't continue the event because the file is too short! Something probably went wrong when loading the file.\nChanging a setting now will overwrite and clear it (try again in a few seconds)")
            print("Did not set default settings because the dictionary is 0, so prevented overloading and loss of data")
            return
        data[str(member.guild.id)] = dataTemplate
    try:
        #see if this user already has data, if so, add a new joining time to the list
        data[str(member.guild.id)][type][str(member.id)].append(mktime(datetime.now().timetuple()))
    except:
        data[str(member.guild.id)][type][str(member.id)] = [mktime(datetime.now().timetuple())] #todo: make unlocalized, rather UTC time
    print("Successfully added new data to "+repr(type))

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

@client.event
async def on_raw_reaction_add(reaction):
    global settings, reactionmsgs
    #get the message id from reaction.message_id through the channel (with reaction.channel_id) (oof lengthy process)
    message = await client.get_channel(reaction.channel_id).fetch_message(reaction.message_id)
    if message.author == client.user:
        if reaction.emoji.name == '❌' and reaction.member != client.user:
            await message.delete()

    if message.author == client.user:
        if reaction.member != client.user and str(message.id) in reactionmsgs:
            voteMsg = reactionmsgs[str(message.id)]
            try:
                voteMsg.vote(reaction.member.id, reaction.emoji.name)
                message.id = voteMsg.message_id
                await message.edit(content=voteMsg.getMessage())
            except:pass
            await message.remove_reaction(reaction.emoji.name, reaction.member)

@client.event
async def on_voice_state_update(member, before, after):
    global newVcs
    if after.channel is not None:
        if after.channel.id == 981557586723758091:
            after.channel.category.id = 981558003822108733
            cmdChannel = discord.utils.find(lambda r: r.name == 'no-mic', after.channel.category.text_channels)
            defaultName = "Untitled voice chat"
            vc = await after.channel.category.create_voice_channel(defaultName)
            await member.move_to(vc,reason=f"Opened a new voice channel through the vc hub thing.")
            await cmdChannel.send(content=f"You have joined <#{vc.id}>, <@{member.id}>. Use `/renamevc <name>` to rename your voice channel! (follow the rules)",delete_after=32)
    if before.channel is None:
        print(debug()+f"{member} joined a (new) voice channel but wasn't in one before")
        return
    if before.channel in before.channel.guild.voice_channels:
        if before.channel.category.id not in [981558003822108733]:
            print(debug()+"some user left a voice channel that wasn't in the 'deleting vcs' category, u know")
            return
        if after.channel in before.channel.guild.voice_channels:
            print(debug()+f"{member} left vc / joined to another voice channel")
        if before.channel.id == 981557586723758091: # avoid deleting the hub channel
            print(debug()+f"{member} left the vc hub thing")
            return
        if len(before.channel.members) == 0:
            # try:
            cmdChannel = discord.utils.find(lambda r: r.name == 'no-mic', before.channel.category.text_channels)
            def pingSafe(str):
                return str.replace("@everyone","@ everyone").replace("@here","@ here").replace('`','\`').replace('@','\@').replace('>','\>')
            await cmdChannel.send(f"{pingSafe(member.nick or member.name)} left voice channel \"{pingSafe(before.channel.name)}\", and was the last one in it, so it was deleted.",delete_after=32, allowed_mentions = discord.AllowedMentions.none())
            await before.channel.delete()
            print(repr(newVcs)+"\n\n"+str(before.channel.id))
            try:
                del newVcs[before.channel.id]
            except:
                pass #haven't edit the channel yet
            # except Exception as ex:
            #     print(debug()+f"Tried to remove channel but couldn't",ex.message, ex)
            #     raise ex
        else:
            print(debug()+f"{member} left voice channel, but it wasn't empty yet, so it wasn't deleted.")

@client.event
async def on_interaction(ctx,interaction):
    print(repr(interaction))
    await interaction.respond(content="Button Clicked")

@client.event
async def on_component(ctx: ComponentContext):
    global tableInfo
    if len(tableInfo) == 0:
        await ctx.send("Couldn't find table data. Please wait 1 second.",hidden=True)
        return

    if ctx.origin_message_id == tableInfo["message"]:
        # check if user has a table role
        # if user has no roles:
        #   if table is new, add owner role, open table
        #   if table is open, add member role
        # if user has owner role, say they have to close the table instead of losing their role
        # if user has member role, remove their role
        #   if table is locked, announce it too
        for tableId in tableInfo:
            if type(tableInfo[tableId]) is int:
                continue # probably message/channel id thing
            table = tableInfo[tableId]
            for role in ctx.author.roles:
                if ctx.custom_id == tableId:
                    if role.id == table["owner"]:
                        await ctx.send(f"You can't leave this table because you are the owner. As owner, close table {table['id']} (/table close), or transfer the ownership to someone else (/table newowner <User>).",hidden=True)
                        return
                    elif role.id == table["member"]:
                        await ctx.author.remove_roles(role,reason="Removed from table role after clicking on button.")
                        await ctx.send(f"Successfully removed you from table {table['id']}",hidden=True)
                        # send message in table chat
                        category = discord.utils.find(lambda r: r.id == table["category"], ctx.guild.categories)
                        channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
                        await channel.send(f"{ctx.author.nick or ctx.author.name} ({ctx.author.id}) left the table!", allowed_mentions=discord.AllowedMentions.none())

                        return
                elif role.id == table["owner"] or role.id == table["member"]:
                    #if you already have a table role
                    await ctx.send(f"You can currently only join one table at a time. Leave table {table['id']} first before you can join another!",hidden=True)
                    return #todo; let them join multiple tables
            # doesn't have the role yet
            if ctx.custom_id == tableId:
                if table["status"] == "new":
                    # give Member the table role; open table
                    role = discord.utils.find(lambda r: r.id == table["owner"], ctx.guild.roles)
                    print(f"Creating table {table['id']} and adding {ctx.author} to it.")
                    await ctx.author.add_roles(role)
                    await ctx.send(f"Successfully created and joined table {table['id']}",hidden=True)
                    tableInfo[tableId]["status"] = "join"
                    # send message in table chat
                    category = discord.utils.find(lambda r: r.id == table["category"], ctx.guild.categories)
                    channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
                    await channel.send(f"This table was opened by {ctx.author.nick or ctx.author.name} ({ctx.author.id}).", allowed_mentions=discord.AllowedMentions.none())
                    await channel.send(f"{ctx.author.nick or ctx.author.name} ({ctx.author.id}) joined the table as Table Owner", allowed_mentions=discord.AllowedMentions.none())
                    return
                elif table["status"] == "open":
                    role = discord.utils.find(lambda r: r.id == table["member"], ctx.guild.roles)
                    print(f"Adding {ctx.author} to table {table['id']}.")
                    await ctx.author.add_roles(role)
                    await ctx.send(f"Successfully joined table {table['id']}",hidden=True)
                    # send message in table chat
                    category = discord.utils.find(lambda r: r.id == table["category"], ctx.guild.categories)
                    channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
                    await channel.send(f"{ctx.author.nick or ctx.author.name} ({ctx.author.id}) joined the table!", allowed_mentions=discord.AllowedMentions.none())
                    return
                else:
                    print(f"{ctx.author} tried to join a locked table (Table {table['id']}).. somehow?")
                    await ctx.send("I don't know how you did it.. But you can't join a locked table!",hidden=True)
                    return
        else:
            print("huh nothing happened..")

    print("on_component event")

# @slash.component_callback()
# async def buttonEvent(ctx: ComponentContext):
#     print("component_callback")

class AnonymousVote:
    def __init__(self, question):
        self.question = question
        self.upvotes = []
        self.downvotes = []
        self.message_id = 0

    def vote(self, member_id, voteEmoji):
        # if you voted for the other option already, move your vote to new option, else ignore
        if voteEmoji == '🔺':
            if member_id in self.upvotes:
                return
            if member_id in self.downvotes:
                self.downvotes.remove(member_id)
            self.upvotes.append(member_id)
        elif voteEmoji == '🔻':
            if member_id in self.downvotes:
                return
            if member_id in self.upvotes:
                self.upvotes.remove(member_id)
            self.downvotes.append(member_id)
        else:
            raise ValueError("This emoji can't be used to vote!")

    def getMessage(self):
        return self.question+f"\n`{len(self.upvotes)}` upvotes 🔺  and `{len(self.downvotes)}` downvotes 🔻"

@slash.slash(name="anonymousvote",
            description="Create a 2-choiced poll that people can react to, and will update msg to keep it anonymous",
            options=[
                create_option(
                    name="question",
                    description="Poll question to which people can upvote/downvote",
                    option_type=3,
                    required=True)])
async def anonymousVote(ctx,question):
    global reactionmsgs
    # if len(reactionmsgs) == 0:
    #     await ctx.send("Won't continue the event because the file is too short! Something probably went wrong when loading the file.\nChanging the tracking file now will overwrite and clear its contents (try again in a few seconds)")
    #     print("Interrupted event because the dictionary is 0, so prevented overloading and loss of data")
    #     return
    voteMsg = AnonymousVote(question)
    msg = await ctx.send(voteMsg.getMessage())
    voteMsg.message_id = msg.id
    await msg.add_reaction("🔺")
    await msg.add_reaction("🔻")
    reactionmsgs[str(msg.id)] = voteMsg

@slash.slash(name="version", description="Get bot version")
async def botVersion(ctx):
    await ctx.send(f"Bot is currently running on v{version}")

# slash command format: https://dpyslash.readthedocs.io/en/latest/gettingstarted.html
@slash.slash(name="getdata",
            description="See joined, left, and recently verified users in x days",
            options=[
                create_option(
                    name="period",
                    description="Get data from [period] days ago",
                    option_type=3,
                    required=True),
                create_option(
                    name="doubles",
                    description="If someone joined twice, are they counted double? (y/n or 1/0)",
                    option_type=3,
                    required=False)
            ])
async def getData(ctx,period, doubles="false"):
    modRoles = [
        discord.utils.find(lambda r: r.name == 'Test Admin', ctx.guild.roles),
        discord.utils.find(lambda r: r.name == 'Head Staff', ctx.guild.roles),
        discord.utils.find(lambda r: r.name == 'Core Staff', ctx.guild.roles),
        discord.utils.find(lambda r: r.name == 'Chat Mod'  , ctx.guild.roles),
        discord.utils.find(lambda r: r.name == 'Verifier'  , ctx.guild.roles)]
        # there's gotta be a better way to do this..
    # new method for multiple roles /\, old method for single role \/
    # role = discord.utils.find(lambda r: r.name == 'Verifier', ctx.guild.roles)
    # if role in ctx.author.roles:
    if len(set(modRoles).intersection(ctx.author.roles)) > 0:
        try:
            period = float(period)
            if period <= 0:
                await ctx.send("Your period (data in the past [x] days) has to be above 0!",hidden=True)
                return
        except:
            await ctx.send("Your period has to be an integer for the amount of days that have passed",hidden=True)
            return
        values = {
            0:["false",'0','n','no','nah','nope','never','nein',"don't"],
            1:['true','1','y','ye','yes','okay','definitely','please']
        }
        for val in values:
            if str(doubles).lower() in values[val]:
                doubles = val
        if not doubles in [0,1]:
            await ctx.send("Your value for Doubles is not a boolean or binary (true/1 or false/0)!")
        accuracy = period*2400 #divide graph into 36 sections
        period *= 86400 # days to seconds
        # Get a list of people (in this server) that joined at certain times. Maybe round these to a certain factor (don't overstress the x-axis)
        # These certain times are in a period of "now" and "[period] seconds ago"
        totals = []
        results = {}
        currentTime = mktime(datetime.utcnow().timetuple()) #  todo: globalize the time # maybe fixed with .utcnow() ?
        minTime = int((currentTime-period)/accuracy)*accuracy
        maxTime = int(currentTime/accuracy)*accuracy
        for y in data[str(ctx.guild.id)]:
            column = []
            results[y] = {}
            for member in data[str(ctx.guild.id)][y]:
                for time in data[str(ctx.guild.id)][y][member]:
                    #if the current time minus the amount of seconds in every day in the period since now, is still older than more recent joins, append it
                    if currentTime-period < time:
                        column.append(time)
                        if doubles == 0:
                            break
            totals.append(len(column))
            for time in range(len(column)):
                column[time] = int(column[time]/accuracy)*accuracy
                if column[time] in results[y]:
                    results[y][column[time]]+=1
                else:
                    results[y][column[time]]=1

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
        for y in data[str(ctx.guild.id)]:
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

        # for i in results:
            # print(i)
            # print(results[i])

        import matplotlib.pyplot as plt
        import pandas as pd
        # print("\n"*5+str([i for i in results["joined"]]))
        # print("\n"*5+str([results["joined"][i] for i in results["joined"]]))
        d = {
            "time": [i for i in results["joined"]],
            "joined":[results["joined"][i] for i in results["joined"]],
            "left":[results["left"][i] for i in results["left"]],
            "verified":[results["verified"][i] for i in results["verified"]]
        }
        df = pd.DataFrame(data=d)
        # print(df)
        fig, (ax1) = plt.subplots(1,1)
        fig.suptitle(f"Joins (b), leaves (r), and verifications (g) in the past {period/86400} days ({period} seconds)")
        fig.tight_layout(pad=1.0)
        ax1.plot(df['time'], df["joined"], 'b')
        ax1.plot(df['time'], df["left"], 'r')
        ax1.plot(df['time'], df["verified"], 'g')
        ax1.set_ylabel("# of players joined")
        fig.subplots_adjust(bottom=0.180, top=0.90, left=0.1, hspace=0.1)
        plt.savefig('joined.png')
        await ctx.send(f"In the past {period/86400} days, `{totals[0]}` members joined, `{totals[1]}` left, and `{totals[2]}` were verified. (with{'out'*(1-doubles)} doubles)",file=discord.File('joined.png') )

        # print(results)
        # await ctx.send(f"In the past {period/86400} days, `{totals[0]}` members joined, `{totals[1]}` left, and `{totals[2]}` were verified. (with{'out'*(1-doubles)} doubles)",hidden=True)
    else:
        await ctx.send("You don't have the right role to be able to execute this command! (sorrryyy)\n  (This project is still in early stages, if you think this is an error, please message MysticMia#7612)",hidden=True) #todo
    pass

@slash.slash(name="editvc",
            description="Edit your voice channel name or user limit",
            options=[
                create_option(
                    name="name",
                    description="Give your voice channel a name!",
                    option_type=3,
                    required=True),
                create_option(
                    name="limit",
                    description="Give your voice channel a user limit!",
                    option_type=4,
                    required=False)
            ])
async def editVc(ctx,name,limit=0):
    global newVcs
    allowedRoles = [
        discord.utils.find(lambda r: r.name == 'Verified'  , ctx.guild.roles)]
        # there's gotta be a better way to do this..
    # new method for multiple roles /\, old method for single role \/
    # role = discord.utils.find(lambda r: r.name == 'Verifier', ctx.guild.roles)
    # if role in ctx.author.roles:
    if len(set(allowedRoles).intersection(ctx.author.roles)) > 0:
        if ctx.author.voice is None:
            print(debug()+f"{ctx.author} tried to make a new vc channel but isn't connected to a voice channel")
            await ctx.send("You must be connected to a voice channel to use this command",hidden=True)
            return
        channel = ctx.author.voice.channel
        if channel.category.id not in [981558003822108733] or channel.id == 981557586723758091:
            await ctx.send("You can't change that voice channel's name!",hidden=True)
            return
        if len(name) < 4:
            await ctx.send("Your voice channel name needs to be at least 4 letters long!",hidden=True)
            return
        if len(name) > 35:
            await ctx.send("Please don't make your voice channel name more than 35 letters long! (pls don't make it spammy)",hidden=True)
            return
        if limit < 2 and limit != 0:
            await ctx.send("The user limit of your channel must be a positive amount of people... (at least 2)",hidden=True)
            return
        if limit > 999:
            await ctx.send("I don't think you need to account for that many people... (max 999)",hidden=True)
            return
        if name == "Untitled voice chat":
            await ctx.send("Are you really going to change it to that..",hidden=True)

        if channel.id in newVcs:
            # if you have made 2 renames in the past 10 minutes already
            if len(newVcs[channel.id]) < 2:
                #ignore but still continue the command
                pass
            elif newVcs[channel.id][0]+600 > mktime(datetime.now().timetuple()):
                await ctx.send("You can't edit your channel more than twice in 10 minutes! (bcuz discord :P)\n"+
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
        category = discord.utils.find(lambda r: r.name == 'VC'      , ctx.guild.categories)
        verified = discord.utils.find(lambda r: r.name == 'Verifier', ctx.guild.roles)
        limitInfo = [" with a user limit of "+str(limit) if limit > 0 else ""][0]
        def pingSafe(str):
            return str.replace("@everyone","@ everyone").replace("@here","@ here").replace('`','\`').replace('@','\@').replace('>','\>')
        await ctx.send(f"Voice channel renamed from \"{pingSafe(channel.name)}\" to \"{pingSafe(name)}\" (by {pingSafe(ctx.author.nick or ctx.author.name)}, {ctx.author.id})"+limitInfo, allowed_mentions=discord.AllowedMentions.none())
        await channel.edit(reason=f"Voice channel renamed from \"{channel.name}\" to \"{name}\""+limitInfo,user_limit=limit,name=name)
    else:
        await ctx.send("You don't have the right role to be able to execute this command! (sorrryyy)\n  (This project is still in early stages, if you think this is an error, please message MysticMia#7612)",hidden=True) #todo
        return

@slash.slash(name="table",
            description="Edit a table system")
async def table(ctx):
    pass

@slash.subcommand(base="table", subcommand_group="message",name="send",description="Send initial table object message. developmental purposes only",
            options=[
                create_option(
                    name="channel",
                    description="Which channel do you want to send the message in?",
                    option_type=7,
                    required=False)
            ])
async def tablemsgsend(ctx,channel=None):
    if ctx.author.id != 262913789375021056:
        ctx.send("Only Mia can send this message, due to developmental purposes. I hope you understand, otherwise just send a lil dm lol",hidden=True)
    await tablemsg(ctx,channel)
    {
      # "embeds": [
      #   {
      #     "image": {
      #       "url": "https://i.imgur.com/SBy90SG.png"
      #     }
      #   },
      #   {
      #     "title": "Join a Table",
      #     "description": "Click one of the buttons below to join a table!~",
      #     "color": 8481900,
      #     "fields": [
      #       {
      #         "name": "<:red:964277761575387186> Table 1",
      #         "value": "<@&981672127465934878>",
      #         "inline": true
      #       },
      #       {
      #         "name": "<:Purple:964277761344684072> Table 2",
      #         "value": "<@&981672186223943750>",
      #         "inline": true
      #       },
      #       {
      #         "name": "<:green:964277760451285003> Table 3",
      #         "value": "<@&981672223695851560>",
      #         "inline": true
      #       },
      #       {
      #         "name": "<:Blue:964277761294336111> Table 4",
      #         "value": "<@&981672304645926953>",
      #         "inline": true
      #       },
      #       {
      #         "name": "<:Orange:964277761134977024> Table 5",
      #         "value": "<@&981672374665633892>",
      #         "inline": true
      #       },
      #       {
      #         "name": "<:Yellow:964277761629884426> Table 6",
      #         "value": "<@&981673889396563988>",
      #         "inline": true
      #       }
      #     ],
      #     "footer": {
      #       "text": "UALL|981672127465934878|Table 1|964277761575387186\nUALL|981672186223943750|Table 2|964277761344684072\nUALL|981672223695851560|Table 3|964277760451285003\n[SPLIT]\nUALL|981672304645926953|Table 4|964277761294336111\nUALL|981672374665633892|Table 5|964277761134977024\nUALL|981673889396563988|Table 6|964277761629884426"
      #     },
      #     "image": {
      #       "url": "https://i.imgur.com/t3zhm4k.png"
      #     }
      #   }
      # ],
      # "attachments": []
    }

async def tablemsg(ctx,channel=None):
    global tableInfo
    if len(tableInfo) == 0:
        await ctx.send("Couldn't find table data. Please wait 1 second.",hidden=True)
        return
    if channel is not None and type(channel) is not discord.TextChannel:
        await ctx.send("You did not mention a (correct) text channel!",hidden=True)
        return
    embed1 = discord.Embed(color=8481900, type='rich',description=" ")
    embed2 = discord.Embed(color=8481900, type='rich', title='Join a Table!',
        description="Click one of the buttons below to create or join a table!~")
    embed1.set_image(url="https://i.imgur.com/SBy90SG.png")
    embed2.set_image(url="https://i.imgur.com/t3zhm4k.png") # i feel like this doesn't do anything..

    components = [{  "type": 1,"components":[]  }]
    for x in tableInfo:
        x = tableInfo[x]
        try:
            disabled,status,label = getTableStatus(x)
        except TypeError:
            continue
        embed2.add_field(name=f'{x["emoji"]} Table {x["id"]} ({status})',value=f'<@&{x["member"]}>')
        if ">" in x["emoji"]:
            emoji = x["emoji"].replace(">","").split(":")
            if len(emoji) > 1:
                emoji = {"name":emoji[1],"id":emoji[2]}
        else:
            emoji = {"name":x["emoji"]}
        component = {"type": 2,
         "label": f'{label} {x["id"]}',
         "style": 2,
         "emoji": emoji,
         "custom_id": "table"+x["id"],
         "disabled": disabled}
        components[0]["components"].append(component)

    if channel:
        ctx.channel_id, ctx.channel.id = [channel.id,channel.id]
    if "message" in tableInfo:
        print(f"I am looking for {tableInfo['message']}, most likely in {tableInfo['msgChannel']}")
        await ctx.send("Checking for a message to delete first...",hidden=True)
        try:
            c = ctx.guild.text_channels[0]
            c.id = tableInfo["msgChannel"]
            await c.fetch_message(tableInfo["message"]).delete()
        except:
            print("Couldn't find message through ctx thing")
            for c in ctx.guild.text_channels:
                try:
                    msg = await c.fetch_message(tableInfo["message"])
                    print(f"Msg found in {c.name} / {c.id}!")
                    await msg.delete()
                    break
                except:
                    print(f"{c.name} / {c.id} didn't have the message")
            else:
                await ctx.send("Couldn't find a message to delete",hidden=True)
    msg = await ctx.send(embeds=[embed1,embed2],components=components)
    tableInfo["msgChannel"] = msg.channel.id
    tableInfo["message"] = msg.id

async def tablemsgUpdate(ctx):
    global tableInfo
    embed1 = discord.Embed(color=8481900, type='rich',description=" ")
    embed2 = discord.Embed(color=8481900, type='rich', title='Join a Table!',
        description="Click one of the buttons below to create or join a table!~")
    embed1.set_image(url="https://i.imgur.com/SBy90SG.png")
    embed2.set_image(url="https://i.imgur.com/t3zhm4k.png") # i feel like this doesn't do anything..

    components = [{  "type": 1,"components":[]  }]
    for x in tableInfo:
        x = tableInfo[x]
        try:
            disabled,status,label = getTableStatus(x)
        except TypeError:
            continue
        embed2.add_field(name=f'{x["emoji"]} Table {x["id"]} ({status})',value=f'<@&{x["member"]}>')
        if ">" in x["emoji"]:
            emoji = x["emoji"].replace(">","").split(":")
            if len(emoji) > 1:
                emoji = {"name":emoji[1],"id":emoji[2]}
        else:
            emoji = {"name":x["emoji"]}
        component = {"type": 2,
         "label": f'{label} {x["id"]}',
         "style": 2,
         "emoji": emoji,
         "custom_id": "table"+x["id"],
         "disabled": disabled}
        components[0]["components"].append(component)

    print(f"I am looking for {tableInfo['message']}, most likely in {tableInfo['msgChannel']}")
    try:
        c = ctx.guild.text_channels[0]
        c.id = tableInfo["msgChannel"]
        msg = await c.fetch_message(tableInfo["message"])
    except:
        print("Couldn't find message through ctx thing")
        for c in ctx.guild.text_channels:
            try:
                msg = await c.fetch_message(tableInfo["message"])
                print(f"Msg found in {c.name} / {c.id}!")
                break
            except:
                print(f"{c.name} / {c.id} didn't have the message")
        else:
            print("couldn't find message to update")
    msg = await msg.edit(embed=embed2,components=components)
    # tableInfo["msgChannel"] = msg.channel.id
    # tableInfo["message"] = msg.id

@slash.subcommand(base="table",name="build",
            options=[
                create_option(
                    name="id",
                    description="Give the table a number: \"1\" for \"Table 1\", eg.",
                    option_type=3,
                    required=True),
                create_option(
                    name="category",
                    description="Mention the table category",
                    option_type=7,
                    required=True),
                create_option(
                    name="owner",
                    description="Ping/mention the table owner role",
                    option_type=8,
                    required=True),
                create_option(
                    name="member",
                    description="Ping/mention the table (member) role",
                    option_type=8,
                    required=True),
                create_option(
                    name="emoji",
                    description="Type the emoji (circle) for the table",
                    option_type=3,
                    required=True)
            ])
async def build(ctx,id,category,owner,member,emoji):
    global tableInfo
    if type(category) is not discord.CategoryChannel:
        await ctx.send("You did not mention the right category!",hidden=True)
        return
    tableInfo["table"+id] = {
        "id":id,
        "category":category.id,
        "owner":owner.id,
        "member":member.id,
        "emoji":emoji,
        "status":"new",
    }
    await ctx.send(f"┬─┬ ノ( ゜-゜ノ) Created `Table {id}` with category:<#{category.id}>, owner:<@&{owner.id}>, member:<@&{member.id}>, emoji:{emoji}",allowed_mentions=discord.AllowedMentions.none())
    #print(tableInfo)

@slash.subcommand(base="table",name="destroy",
            options=[
                create_option(
                    name="id",
                    description="Give the table's ID: \"1\" for \"Table 1\", eg.",
                    option_type=3,
                    required=True),
                ])
async def destroy(ctx,id):
    global tableInfo
    for x in tableInfo:
        try:
            if tableInfo[x]["id"] == id:
                del tableInfo[x]
                await ctx.send(f"(╯°□°）╯︵ ┻━┻ Destroyed table {id} successfully. Happy now? ")
                return
        except TypeError: #probably the message/channel info
            pass
    await ctx.send(f"Finished command without any action, thus the id was likely incorrect",hidden=True)

@slash.subcommand(base="table",name="lock", description="Lock your table, so no new players can join.")
async def tableLock(ctx):
    global tableInfo
    if len(tableInfo) == 0:
        await ctx.send("Couldn't find table data. Please wait 1 second.",hidden=True)
        return
    lockable = ""
    if not "message" in tableInfo:
        await ctx.send("There is no table message to update, thus I'm afraid you can't lock your table..",hidden=True)
        return
    for table in tableInfo:
        try:
            for role in ctx.author.roles:
                if role.id == tableInfo[table]["owner"]:
                    lockable = table
            if lockable:
                break
        except: #is message dictionary, probably
            pass
    if lockable == "":
        await ctx.send("You aren't a table owner, thus can't lock this table!",hidden=True)
        return
    tableInfo[lockable]["status"] = "locked"

    # send update message in table chat
    category = discord.utils.find(lambda r: r.id == tableInfo[lockable]["category"], ctx.guild.categories)
    channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
    await channel.send("This table was locked by the table owner. No new players can join the table anymore.\nUse `/table unlock` as table owner to open the table again.")
    await ctx.send("Locked successfully",hidden=True)
    await tablemsgUpdate(ctx)

@slash.subcommand(base="table",name="unlock", description="Unlock your table, so new players can join again.")
async def tableUnlock(ctx):
    global tableInfo
    if len(tableInfo) == 0:
        await ctx.send("Couldn't find table data. Please wait 1 second.",hidden=True)
        return
    unlockable = ""
    if not "message" in tableInfo:
        await ctx.send("There is no table message to update, thus I'm afraid you can't lock your table..",hidden=True)
        return
    for table in tableInfo:
        try:
            for role in ctx.author.roles:
                if role.id == tableInfo[table]["owner"]:
                    unlockable = table
            if unlockable:
                break
        except: #is message dictionary, probably
            pass
    if unlockable == "":
        await ctx.send("You aren't a table owner, thus can't unlock this table!",hidden=True)
        return

    tableInfo[unlockable]["status"] = "open"

    # send update message in table chat
    category = discord.utils.find(lambda r: r.id == tableInfo[unlockable]["category"], ctx.guild.categories)
    channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
    await channel.send("This table was unlocked by the table owner. Players can join the table again.\nUse `/table lock` as table owner to lock the table.")
    await ctx.send("Locked successfully",hidden=True)

@slash.subcommand(base="table", name="close", description="Close your table, a new group can start.")
async def tableClose(ctx):
    global tableInfo
    if len(tableInfo) == 0:
        await ctx.send("Couldn't find table data. Please wait 1 second.",hidden=True)
        return
    closable = ""
    if not "message" in tableInfo:
        await ctx.send("There is no table message to update, thus I'm afraid you can't close your table..",hidden=True)
        return
    for table in tableInfo:
        try:
            for role in ctx.author.roles:
                if role.id == tableInfo[table]["owner"]:
                    closable = table
            if closable:
                break
        except: #is message dictionary, probably
            pass
    if closable == "":
        await ctx.send("You aren't a table owner, thus can't close this table!",hidden=True)
        return
    # remove every member and the owner from the table
    ownerRole = discord.utils.find(lambda r: r.id == tableInfo[closable]["owner"], ctx.guild.roles)
    for member in ownerRole.members:
        await member.remove_roles(ownerRole)
    try:
        memberRole = discord.utils.find(lambda r: r.id == tableInfo[closable]["member"], ctx.guild.roles)
        for member in memberRole.members:
            await member.remove_roles(memberRole)
    except TypeError:
        print(f"Tried to remove all members from table {tableInfo[closable]['id']}, but there were none maybe?")

    tableInfo[closable]["status"] = "new"
    # send update message in table chat
    category = discord.utils.find(lambda r: r.id == tableInfo[closable]["category"], ctx.guild.categories)
    channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
    await channel.send("This table was closed by the table owner. A new table can be created now.")
    await ctx.send("Closed successfully",hidden=True)

@slash.subcommand(base="table",name="newowner", description="Transfer your ownership, in case you'd want someone else to have it instead.",
            options=[
                create_option(
                    name="newowner",
                    description="Give the table's ID: \"1\" for \"Table 1\", eg.",
                    option_type=6,
                    required=True),
                ])
async def tableNewOwner(ctx,newOwner):
    global tableInfo
    if len(tableInfo) == 0:
        await ctx.send("Couldn't find table data. Please wait 1 second.",hidden=True)
        return
    transfer = ""
    for table in tableInfo:
        try:
            for role in ctx.author.roles:
                if role.id == tableInfo[table]["owner"]:
                    transfer = table
            if transfer:
                break
        except: #is message dictionary, probably
            pass
    if transfer == "":
        await ctx.send("You aren't a table owner, thus can't transfer your ownership of this table!",hidden=True)
        return
    if discord.utils.find(lambda r: r.id == tableInfo[transfer]["member"], newOwner.roles) is None:
        await ctx.send("To grant someone ownership, they must have joined the table first (have table member role)!")
        return
    # change owner roles
    ownerRole = discord.utils.find(lambda r: r.id == tableInfo[transfer]["owner"], ctx.guild.roles)
    for member in ownerRole.members:
        await member.remove_roles(ownerRole)
    await newOwner.add_roles(ownerRole)

    # send update message in table chat
    category = discord.utils.find(lambda r: r.id == tableInfo[lockable]["category"], ctx.guild.categories)
    channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
    await channel.send(f"This table's ownership was transferred from {ctx.author.nick or ctx.author.name} ({ctx.author.id}) to {newOwner.nick or newOwner.name} ({newOwner.id}).",allowed_mentions=discord.AllowedMentions.none())
    await ctx.send(f"Ownership transferred successfully", allowed_mentions=discord.AllowedMentions.none(), hidden=True)

@client.event
async def on_error(event, *args, **kwargs):
    import traceback, logging
    #message = args[0]
    print(f"\n\n\n\n[{datetime.now().strftime('%H:%M:%S.%f')}] [ERROR]: {event}")
    logging.warning(traceback.format_exc())
    print('\n          '.join([repr(i) for i in args])+"\n\n")
    print('\n                   '.join([repr(i) for i in kwargs]))
    print(repr(event))

def signal_handler(signal, frame):
    # try to save files. if they haven't been loaded in yet (discord hasn't started on_read() yet;
    # and the files are empty, don't save the empty variables into them!) Then exit the program using sys.exit(0)
    print("📉 Disconnecting...")
    if len(data) > 0:
        json.dump(data, open(path+"data.json","w"))
        print("Saved data file!")
    else:
        print("Couldn't save data (unsafe)! Not loaded in correctly!")
    if len(tableInfo) > 0:
        json.dump(tableInfo, open(path+"tableInfo.json","w"))
        print("Saved table file!")
    else:
        print("Couldn't save table file (unsafe)! Not loaded in correctly!")

    if len(reactionmsgs) > 0:
        pickle.dump(reactionmsgs, open(path+"reactionmsgs.txt","wb"))
        print("Saved reactionmsgs data!")
    else:
        print("Couldn't save reactionmsgs data (unsafe)! Not loaded in correctly!")

    print("-=--- Finishing ---=-")
    try:
        sys.exit(0)
    except RuntimeError as ru:
        print("Excepted the runtime error, please ignore everything lol")
        try:
            sys.exit(0)
        except:
            print("double runtime error?")

signal.signal(signal.SIGINT, signal_handler) #notice KeyboardInterrupt, and run closing code (save files and exit)
client.run( #token v1
    open('token.txt',"r").read()
)

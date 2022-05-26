version = "0.1.7"
import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_permission # limit commands to roles/users
from discord_slash.model import SlashCommandPermissionType # limit commands to roles/users
from discord_slash.utils.manage_commands import create_option, create_choice # set command argument limitations (string/int/bool)

#from discord.utils import get #dunno what this is for tbh.
import json #json used for settings file
import pickle # pickle used for reactionmsgs file
import signal # save files when receiving KeyboardInterrupt
import sys # exit program after Keyboardinterrupt signal is noticed

from datetime import datetime, timedelta
from time import mktime #for unix time code
import random #for very uncute responses

# Dependencies:
#   server members intent, message content intent,
#   permissions:
#       send messages
#       read messages
#       remove reactions on a message
#

intents = discord.Intents.default()
intents.members = True #apparently this needs to be additionally defined cause it's not included in Intents.default()?
#setup default discord bot client settings, permissions, slash commands, and file paths
client =  commands.Bot(intents = intents
, command_prefix=commands.when_mentioned_or("/"), case_insensitive=True
, activity = discord.Game(name="with slash (/) commands!"))
slash = SlashCommand(client, sync_commands=True)

#default defining before settings
settings = {}
data = {}
dataTemplate = {
    "joined"  :{    },
    "left"    :{    },
    "verified":{    }}
reactionmsgs = {}
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
path = ""
# dunno if i should delete this. Could be used if your files are not in the same folder as this program.

@client.event
async def on_ready():
    global data,reactionmsgs
    #load the data file.
    if len(data) == 0:
        data = json.loads(open(path+"data.json","r").read())
    if len(reactionmsgs) == 0:
        reactionmsgs = pickle.loads(open('reactionmsgs.txt', 'rb').read())
    print(f"Files loaded and logged in as {client.user}, in version {version}")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    # random cool commands
    if message.content.startswith(":say "):
        await message.channel.send(message.content.split(" ",1)[1].replace("[[del]]",""))
        return
    if client.user.mentioned_in(message):
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
                "You're also part of the cuties set"]
            respond = random.choice(responses)
            if respond == "BAD!":
                await message.channel.send("https://cdn.discordapp.com/emojis/902351699182780468.gif?size=56&quality=lossless")
            await message.channel.send(respond)
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

# slash command format: https://dpyslash.readthedocs.io/en/latest/gettingstarted.html
@slash.slash(name="getdata",
            description="See joined, left, and recently verified users in x days",
            options=[
                create_option(
                    name="range",
                    description="Get data from [range] days ago",
                    option_type=3,
                    required=True),
                create_option(
                    name="doubles",
                    description="If someone joined twice, are they counted double? (y/n or 1/0)",
                    option_type=3,
                    required=False)
            ])
async def getData(ctx,range, doubles="false"):
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
            range = float(range)
            if range <= 0:
                await ctx.send("Your range (data in the past [x] days) has to be above 0!",hidden=True)
                return
        except:
            await ctx.send("Your range has to be an integer for the amount of days that have passed",hidden=True)
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
        range *= 86400 # days to seconds
        # Get a list of people (in this server) that joined at certain times. Maybe round these to a certain factor (don't overstress the x-axis)
        # These certain times are in a range of "now" and "[range] seconds ago"
        table = []
        for y in data[str(ctx.guild.id)]:
            column = []
            for member in data[str(ctx.guild.id)][y]:
                for time in data[str(ctx.guild.id)][y][member]:
                    #if the current time minus the amount of seconds in every day in the range since now, is still older than more recent joins, append it
                    if mktime(datetime.now().timetuple())-range < time: # todo: globalize the time
                        column.append(time)
                        if doubles == 0:
                            break
            table.append(len(column))
        await ctx.send(f"In the past {range/86400} days, `{table[0]}` members joined, `{table[1]}` left, and `{table[2]}` were verified. (with{'out'*(1-doubles)} doubles)",hidden=True)
    else:
        await ctx.send("You don't have the right role to be able to execute this command! (sorrryyy)\n  (This project is still in early stages, if you think this is an error, please message MysticMia#7612)",hidden=True) #todo
    pass

def signal_handler(signal, frame):
    # try to save files. if they haven't been loaded in yet (discord hasn't started on_read() yet;
    # and the files are empty, don't save the empty variables into them!) Then exit the program using sys.exit(0)
    print("📉 Disconnecting...")
    if len(data) > 0:
        json.dump(data, open(path+"data.json","w"))
        print("Saved data file!")
    else:
        print("Couldn't save data (unsafe)! Not loaded in correctly!")
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

signal.signal(signal.SIGINT, signal_handler) #notice KeyboardInterrupt, and run closing code (save files and exit)
client.run( #token v1
    open('token.txt',"r").read()
)

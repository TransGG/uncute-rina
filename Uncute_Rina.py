version = "0.1.4"
import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
#from discord.utils import get #dunno what this is for tbh.
import json #json used for settings file
import signal # save files when receiving KeyboardInterrupt
import sys # exit program after Keyboardinterrupt signal is noticed

from datetime import datetime, timedelta
from time import mktime #for unix time code
import random

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
# dunno if i should delete this. Could be used if your file is not in the same folder as this program.

@client.event
async def on_ready():
    global data
    #load the data file.
    if len(data) == 0:
        data = json.loads(open(path+"data.json","r").read())
    print(f"Files loaded and logged in as {client.user}, in version {version}")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if client.user.mentioned_in(message):
        if (("cutie" in message.content or "cute" in message.content) and "not" not in message.content and "uncute" not in message.content) or "not uncute" in message.content:
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
                "You gotta praise those around you as well. Cleo, for example, is very cute.",
                "Oh by the way, did I say Mia was cute yet? I probably didn't. Mia? You're very cute",
                "Such nice weather outside, isn't it? What- you asked me a question?\nNo you didn't, you're just talking to youself.",
                "".join(random.choice("acefgilrsuwnopacefgilrsuwnopacefgilrsuwnop;;  ") for i in range(random.randint(10,25))), # 3:2 letters to symbols
                "Oh I heard about that! That's a way to get randomized passwords from a transfem!",
                "Cuties are not gender-specific. For example, my cat is a cutie!\nOh wait, species aren't the same as genders. Am I still a catgirl then? Trans-species?",
                "...",
                "Hey that's not how it works!",
                "Hey my lie detector said you are lying.",
                "You know i'm not a mirror, right?"]
            await message.channel.send(random.choice(responses))
    return

async def addToData(member, type):
    global data
    print(data)
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
    global settings
    #get the message id from reaction.message_id through the channel (with reaction.channel_id) (oof lengthy process)
    message = await client.get_channel(reaction.channel_id).fetch_message(reaction.message_id)
    if reaction.emoji.name == '❌' and reaction.member != client.user:
        if message.author == client.user:
            await message.delete()

@slash.slash(name="getdata",description="See joined, left, and recently verified users in x days")
async def getData(ctx,range):
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
            range = int(range)
            if range < 1:
                await ctx.send("Your range (data in the past [x] days) has to be above 0!",hidden=True)
                return
        except:
            await ctx.send("Your range has to be an integer for the amount of days that have passed",hidden=True)
            return
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
            table.append(len(column))
        await ctx.send(f"In the past {int(range/86400)} days, `{table[0]}` members joined, `{table[1]}` left, and `{table[2]}` was verified.",hidden=True)
    else:
        await ctx.send("You don't have the right role to be able to execute this command! (sorrryyy)\n  (This project is still in early stages, if you think this is an error, please message MysticMia#7612)",hidden=True) #todo
    pass

def signal_handler(signal, frame):
    # try to save files. if they haven't been loaded in yet (discord hasn't started on_read() yet;
    # and the files are empty, don't save the empty variables into them!) Then exit the program using sys.exit(0)
    print("📉 Disconnecting...")
    # if len(settings) > 0:
    #     with open('settings.json', 'w') as f:
    #         json.dump(settings, open(path+"settings.json","w"))
    #     print("Saved guild settings!")
    # else:
    #     print("Couldn't save settings (unsafe)! Not loaded in correctly!")
    if len(data) > 0:
        json.dump(data, open(path+"data.json","w"))
        print("Saved data file!")
    else:
        print("Couldn't save data (unsafe)! Not loaded in correctly!")
    print("-=--- Finishing ---=-")
    try:
        sys.exit(0)
    except RuntimeError as ru:
        print("Excepted the runtime error, please ignore everything lol")

signal.signal(signal.SIGINT, signal_handler) #notice KeyboardInterrupt, and run closing code (save files and exit)


# import os
# from dotenv import load_dotenv
#
# load_dotenv()
#
# TOKEN = os.getenv("DISCORD_TOKEN")

client.run( #token v1
    open('token.txt',"r").read()
)

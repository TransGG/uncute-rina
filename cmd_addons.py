import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *

import re #use regex to remove pronouns from people's usernames, and split their names into sections by capital letter

import pymongo # for online database
from pymongo import MongoClient
import random # for picking a random call_cute quote

import requests # for getting the equality index of countries
import json # to interpret the obtained api data

from datetime import datetime, timedelta, timezone # for checking if user is older than 7days (in verification

import asyncio # for waiting a few seconds before removing a timed-out pronoun-selection message


def generateOutput(responses, author):
    output = ""
    if len(responses) > 0:
        output += f"""Hey there {author.mention},
Thank you for taking the time to answer our questions
If you don't mind, could you answer some more for us?"""

    keywords = ["First of all","Next","aaand..","Also","Lastly","PS","PPS","PPPS","PPPPS","PPPPPS","PPPPPPS"]
    for index in range(len(responses)):
        output += f"""

{keywords[index]},
{responses[index]}"""

    if len(output) > 0:
        output += """

Once again, if you dislike answering any of these or following questions, feel free to tell me. I can give others.
Thank you in advance :)"""
    else:
        output += "\n:warning: Couldn't think of any responses."
    return output

class Addons(commands.Cog):
    def __init__(self, client):
        global RinaDB
        self.client = client
        RinaDB = client.RinaDB
        self.headpatWait = 0

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        #random cool commands
        self.headpatWait += 1
        if self.headpatWait >= 500:
            ignore = False
            if type(message.channel) is discord.Thread:
                if message.channel.parent == 987358841245151262: # <#welcome-verify>
                    ignore = True
            if message.channel.name.startswith('ticket-') or message.channel.name.startswith('closed-'):
                ignore = True
            if message.channel.category.id in [959584962443632700, 959590295777968128, 959928799309484032, 1041487583475138692]: # <#Bulletin Board>, <#Moderation Logs>, <#Verifier Archive>, <#Events>
                ignore = True
            if message.guild_id in [981730502987898960]: # don't send in Mod server
                ignore = True
            if not ignore:
                self.headpatWait = 0
                try:
                    await message.add_reaction("<:TPF_02_Pat:968285920421875744>") #headpatWait
                except discord.errors.HTTPException:
                    await logMsg(message.guild, f'**:warning: Warning: **Couldn\'t add pat reaction to {message.jump_url}')
                    try:
                        await message.add_reaction("☺️") # relaxed
                    except:
                        raise

        if self.client.user.mention in message.content.split():
            msg = message.content.lower()
            if ((("cute" or "cutie" or "adorable" in msg) and "not" in msg) or "uncute" in msg) and "not uncute" not in msg:
                try:
                    await message.add_reaction("<:this:960916817801535528>")
                except:
                    await logMsg(message.guild, f'**:warning: Warning: **Couldn\'t add pat reaction to {message.jump_url}')
                    raise
            elif "cutie" in msg or "cute" in msg:
                responses = [
                    "I'm not cute >_<",
                    "I'm not cute! I'm... Tough! Badass!",
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



    @app_commands.command(name="say",description="Force Rina to repeat your wise words")
    @app_commands.describe(text="What will you make Rina repeat?")
    async def say(self, itx: discord.Interaction, text: str):
        if not isStaff(itx):
            await itx.response.send_message("Hi. sorry.. It would be too powerful to let you very cool person use this command.",ephemeral=True)
            return
        collection = RinaDB["guildInfo"]
        query = {"guild_id": itx.guild.id}
        guild = collection.find_one(query)
        if guild is None:
            debug("Not enough data is configured to do this action! Please fix this with `/editguildinfo`!",color="red")
            await itx.response.send_message("Couldn't send your message. You can't send messages in this server because the bot setup seems incomplete",ephemeral=True)
            return
        try:
            vcLog      = guild["vcLog"]
            logChannel = itx.guild.get_channel(vcLog)
            await logChannel.send(f"{itx.user.nick or itx.user.name} ({itx.user.id}) said a message using Rina: {text}", allowed_mentions=discord.AllowedMentions.none())
            text = text.replace("[[\\n]]","\n").replace("[[del]]","")
            await itx.channel.send(f"{text}", allowed_mentions=discord.AllowedMentions.none())
        except discord.Forbidden:
            await itx.response.send_message("Forbidden! I can't send a message in this channel/thread because I can't see it or because I'm not added to it yet!\n(Add me to the thread by mentioning me, or let Rina see this channel)",ephemeral=True)
            return
        except:
            await itx.response.send_message("Oops. Something went wrong!",ephemeral=True)
            raise
        await itx.response.send_message("Successfully sent!", ephemeral=True)

    @app_commands.command(name="compliment", description="Complement someone fem/masc/enby")
    @app_commands.describe(user="Who do you want to compliment?")
    async def compliment(self, itx: discord.Interaction, user: discord.User):
        # await itx.response.send_message("This command is currently disabled for now, since we're missing compliments. Feel free to suggest some, and ping @MysticMia#7612",ephemeral=True)
        # return

        try:
            user.roles
        except AttributeError:
            await itx.response.send_message("Aw man, it seems this person isn't in the server. I wish I could compliment them but they won't be able to see it!", ephemeral=True)
            return
        async def call(itx, user, type):
            quotes = {
                "fem_quotes": [
                    # "Was the sun always this hot? or is it because of you?",
                    # "Hey baby, are you an angel? Cuz I’m allergic to feathers.",
                    "I bet you sweat glitter.",
                    "Your hair looks stunning!",
                    "Being around you is like being on a happy little vacation.",
                    "Good girll",
                    "Who's a good girl?? You are!!",
                    "Amazing! Perfect! Beautiful! How **does** she do it?!",
                    "I can tell that you are a very special and talented girl!",
                    "Here, have this cute sticker!"
                ],
                "masc_quotes": [
                    "You are the best man out there.",
                    "You are the strongest guy I know.",
                    "You have an amazing energy!",
                    "You seem to know how to fix everything!",
                    "Waw, you seem like a very attractive guy!",
                    "Good boyy!",
                    "Who's a cool guy? You are!!",
                    "I can tell that you are a very special and talented guy!",
                    "You're such a gentleman!",

                ],
                "they_quotes": [
                    "I can tell that you are a very special and talented person!",
                    "Their, their... ",
                ],
                "it_quotes": [
                    "I bet you do the crossword puzzle in ink!",
                ],
                "unisex_quotes": [ #unisex quotes are added to each of the other quotes later on.
                    "Hey I have some leftover cookies.. \\*wink wink\\*",
                    # "_Let me just hide this here-_ hey wait, are you looking?!", #it were meant to be cookies TwT
                    "Would you like a hug?",
                    "Would you like to walk in the park with me? I gotta walk my catgirls",
                    "morb",
                    "You look great today!",
                    "You light up the room!",
                    "On a scale from 1 to 10, you’re an 11!",
                    'When you say, “I meant to do that,” I totally believe you.',
                    "You should be thanked more often. So thank you!",
                    "You are so easy to have a conversation with!",
                    "Ooh you look like a good candidate to give my pet blahaj to!",
                    "Here, have a sticker!"



                ]
            }
            type = {
                "she/her"   : "fem_quotes",
                "he/him"    : "masc_quotes",
                "they/them" : "they_quotes",
                "it/its"    : "it_quotes",
                "unisex"    : "unisex_quotes", #todo
            }[type]

            for x in quotes:
                if x == "unisex_quotes":
                    continue
                else:
                    quotes[x] += quotes["unisex_quotes"]

            collection = RinaDB["complimentblacklist"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                blacklist = []
            else:
                blacklist = search["list"]
            for string in blacklist:
                dec = 0
                for x in range(len(quotes[type])):
                    if string in quotes[type][x-dec]:
                        del quotes[type][x-dec]
                        dec += 1
            if len(quotes[type]) == 0:
                quotes[type].append("No compliment quotes could be given... This person seems to have blacklisted every quote.")

            base = f"{itx.user.mention} complimented {user.mention}!\n"
            if itx.response.is_done():
                # await itx.edit_original_response(content=base+random.choice(quotes[type]), view=None)
                await itx.followup.send(content=base+random.choice(quotes[type]), allowed_mentions=discord.AllowedMentions(everyone=False, users=[user], roles=False, replied_user=False))
            else:
                await itx.response.send_message(base+random.choice(quotes[type]), allowed_mentions=discord.AllowedMentions(everyone=False, users=[user], roles=False, replied_user=False))
        async def confirm_gender():
            # Define a simple View that gives us a confirmation menu
            class Confirm(discord.ui.View):
                def __init__(self, timeout=None):
                    super().__init__()
                    self.value = None
                    self.timeout = timeout

                # When the confirm button is pressed, set the inner value to `True` and
                # stop the View from listening to more input.
                # We also send the user an ephemeral message that we're confirming their choice.
                @discord.ui.button(label='She/Her', style=discord.ButtonStyle.green)
                async def feminine(self, itx: discord.Interaction, button: discord.ui.Button):
                    self.value = "she/her"
                    await itx.response.edit_message(content='Selected She/Her pronouns for compliment', view=None)
                    self.stop()

                @discord.ui.button(label='He/Him', style=discord.ButtonStyle.green)
                async def masculine(self, itx: discord.Interaction, button: discord.ui.Button):
                    self.value = "he/him"
                    await itx.response.edit_message(content='Selected He/Him pronouns for the compliment', view=None)
                    self.stop()

                @discord.ui.button(label='They/Them', style=discord.ButtonStyle.green)
                async def enby_them(self, itx: discord.Interaction, button: discord.ui.Button):
                    self.value = "they/them"
                    await itx.response.edit_message(content='Selected They/Them pronouns for the compliment', view=None)
                    self.stop()

                @discord.ui.button(label='It/Its', style=discord.ButtonStyle.green)
                async def enby_its(self, itx: discord.Interaction, button: discord.ui.Button):
                    self.value = "it/its"
                    await itx.response.edit_message(content='Selected It/Its pronouns for the compliment', view=None)
                    self.stop()

                @discord.ui.button(label='Unisex/Unknown', style=discord.ButtonStyle.grey)
                async def unisex(self, itx: discord.Interaction, button: discord.ui.Button):
                    self.value = "unisex"
                    await itx.response.edit_message(content='Selected Unisex/Unknown gender for the compliment', view=None)
                    self.stop()

            view = Confirm(timeout=60)
            await itx.response.send_message(f"{user.mention} doesn't have any pronoun roles! Which pronouns would like to use for the compliment?", view=view,ephemeral=True)
            await view.wait()
            if view.value is None:
                await itx.edit_original_response(content=':x: Timed out...', view=None)
                # await asyncio.sleep(3)
                # await itx.delete_original_response()
            else:
                await call(itx, user, view.value)

        roles = ["he/him", "she/her", "they/them", "it/its"]
        userroles = user.roles[:]
        random.shuffle(userroles) # pick a random order for which pronoun role to pick
        for role in userroles:
            if role.name.lower() in roles:
                await call(itx, user, role.name.lower())
                return
        await confirm_gender()

    @app_commands.command(name="complimentblacklist", description="If you dislike words in certain compliments")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Add a string to your compliments blacklist', value=1),
        discord.app_commands.Choice(name='Remove a string from your compliments blacklist', value=2),
        discord.app_commands.Choice(name='Check your blacklisted strings', value=3)
    ])
    @app_commands.describe(string="What sentence or word do you want to blacklist? (eg: 'good girl' or 'girl')")
    async def complimentblacklist(self, itx: discord.Interaction, mode: int, string: str):
        if mode == 1: # add an item to the blacklist
            if len(string) > 150:
                await itx.response.send_message("Please make strings shorter than 150 characters...",ephemeral=True)
                return
            collection = RinaDB["complimentblacklist"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                blacklist = []
            else:
                blacklist = search['list']
            blacklist.append(string)
            collection.update_one(query, {"$set":{f"list":blacklist}}, upsert=True)
            await itx.response.send_message(f"Successfully added {repr(string)} to your blacklist. ({len(blacklist)} item{'s'*(len(blacklist)!=1)} in your blacklist now)",ephemeral=True)

        elif mode == 2: # Remove item from black list
            try:
                string = int(string)
            except ValueError:
                await itx.response.send_message("To remove a string from your blacklist, you must give the id of the string you want to remove. This should be a number... You didn't give a number...", ephemeral=True)
                return
            collection = RinaDB["complimentblacklist"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                await itx.response.send_message("There are no items on your blacklist, so you can't remove any either...",ephemeral=True)
                return
            blacklist = search["list"]

            try:
                del blacklist[string]
            except IndexError:
                cmd_mention = self.client.getCommandMention("complimentblacklist")
                await itx.response.send_message(f"Couldn't delete that ID, because there isn't any item on your list with that ID.. Use {cmd_mention}` mode:Check` to see the IDs assigned to each item on your list",ephemeral=True)
                return
            collection.update_one(query, {"$set":{f"list":blacklist}}, upsert=True)
            await itx.response.send_message(f"Successfully removed '{string}' from your blacklist. Your blacklist now contains {len(blacklist)} string{'s'*(len(blacklist)!=1)}.", ephemeral=True)
        elif mode == 3:
            collection = RinaDB["complimentblacklist"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                await itx.response.send_message("There are no strings in your blacklist, so.. nothing to list here....",ephemeral=True)
                return
            blacklist = search["list"]
            length = len(blacklist)

            ans = []
            for id in range(length):
                ans.append(f"`{id}`: {blacklist[id]}")
            ans = '\n'.join(ans)
            await itx.response.send_message(f"Found {length} string{'s'*(length!=1)}:\n{ans}",ephemeral=True)

    nameusage = app_commands.Group(name='nameusage', description='Get data about which names are used in the server')

    @nameusage.command(name="gettop", description="See how often different names occur in this server")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Search most-used usernames', value=1),
        discord.app_commands.Choice(name='Search most-used nicknames', value=2),
        discord.app_commands.Choice(name='Search nicks and usernames', value=3),
    ])
    # @app_commands.describe(string="What sentence or word do you want to blacklist? (eg: 'good girl' or 'girl')")
    async def nameusage_gettop(self, itx: discord.Interaction, mode: int):#, mode: int, string: str):
        await itx.response.defer(ephemeral=True)
        sections = {}
        for member in itx.guild.members:
            member_sections = []
            if mode == 1:
                names = [member.name]
            elif mode == 2 and member.nick is not None:
                names = [member.nick]
            elif mode == 3:
                names = [member.name]
                if member.nick is not None:
                    names.append(member.nick)
            else:
                continue

            _pronouns = [
                "she", "her",
                "he", "him",
                "they", "them",
                "it", "its"
            ]
            pronouns = []
            for pronounx in _pronouns:
                for pronouny in _pronouns:
                    pronouns.append(pronounx + " " + pronouny)

            for index in range(len(names)):
                new_name = ""
                for char in names[index]:
                    if char.lower() in "abcdefghijklmnopqrstuvwxyz":
                        new_name += char
                    else:
                        new_name += " "

                for pronoun in pronouns:
                    _name_backup = new_name + " "
                    while new_name != _name_backup:
                        _name_backup = new_name
                        new_name = re.sub(pronoun, "", new_name, flags=re.IGNORECASE)

                names[index] = new_name

            def add(part):
                if part not in member_sections:
                    member_sections.append(part)

            for name in names:
                for section in name.split():
                    if section in member_sections:
                        pass
                    else:
                        parts = []
                        match = 1
                        while match:
                            match = re.search("[A-Z][a-z]*[A-Z]", section, re.MULTILINE)
                            if match:
                                caps = match.span()[1]-1
                                parts.append(section[:caps])
                                section = section[caps:]
                        if len(parts) != 0:
                            for part in parts:
                                add(part)
                            add(section)
                        else:
                            add(section)

            for section in member_sections:
                section = section.lower()
                if section in ["the", "any"]:
                    continue
                if len(section) < 3:
                    continue
                if section in sections:
                    sections[section] += 1
                else:
                    sections[section] = 1

        sections = sorted(sections.items(), key=lambda x:x[1], reverse=True)
        pages = []
        for i in range(int(len(sections)/20+0.999)+1):
            result_page = ""
            for section in sections[0+20*i:20+20*i]:
                result_page += f"{section[1]} {section[0]}\n"
            if result_page == "":
                result_page = "_"
            pages.append(result_page)
        page = 0
        class Pages(discord.ui.View):
            def __init__(self, pages, timeout=None):
                super().__init__()
                self.value   = None
                self.timeout = timeout
                self.page    = 0
                self.pages   = pages

            # When the confirm button is pressed, set the inner value to `True` and
            # stop the View from listening to more input.
            # We also send the user an ephemeral message that we're confirming their choice.
            @discord.ui.button(label='Previous', style=discord.ButtonStyle.blurple)
            async def previous(self, itx: discord.Interaction, _button: discord.ui.Button):
                # self.value = "previous"
                self.page -= 1
                if self.page < 0:
                    self.page += 1
                    await itx.response.send_message("This is the first page, you can't go to a previous page!",ephemeral=True)
                    return
                result_page = self.pages[self.page*2]
                result_page2 = self.pages[self.page*2+1]
                embed = discord.Embed(color=8481900, type='rich', title=f'Most-used {"user" if type==1 else "nick"}names leaderboard!')
                embed.add_field(name="Column 1",value=result_page)
                embed.add_field(name="Column 2",value=result_page2)
                embed.set_footer(text="page: "+str(self.page+1)+" / "+str(int(len(self.pages)/2)))
                await itx.response.edit_message(embed=embed)

            @discord.ui.button(label='Next', style=discord.ButtonStyle.blurple)
            async def next(self, itx: discord.Interaction, _button: discord.ui.Button):
                self.page += 1
                try:
                    result_page = self.pages[self.page*2]
                    result_page2 = self.pages[self.page*2+1]
                except IndexError:
                    await itx.response.send_message("This is the last page, you can't go to a next page!",ephemeral=True)
                    return
                embed = discord.Embed(color=8481900, type='rich', title=f'Most-used {"user" if type==1 else "nick"}names leaderboard!')
                embed.add_field(name="Column 1",value=result_page)
                embed.add_field(name="Column 2",value=result_page2)
                embed.set_footer(text="page: "+str(self.page+1)+" / "+str(int(len(self.pages)/2)))
                try:
                    await itx.response.edit_message(embed=embed)
                except discord.errors.HTTPException:
                    self.page -= 1
                    await itx.response.send_message("This is the last page, you can't go to a next page!",ephemeral=True)

        result_page = pages[page]
        result_page2 = pages[page+1]
        embed = discord.Embed(color=8481900, type='rich', title=f'Most-used {"user" if type==1 else "nick"}names leaderboard!')
        embed.add_field(name="Column 1",value=result_page)
        embed.add_field(name="Column 2",value=result_page2)
        embed.set_footer(text="page: "+str(page+1)+" / "+str(int(len(pages)/2)))
        view = Pages(pages, timeout=60)
        await itx.followup.send(f"",embed=embed, view=view,ephemeral=True)
        await view.wait()
        if view.value is None:
            await itx.edit_original_response(view=None)

    @nameusage.command(name="name", description="See how often different names occur in this server")
    @app_commands.describe(name="What specific name are you looking for?")
    @app_commands.choices(type=[
        discord.app_commands.Choice(name='usernames', value=1),
        discord.app_commands.Choice(name='nicknames', value=2),
        discord.app_commands.Choice(name='Search both nicknames and usernames', value=3),
    ])
    async def nameusage_name(self, itx: discord.Interaction, name: str, type: int):
        await itx.response.defer(ephemeral=True)
        count = 0
        type_string = ""
        if type == 1:
            for member in itx.guild.members:
                if name.lower() in member.name.lower():
                    count += 1
            type_string = "username"
        elif type == 2:
            for member in itx.guild.members:
                if member.nick is not None:
                    if name.lower() in member.nick.lower():
                        count += 1
            type_string = "nickname"
        elif type == 3:
            for member in itx.guild.members:
                if member.nick is not None:
                    if name.lower() in member.nick.lower() or name.lower() in member.name.lower():
                        count += 1
                elif name.lower() in member.name.lower():
                    count += 1
            type_string = "username or nickname"
        await itx.followup.send(f"I found {count} people with '{name.lower()}' in their {type_string}",ephemeral=True)


    @app_commands.command(name="roll", description="Roll a die or dice with random chance!")
    @app_commands.describe(dice="How many dice do you want to roll?",
                           faces="How many sides does every die have?",
                           mod="Do you want to add a modifier? (add 2 after rolling the dice)",
                           advanced="Roll more advanced! example: 1d20+3*2d4. Overwrites dice/faces given; 'help' for more")
    async def roll(self, itx: discord.Interaction, dice: int, faces: int, public: bool = False, mod: int = None, advanced: str = None):
        if advanced is None:
            if dice < 1 or faces < 1:
                await itx.response.send_message("You can't have negative dice/faces! Please give a number above 0",ephemeral=True)
                return
            if dice > 100000:
                await itx.response.send_message(f"Sorry, if I let you roll `{dice:,}` dice, then the universe will implode, and Rina will stop responding to commands. Please stay below 1 million dice...",ephemeral=True)
                return
            if faces > 100000:
                await itx.response.send_message(f"Uh.. At that point, you're basically rolling a sphere. Even earth has fewer faces than `{dice:,}`. Please bowl with a sphere of fewer than 1 million faces...",ephemeral=True)
            rolls = []
            for die in range(dice):
                rolls.append(random.randint(1,faces))

            if mod is None:
                if dice == 1:
                    out = f"I rolled {dice} di{'c'*(dice>1)}e with {faces} face{'s'*(faces>1)}: " +\
                          f"{str(sum(rolls))}"
                else:
                    out = f"I rolled {dice} di{'c'*(dice>1)}e with {faces} face{'s'*(faces>1)}:\n" +\
                          f"{' + '.join([str(roll) for roll in rolls])}  =  {str(sum(rolls))}"
            else:
                out = f"I rolled {dice} {'die' if dice == 0 else 'dice'} with {faces} face{'s'*(faces>1)} and a modifier of {mod}:\n" +\
                      f"({' + '.join([str(roll) for roll in rolls])}) + {mod}  =  {str(sum(rolls)+mod)}"
            if len(out) > 1995:
                out = f"I rolled {dice:,} {'die' if dice == 0 else 'dice'} with {faces:,} face{'s'*(faces>1)}"+f" and a modifier of {(mod or 0):,}"*(mod is not None)+":\n" +\
                      f"With this many numbers, I've simplified it a little. You rolled `{sum(rolls)+(mod or 0):,}`."
                roll_db = {}
                for roll in rolls:
                    try:
                        roll_db[roll] += 1
                    except KeyError:
                        roll_db[roll] = 1
                roll_db = dict(sorted(roll_db.items()))
                details = "You rolled "
                for roll in roll_db:
                    details += f"'{roll}'x{roll_db[roll]}, "
                if len(details) > 1500:
                    details = ""
                elif len(details) > 300:
                    public = False
                out = out + "\n" + details
            elif len(out) > 300:
                public = False
            await itx.response.send_message(out,ephemeral=not public)
        else:
            advanced = advanced.replace(" ","")
            def prod(list: list):
                a = 1
                for x in list:
                    a *= x
                return a

            def generate_roll(query: str):
                # print(query)
                temp = query.split("d")
                ## 2d4 = ["2","4"]
                ## 2d3d4 = ["2","3","4"] (huh?)
                ## 4 = 4
                ## [] (huh?)
                if len(temp) > 2:
                    raise ValueError("Can't have more than 1 'd' in the query of your die!")
                if len(temp) == 1:
                    try:
                        temp[0] = int(temp[0])
                    except ValueError:
                        raise TypeError(f"You can't do operations with '{temp[0]}'")
                    return [temp[0]]
                if len(temp) < 1:
                    raise ValueError(f"I couldn't understand what you meant with {query} ({str(temp)})")
                dice = temp[0]
                faces = ""
                for x in temp[1]:
                    if x in "0123456789":
                        faces += x
                    else:
                        break
                remainder = temp[1][len(faces):]
                try:
                    dice = int(dice)
                except ValueError:
                    raise ValueError(f"You have to roll a numerical number of dice! (You tried to roll '{dice}' dice)")
                try:
                    faces = int(faces)
                except ValueError:
                    raise TypeError(
                        f"You have to roll a die with a numerical number of faces! (You tried to roll {dice} dice with '{faces}' faces)")
                if len(remainder) > 0:
                    raise TypeError("Idk what happened, but you probably filled something in incorrectly.")
                if dice > 1000000:
                    raise OverflowError(f"Sorry, if I let you roll `{dice:,}` dice, then the universe will implode, and Rina will stop responding to commands. Please stay below 1 million dice...")
                if faces > 1000000:
                    raise OverflowError(f"Uh.. At that point, you're basically rolling a sphere. Even earth has fewer faces than `{faces:,}`. Please bowl with a sphere of fewer than 1 million faces...")
                return [random.randint(1, faces) for _ in range(dice)]

            for char in advanced:
                if char not in "0123456789d+*":  # kKxXrR": #!!pf≤≥
                    await itx.response.send_message(f"Invalid input! This command doesn't have support for '{char}' yet!",ephemeral=True)
                    return
            add = advanced.split('+')
            # print("add:       ",add)
            multiply = []
            for section in add:
                multiply.append(section.split('*'))
            # print("multiply:  ",multiply)
            try:
                result = [[sum(generate_roll(query)) for query in section] for section in multiply]
            except (TypeError,ValueError) as ex:
                ex = repr(ex).split("(",1)
                ex_type = ex[0]
                ex_message = ex[1][1:-2]
                await itx.response.send_message(f"Wasn't able to roll your dice!\n  {ex_type}: {ex_message}",ephemeral=True)
                return
            # print("result:    ",result)
            out = ["Input:  " + advanced]
            if "*" in advanced:
                out += [' + '.join([' * '.join([str(x) for x in section]) for section in result])]
            if "+" in advanced:
                out += [' + '.join([str(prod(section)) for section in result])]
            out += [str(sum([prod(section) for section in result]))]
            output = discord.utils.escape_markdown('\n= '.join(out))
            if len(output) >= 1950:
                output = "Your result was too long! I couldn't send it. Try making your rolls a bit smaller, perhaps by splitting it into multiple operations..."
            if len(output) >= 500:
                public = False
            try:
                await itx.response.send_message(output,ephemeral=not public)
            except discord.errors.NotFound:
                await itx.user.send("Couldn't send you the result of your roll because it took too long or something. Here you go: \n"+output)

    @app_commands.command(name="equaldex", description="Find info about LGBTQ+ laws in different countries!")
    @app_commands.describe(country_id="What country do you want to know more about? (GB, US, AU, etc.)")
    async def equaldex(self, itx: discord.Interaction, country_id: str):
        response_api = requests.get(
            f"https://www.equaldex.com/api/region?regionid={country_id}&formatted=true&apiKey=edd1d1790184e97861e7b5a51138845222d4c68b").text
        # returns ->  <pre>{"regions":{...}}</pre>  <- so you need to remove the <pre> and </pre> parts
        # it also has some <br \/>\r\n strings in there for some reason..? so uh
        response_api = response_api[6:-6].replace(r"<br \/>\r\n", r"\n")
        data = json.loads(response_api)
        if "error" in data:
            if country_id == "uk":
                await itx.response.send_message(f"I'm sorry, I couldn't find '{country_id}'...\nTry 'GB' instead!", ephemeral=True)
            else:
                await itx.response.send_message(f"I'm sorry, I couldn't find '{country_id}'...",ephemeral=True)
            return

        class Region:
            def __init__(self, data):
                self.id = data['region_id']
                self.name = data['name']
                self.continent = data['continent']
                self.url = data['url']
                self.issues = data['issues']

        region = Region(data['regions']['region'])

        embed = discord.Embed(color=7829503, type='rich',
                              title=region.name)
        for issue in region.issues:
            if type(region.issues[issue]['current_status']) is list:
                value = "No data"
            else:
                value = region.issues[issue]['current_status']['value_formatted']
                if len(region.issues[issue]['current_status']['description']) > 0:
                    value += f" ({region.issues[issue]['current_status']['description']})"
            embed.add_field(name=region.issues[issue]['label'],
                            value=value,
                            inline=False)
        embed.set_footer(text=f"For more info, click the button below,")
        class MoreInfo(discord.ui.View):
            def __init__(self, url):
                super().__init__()
                link_button = discord.ui.Button(style = discord.ButtonStyle.gray,
                                                label = "More info",
                                                url = url)
                self.add_item(link_button)
        view = MoreInfo(region.url)
        await itx.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="help", description="A help command to learn more about me!")
    async def help(self, itx: discord.Interaction):
        out = f"""\
Hi there! This bot has a whole bunch of commands. Let me introduce you to some:
{self.client.getCommandMention('compliment')}: Rina can compliment others (matching their pronoun role)
{self.client.getCommandMention('roll')}: roll some dice with a random result!
{self.client.getCommandMention('help')}: see this help page
{self.client.getCommandMention('dictionary')}: search for an lgbtq+-related term!
{self.client.getCommandMention('reminder')}: make or see your reminders!
{self.client.getCommandMention('todo')}: make, add, or remove items from your to-do list!

Make a custom voice channel by joining "Join to create VC"
{self.client.getCommandMention('editvc')}: edit the name or user limit of the custom voice channel!

{self.client.getCommandMention('pronouns')}: see someone's pronouns (from their role, or if they've added a custom one)
{self.client.getCommandMention('addpronoun')}: add one of your own pronouns
{self.client.getCommandMention('removepronoun')}: remove a pronoun

{self.client.getCommandMention('qotw')}: Suggest a question of the week to staff

Check out the #join-a-table channel: In this channel, you can claim a channel for roleplaying or tabletop games for you and your group!
The first person that joins/creates a table gets a Table Owner role, and can lock, unlock, or close their table.
{self.client.getCommandMention('table lock')}, {self.client.getCommandMention('table unlock')}, {self.client.getCommandMention('table close')}
You can also transfer your table ownership to another table member, after they joined your table: {self.client.getCommandMention('table newowner')}\
"""
        await itx.response.send_message(out, ephemeral=True)


    @app_commands.command(name="genanswer", description="Make verification question guesses")
    @app_commands.describe(messageid="Which message should I check? (id)")
    async def gen_answer(self, itx: discord.Interaction, messageid: str = None):
        await itx.response.defer(ephemeral=True)
        if messageid is None:
            messages = []
            async for msg in itx.channel.history(limit=100):
                class Interaction:
                    def __init__(self, user):
                        self.guild = user.guild
                        self.user = user
                if msg.author.bot:
                    continue
                elif type(msg.author) is discord.User:
                    messages.append(msg)
                elif not isVerified(Interaction(msg.author)):
                    messages.append(msg)
            messagelist = [str(i.id) for i in messages][::-1] # reverse list to make newest messages last
            if len(messagelist) == 0:
                await itx.followup.send(f"I can't find any messages in this channel that are from unverified people!", ephemeral=True)
        else:
            messagelist = [messageid]
            if "," in messageid:
                messagelist = [i.strip() for i in messageid.split(",")]
        lines = []
        for messageid in messagelist:
            try:
                messageid = int(messageid)
                message = await itx.channel.fetch_message(messageid)
            except discord.errors.NotFound:
                await itx.followup.send(f"I couldn't find that message ({messageid})!",ephemeral=True)
                return
            except ValueError:
                await itx.followup.send(f"That ('{messageid}') is not a valid message ID!",ephemeral=True)
                return

            if message is None:
                await itx.followup.send(f"That message has no content ({messageid})?",ephemeral=True)
                return
            if type(message.author) is discord.User:
                await itx.followup.send(f"This user left the server!",ephemeral=True)

            lines += message.content.split("\n")

        verification = []
        copy_pasta = [
            "1. Do you agree to the server rules and to respect the Discord Community Guidelines & Discord ToS?",
            "2. Do you identify as transgender; and/or any other part of the LGBTQ+ community? (Please be specific in your answer)",
            "3. Do you have any friends who are already a part of our Discord? (If yes, please send their username)",
            "4. What’s your main goal/motivation in joining the TransPlace Discord?",
            "5. If you could change one thing about the dynamic of the LGBTQ+ community, what would it be? ",
            "6. What is gatekeeping in relation to the trans community?",
            "# If you have any social media that contains relevant post  history related to the LGBTQ+ community, please link it to your discord account or send the account name or URL.",
        ]
        # newlineCount = 0
        q_string = ""
        for line in lines:
            if line == "":
                pass
            elif line in copy_pasta:
                q_string = line[0] # copy Question number
            elif ''.join(copy_pasta) in line:
                for pasta in copy_pasta:
                    if pasta in line:
                        q_string.replace(pasta, pasta[0])
            else:
                verification.append(q_string+line)
                # newlineCount = 0
                q_string = ""
        verification = '\n'.join(verification).lower()

        questions = ["1","2","3","4","5","6"]
        question = []
        warning = ""
        for number in range(len(questions)):
            try:
                start = verification.index(questions[number])
                try:
                    end = verification.index(questions[number+1])
                except IndexError: #notsure
                    end = len(verification)
                question.append(verification[start:end])
            except ValueError:
                if warning == "":
                    warning += f"Couldn't find question number for question '{questions[number]}'"
                else:
                    warning += f", '{questions[number]}'"
                if len(verification.split("\n")) >= 6:
                    question.append(verification.split("\n")[number])
        if len(question) < 3:
            await itx.followup.send("I couldn't determine/separate the question answers in this message.",ephemeral=True)
            return

        is_lgbtq = 0 # -1 = uncertain; 0 = cishet; 1 = lgbtq+
        is_trans = -1 # -1 = unconfirmed; 0 = cis; 1 = trans
        has_alibi = False
        is_new = False
        lgbtq_terms = [
            "trans",
            "m2f","f2m","mtf","ftm",
            "demi",
            "intersex",
            "nonbinary",
            "non-binary",
            "non binary",
            "questioning",
            "asexual","agender",
            "lesbian",
            "hrt",
            "ace",
            "aro",
            "gay",
            "homosexual",
            "bi",
            "pan",
            "fluid",
            "nb",
        ]
        trans_terms = [
            "trans",
            "m2f","f2m","mtf","ftm",
            "demi",
            "intersex",
            "agender",
            "nonbinary",
            "non-binary",
            "non binary",
            "fluid"]
        templates = [
            "What made you discover you were transgender?",
            "What would be an example of invalidating someone's identity?",
            "What do you hope to add or gain from this community?",
            "Anything you do or wish to do that makes you feel euphoric about your identity?",
            "Has the process of actually coming out and coming to terms with your identity been something recent?",
            "What is one thing only another lgbtq+ person would know? This can be as lighthearted or as serious as you want.",
            "How long have you been questioning? If it's for a short time, could you share me some things you've experimented with in terms of activities or appearance? "
                "If it's for a long time, could you share some experiences or opinions on different things you've tried?",
            "Do you have any pins, hats, flags, or something else pride-related that a random person trying to get verified wouldnt have that ties you to the lgbtq+ community?",
            "Do you have a fun or interesting story about something you did before you were trans (but still on-topic)? If you have any to share. If you don't that's fine too",
        ]


        out = "\n"
        if message.author.created_at > (datetime.now(tz=timezone.utc)-timedelta(days=7)):
            out += "User might have an account younger than 7 days\n"
            is_new = True

        if type(message.author) is discord.User:
            out += "User might have left the server\n"

        if "yes" not in question[0] and " agree" not in question[0]:
            out += "User might not have accepted the rules\n"

        if "no" in question[1] and "pronoun" not in question[1]:
            out += "They might be cis\n"
            is_trans = 0

        for term in lgbtq_terms:
            if term in question[1]:
                if is_lgbtq == 0:
                    out += f"Is in LGBTQ+: {term}"
                else:
                    out += f", {term}"
                if term in trans_terms:
                    is_trans = 1
                is_lgbtq = 1
        if is_lgbtq == 1:
            out += "\n"
        if "yes" in question[1] and is_lgbtq < 1:
            out += "Might not have fully answered what they identify as\n"
            is_lgbtq = -1
        if not ("yes" in question[1] or "no" in question[1]) and is_lgbtq == 0:
            out += "Indeterminate answer for question 2, cis maybe?\n"
            is_lgbtq = -1
        if ("no" not in question[2]) and (len(question[2]) > 7): # and "not" not in question[2]:
            has_alibi = True

        responses = []
        if not has_alibi:
            responses.append("How did you find out about this server?")
        if is_new:
            responses.append("It looks like your account is less than 7 days old.. Could you tell us why you joined with a new account?")
        if is_trans == 1:
            responses.append("Since you're transgender, what makes you the happiest as your gender? What gives you the most gender euphoria?")
        elif is_lgbtq == 1:
            responses.append("Why did you decide to join a trans server instead of any general LGTBQ+ server?")
        elif is_trans != 0 or is_lgbtq == -1:
            responses.append("If you don't mind answering, what do you identify as?")

        if len(responses) > 0:
            out += "\n__**Suggested output:**__\n"

        class ConfirmSend(discord.ui.View):
            class AddQuestion(discord.ui.Modal, title="Add question to Rina's verification message"):
                def __init__(self, responses, timeout=None):
                    super().__init__()
                    self.value = None
                    self.timeout = timeout
                    self.responses = responses
                    self.question = discord.ui.TextInput(label='Question',
                                                         placeholder="What made you start questioning that you were trans?",
                                                         style=discord.TextStyle.paragraph,
                                                         required=True)
                    self.add_item(self.question)

                async def on_submit(self, interaction: discord.Interaction):
                    self.value = 1
                    self.question = self.question.value.strip()
                    if len(self.question) < 3:
                        self.value = 9
                        try:
                            self.question = templates[int(self.question)]
                            self.value = 2
                        except (ValueError, IndexError):
                            await interaction.response.send_message("If you're trying to use a template.. you messed up\n"
                                                                    "Otherwise, make your string longer than 2 characters",
                                                                    ephemeral=True)
                            self.stop()
                            return

                    if self.question in self.responses:
                        await interaction.response.send_message('You added that question already.. but okay sure...', ephemeral=True)
                    else:
                        await interaction.response.send_message('Adding question...', ephemeral=True, delete_after=8)
                    self.stop()

            class RemoveQuestion(discord.ui.Modal, title="Remove from Rina's verification message"):
                def __init__(self, responses, timeout=None):
                    super().__init__()
                    self.value = None
                    self.timeout = timeout
                    self.responses = responses
                    self.question = None
                    self.question_text = discord.ui.TextInput(label='Question index',
                                                              placeholder=f"[A number from 0 to {len(responses)-1} ]",
                                                              # style=discord.TextStyle.short,
                                                              # required=True
                                                              )
                    self.add_item(self.question_text)

                async def on_submit(self, itx: discord.Interaction):
                    self.value = 9
                    try:
                        self.question = int(self.question_text.value)
                    except ValueError:
                        await itx.response.send_message(content=f"Couldn't add question: '{self.question_text.value}' is not an integer. "
                                                                "It has to be an index number from a response in the verification message.", ephemeral=True)
                        return
                    if self.question < 0 or self.question >= len(self.responses):
                        await itx.response.send_message(content=f"Couldn't add question: '{self.question}' is not a possible index value for removing a verification response. "
                                                                "It has to be an index number from a question in the verification message.", ephemeral=True)
                        return
                    self.value = 1
                    await itx.response.send_message(f'Removing question...', ephemeral=True, delete_after=8)
                    self.stop()

            def __init__(self, prefix, responses, msg_author, suggested_output, timeout=None):
                super().__init__()
                self.prefix = prefix
                self.value = None
                self.timeout = timeout
                self.msg_author = msg_author
                self.responses = responses
                self.suggested_output = suggested_output

        # When the confirm button is pressed, set the inner value to `True` and
            # stop the View from listening to more input.
            # We also send the user an ephemeral message that we're confirming their choice.
            @discord.ui.button(label='Send as suggested', style=discord.ButtonStyle.green)
            async def confirm(self, itx: discord.Interaction, _button: discord.ui.Button):
                self.value = 1

                await itx.channel.send(self.suggested_output)
                await itx.response.edit_message(view=None)
                self.stop()

            @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
            async def cancel(self, itx: discord.Interaction, _button: discord.ui.Button):
                self.value = 0
                await itx.response.edit_message(view=None)
                self.stop()

            @discord.ui.button(label='Add question', style=discord.ButtonStyle.blurple)
            async def add_question(self, itx: discord.Interaction, _button: discord.ui.Button):
                self.value = 10
                new_question = ConfirmSend.AddQuestion(self.responses)
                await itx.response.send_modal(new_question)
                await new_question.wait()
                if new_question.value in [None, 9]:
                    pass
                else:
                    self.responses.append(new_question.question)
                    self.suggested_output = generateOutput(self.responses, self.msg_author)
                    await itx.edit_original_response(content=self.prefix+self.suggested_output)

            @discord.ui.button(label='Remove question', style=discord.ButtonStyle.blurple)
            async def remove_question(self, itx: discord.Interaction, _button: discord.ui.Button):
                self.value = 11
                remove_question = ConfirmSend.RemoveQuestion(self.responses)
                await itx.response.send_modal(remove_question)
                await remove_question.wait()
                if remove_question.value in [None, 9]:
                    pass
                else:
                    try:
                        del self.responses[remove_question.question]
                    except IndexError:
                        await itx.edit_original_response(content=self.prefix+self.suggested_output+"\n\n***__" +
                                                         f"Couldn't add question: '{remove_question.question}' is not a possible index value for removing a verification response. "
                                                         "It has to be an index number from a question in the verification message.__***")
                        return
                    self.suggested_output = generateOutput(self.responses, self.msg_author)
                    await itx.edit_original_response(content=self.prefix+self.suggested_output)

            @discord.ui.button(label='Templates', style=discord.ButtonStyle.gray)
            async def templates(self, itx: discord.Interaction, _button: discord.ui.Button):
                self.value = 20
                await itx.response.send_message(
                    "In the 'Add Question' modal, type one of the numbers of the questions below to automatically add that one:\n" +
                    '\n'.join([f"{i}. {templates[i]}" for i in range(len(templates))]),
                    ephemeral=True
                )

        suggested_output = generateOutput(responses, message.author)
        view = ConfirmSend(warning+out, responses, message.author, suggested_output, timeout=90)
        # data = [warning, out, suggested_output]
        await itx.followup.send(warning+out+suggested_output, view=view, ephemeral=True)
        await view.wait()
        await itx.edit_original_response(view=None)







async def setup(client):
    await client.add_cog(Addons(client))

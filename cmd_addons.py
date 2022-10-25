import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *

import pymongo # for online database
from pymongo import MongoClient

import random # for picking a random call_cute quote

import asyncio # for waiting a few seconds before removing a timed-out pronoun-selection message

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
            self.headpatWait = 0
            try:
                await message.add_reaction("<:TPF_02_Pat:968285920421875744>") #headpatWait
            except discord.errors.HTTPException:
                await message.add_reaction("☺️") # relaxed

        if self.client.user.mention in message.content.split():
            msg = message.content.lower()
            if ((("cute" or "cutie" or "adorable" in msg) and "not" in msg) or "uncute" in msg) and "not uncute" not in msg:
                await message.add_reaction("<:this:960916817801535528>")
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
        if not isAdmin(itx):
            await itx.response.send_message("Hi. sorry.. It would be too powerful to let you very cool person use this command.",ephemeral=True) #todo
            return
        collection = RinaDB["guildInfo"]
        query = {"guild_id": itx.guild.id}
        guild = collection.find_one(query)
        if guild is None:
            debug("Not enough data is configured to do this action! Please fix this with `/editguildinfo`!",color="red")
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
                #todo check if pings work
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

            view = Confirm(timeout=30)
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
    @app_commands.choices(type=[
        discord.app_commands.Choice(name='Search most-used usernames', value=1),
        discord.app_commands.Choice(name='Search most-used nicknames', value=2),
    ])
    # @app_commands.describe(string="What sentence or word do you want to blacklist? (eg: 'good girl' or 'girl')")
    async def nameusage_gettop(self, itx: discord.Interaction, type: int):#, mode: int, string: str):
        await itx.response.defer(ephemeral=True)
        sections = {}
        for member in itx.guild.members:
            if type == 1:
                name = member.name
            elif type == 2 and member.nick is not None:
                name = member.nick
            else:
                continue
            name = name.lower()

            _pronouns = [
                "she","her",
                "he","him",
                "they","them",
                "it","its"
            ]
            pronouns = []
            for pronounx in _pronouns:
                for pronouny in _pronouns:
                    pronouns.append(pronounx+"/"+pronouny)
            for item in pronouns:
                name = name.replace(item, "")
            _name = ""
            for char in name:
                if char in "abcdefghijklmnopqrstuvwxyz ":
                    _name += char
            name = _name

            for section in name.split(" "):
                if section in sections:
                    sections[section] += 1
                else:
                    if len(section) < 3:
                        continue
                    if section in ["the", "god", "one"]:
                        continue
                    sections[section] = 1

        sections = sorted(sections.items(), key=lambda x:x[1], reverse=True)
        # converted_dict = dict(sections)
        # print(sections)
        pages = []
        for i in range(int(len(sections)/20+0.999)+1):
            result_page = ""
            for section in sections[0+20*i:20+20*i]:
                result_page += f"{section[1]} {section[0]}\n"
            if result_page == "":
                result_page = "_"
            pages.append(result_page)
        # print(pages)
        page = 0
        # def getEmbed(page, sections):
        #
        #     embed = discord.Embed(color=8481900, type='rich', title=f'Most-used {"user" if type==1 else "nick"}names leaderboard!')
        #     embed.add_field(name="Column 1",value=result_page)
        #     embed.add_field(name="Column 2",value=result_page2)
        #     return embed
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
        view = Pages(pages, timeout=30)
        await itx.followup.send(f"",embed=embed, view=view,ephemeral=True)
        await view.wait()
        if view.value is None:
            await itx.edit_original_response(view=None)

    @nameusage.command(name="name", description="See how often different names occur in this server")
    @app_commands.describe(name="What specific name are you looking for?")
    @app_commands.choices(type=[
        discord.app_commands.Choice(name='usernames', value=1),
        discord.app_commands.Choice(name='nicknames', value=2),
    ])
    async def nameusage_name(self, itx: discord.Interaction, name: str, type: int):
        await itx.response.defer(ephemeral=True)
        count = 0
        if type == 1:
            for member in itx.guild.members:
                if name.lower() in member.name.lower():
                    count += 1
        elif type == 2:
            for member in itx.guild.members:
                if member.nick is not None:
                    if name.lower() in member.nick.lower():
                        count += 1

        await itx.followup.send(f"I found {count} people with '{name.lower()}' in their {'user' if type==1 else 'nick'}name",ephemeral=True)


    @app_commands.command(name="roll", description="Roll a die or dice with random chance!")
    @app_commands.describe(dice="How many dice do you want to roll?",
                           faces="How many sides does every die have?",
                           mod="Do you want to add a modifier? (add 2 after rolling the dice)",
                           advanced="Roll more advanced! example: 1d20+3cs>10. Overwrites dice/faces given; 'help' for more")
    async def roll(self, itx: discord.Interaction, dice: int, faces: int, public: bool = False, mod: int = None, advanced: str = None):
        if advanced is None:
            if dice < 1 or faces < 1:
                await itx.response.send_message("You can't have negative dice/faces! Please give a number above 0",ephemeral=True)
                return
            if dice > 1000000:
                await itx.response.send_message(f"Sorry, if I let you roll `{thousandSpace(dice,separator=',')}` dice, then the universe will implode, and Rina will stop responding to commands. Please stay below 1 million dice...",ephemeral=True)
                return
            if faces > 1000000:
                await itx.response.send_message(f"Uh.. At that point, you're basically rolling a sphere. Even earth has fewer faces than `{thousandSpace(faces,separator=',')}`. Please bowl with a sphere of fewer than 1 million faces...",ephemeral=True)
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
                out = f"I rolled {thousandSpace(dice,separator=',')} {'die' if dice == 0 else 'dice'} with {thousandSpace(faces,separator=',')} face{'s'*(faces>1)}"+f" and a modifier of {thousandSpace(mod or 0,separator=',')}"*(mod is not None)+":\n" +\
                      f"With this many numbers, I've simplified it a little. You rolled `{thousandSpace(str(sum(rolls)+(mod or 0)),separator=',')}`."
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
            await itx.response.send_message("```\n" +
                                            "I rolled nothing. This feature is in development!, sorryyy" +
                                            "```",ephemeral=True)

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
    async def gen_answer(self, itx: discord.Interaction, messageid: str):
        try:
            messageid = int(messageid)
            message = await itx.channel.fetch_message(messageid)
        except discord.errors.NotFound:
            await itx.response.send_message("I couldn't find that message!",ephemeral=True)
            return
        except ValueError:
            await itx.response.send_message(f"That ('{messageid}') is not a valid message ID!",ephemeral=True)
            return

        if message is None:
            await itx.response.send_message("That message has no content?",ephemeral=True)
            return
        lines = message.content.split("\n")

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
                except ValueError: #notsure
                    end = len(verification)
                question.append(verification[start:end])
            except ValueError:
                if warning == "":
                    warning += f"Couldn't find question number for question '{number}'"
                else:
                    warning += f", '{number}'"
                if len(verification.split("\n")) == 6:
                    question.append(verification.split("\n")[number])
        if len(question) < 3:
            await itx.response.send_message("I couldn't determine/separate the question answers in this message.",ephemeral=True)
            return

        is_lgbtq = 0 # -1 = uncertain; 0 = cishet; 1 = trans
        is_trans = -1 # -1 = unconfirmed; 0 = cis; 1 = trans
        lgbtq_terms = [
            "trans",
            "m2f","f2m","mtf","ftm",
            "demi",
            "intersex",
            "nonbinary",
            "non-binary",
            "non binary",
            "questioning",
            "asexual",
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
            "nonbinary",
            "non-binary",
            "non binary",
            "fluid"]
        has_alibi = False

        out = "\n"
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
        if (("no" not in question[2]) or (len(question[2]) > 7)) and "not" not in question[2]:
            has_alibi = True

        responses = []
        if not has_alibi:
            responses.append("How did you find out about this server?")
        if is_trans == 1:
            responses.append("Since you're transgender, what makes you the happiest as your gender? What gives you the most gender euphoria?")
        elif is_lgbtq == 1:
            responses.append("Why did you decide to join a trans server instead of any general LGTBQ+ server?")
        elif is_trans != 0 or is_lgbtq == -1:
            responses.append("If you don't mind answering, what do you identify as?")

        suggested_output = ""
        if len(responses) > 0:
            out += "\n__**Suggested output:**__\n"
            suggested_output += f"""Hey there {message.author.mention},
Thank you for taking the time to answer our questions
If you don't mind, could you answer some more for us?

First of all,
{responses[0]}"""

        if len(responses) > 1:
            suggested_output += f"""

Next,
{responses[1]}"""

        if len(suggested_output) > 0:
            suggested_output += """

Once again, if you dislike answering any of these or following questions, feel free to tell me. I can give others.
Thank you in advance :)"""
        else:
            suggested_output += "\n:warning: Couldn't think of any responses."


        class ConfirmSend(discord.ui.View):
            def __init__(self, timeout=None):
                super().__init__()
                self.value = None
                self.timeout = timeout

            # When the confirm button is pressed, set the inner value to `True` and
            # stop the View from listening to more input.
            # We also send the user an ephemeral message that we're confirming their choice.
            @discord.ui.button(label='Send as suggested', style=discord.ButtonStyle.green)
            async def confirm(self, itx: discord.Interaction, _button: discord.ui.Button):
                self.value = 1
                await itx.response.edit_message(view=None)
                self.stop()

            @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
            async def cancel(self, itx: discord.Interaction, _button: discord.ui.Button):
                self.value = 0
                await itx.response.edit_message(view=None)
                self.stop()

        view = ConfirmSend(timeout=30)
        await itx.response.send_message(warning+out+suggested_output, view=view, ephemeral=True)
        await view.wait()
        if view.value is None:
            await itx.edit_original_response(view=None)
            # await asyncio.sleep(3)
            # await itx.delete_original_response()
        elif view.value == 1:
            await itx.channel.send(suggested_output)








async def setup(client):
    await client.add_cog(Addons(client))

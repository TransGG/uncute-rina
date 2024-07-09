import discord, discord.ext.commands as commands, discord.app_commands as app_commands
import random # random compliment from list, random user pronouns from their role list, and random keyboard mash
from resources.utils.utils import log_to_guild # to warn when bot can't add headpat reaction (typically cause used blocked the user)
from resources.views.compliments import ConfirmPronounsView
from resources.customs.bot import Bot


async def choose_and_send_compliment(client: Bot, itx: discord.Interaction, user: discord.User, type: str):
    quotes = {
        "fem_quotes": [
            # "Was the sun always this hot? or is it because of you?",
            # "Hey baby, are you an angel? Cuz I’m allergic to feathers.",
            # "I bet you sweat glitter.",
            "Your hair looks stunning!",
            "Being around you is like being on a happy little vacation.",
            "Good girll",
            "Who's a good girl?? You are!!",
            "Amazing! Perfect! Beautiful! How **does** she do it?!",
            "I can tell that you are a very special and talented girl!",
            "Here, have this cute sticker!",
            "Beep boop :zap: Oh no! my circuits overloaded! Her cuteness was too much for me to handle!",
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
            "You always know how to make people feel welcome and included :D",
            "Your intelligence and knowledge never cease to amaze me :O",
            "Beep boop :zap: Oh no! my circuits overloaded! His aura was so strong that I couldn't generate a cool compliment!",
            

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
            "Here, have a sticker!",
            "You always know how to put a positive spin on things!",
            "You make the world a better place just by being in it",
            "Your strength and resilience is truly inspiring.",
            "You have a contagious positive attitude that lifts up those around you.",
            "Your positive energy is infectious and makes everyone feel welcomed!",
            "You have a great sense of style and always look so put together <3",
            "You are a truly unique and wonderful person!",
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
    query = {"user": user.id}
    search: dict[str,int|list] = collection.find_one(query)
    blacklist: list = []
    if search is not None:
        try:
            blacklist += search["list"]
        except KeyError:
            pass
    query = {"user": itx.user.id}
    search = collection.find_one(query)
    if search is not None:
        try:
            blacklist += search["personal_list"]
        except KeyError:
            pass
    for string in blacklist:
        dec = 0
        for x in range(len(quotes[type])):
            if string in quotes[type][x-dec]:
                del quotes[type][x-dec]
                dec += 1
    if len(quotes[type]) == 0:
        quotes[type].append("No compliment quotes could be given... You and/or this person have blacklisted every quote.")

    base = f"{itx.user.mention} complimented {user.mention}!\n"
    cmd_mention = client.get_command_mention("developer_request")
    cmd_mention1 = client.get_command_mention("complimentblacklist")
    suffix = f""#"\n\nPlease give suggestions for compliments! DM <@262913789375021056>, make a staff ticket, or use {cmd_mention} to suggest one. Do you dislike this compliment? Use {cmd_mention1} `location:being complimented` `mode:Add` `string: ` and block specific words (or the letters "e" and "o" to block every compliment)"""
    if itx.response.is_done():
        # await itx.edit_original_response(content=base+random.choice(quotes[type]), view=None)
        await itx.followup.send(content=base+random.choice(quotes[type])+suffix, allowed_mentions=discord.AllowedMentions(everyone=False, users=[user], roles=False, replied_user=False))
    else:
        await itx.response.send_message(base+random.choice(quotes[type])+suffix, allowed_mentions=discord.AllowedMentions(everyone=False, users=[user], roles=False, replied_user=False))

async def send_confirm_gender_modal(client: Bot, itx: discord.Interaction, user: discord.User):
    # Define a simple View that gives us a confirmation menu
    view = ConfirmPronounsView(timeout=60)
    await itx.response.send_message(f"{user.mention} doesn't have any pronoun roles! Which pronouns would like to use for the compliment?", view=view,ephemeral=True)
    await view.wait()
    if view.value is None:
        await itx.edit_original_response(content=':x: Timed out...', view=None)
    else:
        await choose_and_send_compliment(client, itx, user, view.value)


class Compliments(commands.Cog):
    def __init__(self, client: Bot):
        global RinaDB
        self.client = client
        RinaDB = client.RinaDB

    @commands.Cog.listener() # Rina reflecting cuteness compliments
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if self.client.user.mention in message.content.split():
            msg = message.content.lower()
            if ((("cute" or "cutie" or "adorable" in msg) and "not" in msg) or "uncute" in msg) and "not uncute" not in msg:
                try:
                    await message.add_reaction("<:this:960916817801535528>")
                except:
                    await log_to_guild(self.client, message.guild, f'**:warning: Warning: **Couldn\'t add pat reaction to {message.jump_url}')
                    raise
            elif "cutie" in msg or "cute" in msg:
                # TODO: I should probably check people's roles for whether they have she/her and/or would like to be told they're cute. Perhaps check complimentblacklist too.
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
                    "".join(random.choice("acefgilrsuwnop" * 3 + ";;  " * 2) for _ in range(random.randint(10, 25))), # 3:2 letters to symbols
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
            elif any([x in msg for x in [
                "can i have a pat",
                "can i have a headpat",
                "can i have pat",
                "can i have headpat",
                "can you pat",
                "can you headpat",
                "can u pat",
                "can u headpat",
                "please pat",
                "pls pat",
                "please headpat",
                "pls headpat",
                "i want a pat",
                "i want a headpat",
                "i want pat",
                "i want headpat",
                "pats please",
                "headpats please",
                "pats pls",
                "headpats pls",
                "pat pls",
                "headpat pls",
                "pat please",
                "headpat please"
            ]]):
                try:
                    await message.add_reaction("<:TPF_02_Pat:968285920421875744>") #headpatWait
                except discord.errors.HTTPException:
                    try:
                        await message.channel.send("Unfortunately I can't give you a headpat (for some reason), so have this instead:\n<:TPF_02_Pat:968285920421875744>")
                    except discord.errors.Forbidden:
                        pass
            else:
                cmd_mention = self.client.get_command_mention("help")
                await message.channel.send(f"I use slash commands! Use /`command`  and see what cool things might pop up! or try {cmd_mention}\nPS: If you're trying to call me cute: no, I'm not", delete_after=8)

    @app_commands.command(name="compliment", description="Complement someone fem/masc/enby")
    @app_commands.describe(user="Who do you want to compliment?")
    async def compliment(self, itx: discord.Interaction, user: discord.User):
        # discord.User because discord.Member gets errors.TransformerError in DMs (dunno why i'm accounting for that..)
        try:
            user: discord.Member # make IDE happy, i guess
            userroles = user.roles[:]
        except AttributeError:
            await itx.response.send_message("Aw man, it seems this person isn't in the server. I wish I could compliment them but they won't be able to see it!", ephemeral=True)
            return

        roles = ["he/him", "she/her", "they/them", "it/its"]
        random.shuffle(userroles) # pick a random order for which pronoun role to pick
        for role in userroles:
            if role.name.lower() in roles:
                await choose_and_send_compliment(self.client, itx, user, role.name.lower())
                return
        await send_confirm_gender_modal(self.client, itx, user)

    @app_commands.command(name="complimentblacklist", description="If you dislike words in certain compliments")
    @app_commands.choices(location=[
        discord.app_commands.Choice(name='When complimenting someone else', value=1),
        discord.app_commands.Choice(name='When I\'m being complimented by others', value=2)
    ])
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Add a string to your compliments blacklist', value=1),
        discord.app_commands.Choice(name='Remove a string from your compliments blacklist', value=2),
        discord.app_commands.Choice(name='Check your blacklisted strings', value=3)
    ])
    @app_commands.describe(
        location="Blacklist when giving compliments / when receiving compliments from others",
        string  ="What sentence or word do you want to blacklist? (eg: 'good girl' or 'girl')")
    async def complimentblacklist(self, itx: discord.Interaction, location: int, mode: int, string: str = None):
        if location == 1:
            db_location = "personal_list"
        elif location == 2:
            db_location = "list"
        else:
            raise NotImplementedError("This shouldn't happen.")
        print(db_location)
        if mode == 1: # add an item to the blacklist
            if string is None:
                await itx.response.send_message("With this command, you can blacklist a section of text in compliments. "
                                                "For example, if you don't like being called 'Good girl', you can "
                                                "blacklist this compliment by blacklisting 'good' or 'girl'. \n"
                                                "Or if you don't like hugging people, you can blacklist 'hug'.\n"
                                                "Note: it's case sensitive", ephemeral=True)
                return
            if len(string) > 150:
                await itx.response.send_message("Please make strings shorter than 150 characters...",ephemeral=True)
                return
            collection = RinaDB["complimentblacklist"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                blacklist = []
            else:
                blacklist = search.get(db_location, [])
            blacklist.append(string)
            collection.update_one(query, {"$set":{db_location:blacklist}}, upsert=True)
            await itx.response.send_message(f"Successfully added {repr(string)} to your blacklist. ({len(blacklist)} item{'s'*(len(blacklist)!=1)} in your blacklist now)",ephemeral=True)

        elif mode == 2: # Remove item from black list
            if string is None:
                cmd_mention = self.client.get_command_mention("complimentblacklist")
                await itx.response.send_message(f"Type the id of the string you want to remove. To find the id, type {cmd_mention} `mode:Check`.", ephemeral=True)
                return
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
            blacklist = search.get(db_location, [])

            try:
                del blacklist[string]
            except IndexError:
                cmd_mention = self.client.get_command_mention("complimentblacklist")
                await itx.response.send_message(f"Couldn't delete that ID, because there isn't any item on your list with that ID.. Use {cmd_mention} `mode:Check` to see the IDs assigned to each item on your list",ephemeral=True)
                return
            collection.update_one(query, {"$set":{db_location:blacklist}}, upsert=True)
            await itx.response.send_message(f"Successfully removed `{string}` from your blacklist. Your blacklist now contains {len(blacklist)} string{'s'*(len(blacklist)!=1)}.", ephemeral=True)
        
        elif mode == 3: # check
            collection = RinaDB["complimentblacklist"]
            query = {"user": itx.user.id}
            search: dict[str,int|list] = collection.find_one(query)
            if search is None:
                await itx.response.send_message("There are no strings in your blacklist, so.. nothing to list here....",ephemeral=True)
                return
            blacklist = search.get(db_location, [])
            length = len(blacklist)

            ans = []
            for id in range(length):
                ans.append(f"`{id}`: {blacklist[id]}")
            ans = '\n'.join(ans)
            await itx.response.send_message(f"Found {length} string{'s'*(length!=1)}:\n{ans}",ephemeral=True)


async def setup(client):
    await client.add_cog(Compliments(client))

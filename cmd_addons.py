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

    @app_commands.command(name="say",description="Force Rina to repeat your wise words")
    @app_commands.describe(text="What will you make Rina repeat?")
    async def say(self, itx: discord.Interaction, text: str):
        if not isAdmin(itx):
            await itx.response.send_message("Hi. sorry.. It would be too powerful to let you very cool person use this command.",ephemeral=True) #todo
            return
        collection = RinaDB["guildInfo"]
        query = {"guild_id": itx.guild.id}
        guild = collection.find(query)
        try:
            guild = guild[0]
        except IndexError:
            debug("Not enough data is configured to do this action! Please fix this with `/editguildinfo`!",color="red")
            return
        try:
            vcLog      = guild["vcLog"]
            logChannel = itx.guild.get_channel(vcLog)
            await logChannel.send(f"{itx.user.nick or itx.user.name} ({itx.user.id}) said a message using Rina: {text}", allowed_mentions=discord.AllowedMentions.none())
            text = text.replace("[[\\n]]","\n").replace("[[del]]","")
            await itx.channel.send(f"{text}", allowed_mentions=discord.AllowedMentions.none())
        except:
            await itx.response.send_message("Oops. Something went wrong!",ephemeral=True)
            raise
        await itx.response.send_message("Successfully sent!", ephemeral=True)


    @app_commands.command(name="compliment", description="Complement someone fem/masc/enby")
    @app_commands.describe(user="Who do you want to compliment?")
    async def compliment(self, itx: discord.Interaction, user: discord.User):
        async def call(itx, user, type):
            quotes = {
                "fem_quotes" : [
                    "Was the sun always this hot? or is it because of you?",
                    "Ooh you look like a good candidate for my pet blahaj!",
                ],
                "masc_quotes" : [
                    "",
                ],
                "they_quotes" : [
                    "",
                ],
                "it_quotes" : [
                    "",
                ],
                "unisex_quotes" : [ #unisex quotes are added to each of the other quotes later on.
                    "_Let me just hide this here-_ hey wait, are you looking?!",
                    "Would you like a hug?",
                    "Would you like to walk in the park with me? I gotta walk my catgirls",
                    "morb"

                ]
            }
            type = {
                "she/her"   : "fem_quotes",
                "he/him"    : "masc_quotes",
                "they/them" : "enby_quotes",
                "it/its"    : "enby_quotes",
                "unisex"    : "unisex_quotes", #todo
            }[type]

            for x in quotes:
                if x == "unisex_quotes":
                    continue
                else:
                    quotes[x] += quotes["unisex_quotes"]

            if itx.response.is_done():
                await itx.edit_original_response(content=random.choice(quotes[type]), view=None)
            else:
                await itx.response.send_message(random.choice(quotes[type]), allowed_mentions=discord.AllowedMentions.none())

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
                async def feminine(self, interaction: discord.Interaction, button: discord.ui.Button):
                    self.value = "she/her"
                    await interaction.response.send_message('Selected She/Her pronouns for compliment', ephemeral=True)
                    self.stop()

                @discord.ui.button(label='He/Him', style=discord.ButtonStyle.green)
                async def masculine(self, interaction: discord.Interaction, button: discord.ui.Button):
                    self.value = "he/him"
                    await interaction.response.send_message('Selected He/Him pronouns for the compliment', ephemeral=True)
                    self.stop()

                @discord.ui.button(label='They/Them', style=discord.ButtonStyle.green)
                async def enby_them(self, interaction: discord.Interaction, button: discord.ui.Button):
                    self.value = "they/them"
                    await interaction.response.send_message('Selected They/Them pronouns for the compliment', ephemeral=True)
                    self.stop()

                @discord.ui.button(label='It/Its', style=discord.ButtonStyle.green)
                async def enby_its(self, interaction: discord.Interaction, button: discord.ui.Button):
                    self.value = "it/its"
                    await interaction.response.send_message('Selected It/Its pronouns for the compliment', ephemeral=True)
                    self.stop()

                @discord.ui.button(label='Unisex/Unknown', style=discord.ButtonStyle.grey)
                async def unisex(self, interaction: discord.Interaction, button: discord.ui.Button):
                    self.value = "unisex"
                    await interaction.response.send_message('Selected Unisex/Unknown gender for the compliment', ephemeral=True)
                    self.stop()

            view = Confirm(timeout=30)
            await itx.response.send_message("This person doesn't have any pronoun roles! Which pronouns would like to use for the compliment?", view=view)
            await view.wait()
            if view.value is None:
                await itx.edit_original_response(content=':x: Timed out...', view=None)
                await asyncio.sleep(3)
                await itx.delete_original_response()
            else:
                await call(itx, user, view.value)

        roles = ["he/him","she/her","they/them","it/its"]
        for role in user.roles:
            if role.name.lower() in random.shuffle(roles): # pick a random order for which pronoun role to pick
                await call(itx, user, role.name.lower())
                return
        await confirm_gender()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        #random cool commands
        if self.client.user.mention in message.content.split():
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

async def setup(client):
    await client.add_cog(Addons(client))

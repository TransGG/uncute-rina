import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *

import pymongo # for online database
from pymongo import MongoClient
mongoURI = open("mongo.txt","r").read()
cluster = MongoClient(mongoURI)
RinaDB = cluster["Rina"]

class Pronouns(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.ctx_menu_user = app_commands.ContextMenu(
            name='Pronouns',
            callback=self.pronounsCtxUser,
        )
        self.ctx_menu_message = app_commands.ContextMenu(
            name='Pronouns',
            callback=self.pronounsCtxMessage,
        )
        self.client.tree.add_command(self.ctx_menu_user)
        self.client.tree.add_command(self.ctx_menu_message)

    @app_commands.command(name="addpronoun",description="Let others know what pronouns you like to use!")
    @app_commands.describe(pronoun="What pronoun do you want to use (example: she/her, or :a)")
    async def addPronoun(self, itx: discord.Interaction, pronoun: str):
        warning = ""
        if not ("/" in pronoun or pronoun.startswith(":")):
            warning = "Warning: Others may not be able to know what you mean with these pronouns (it doesn't use an `x/y` or `:x` format)\n"
        collection = RinaDB["members"]
        query = {"member_id": itx.user.id}
        data = collection.find(query)
        try:
            pronouns = data[0]['pronouns']
        except IndexError:
            #see if this user already has data, if not, add empty
            pronouns = []
        if pronoun in pronouns:
            await itx.response.send_message("You have already added this pronoun! You can't really put multiple of the same pronouns, that's be unnecessary..",ephemeral=True)
            return
        pronouns.append(pronoun)
        collection.update_one(query, {"$set":{f"pronouns":pronouns}}, upsert=True)

        await itx.response.send_message(warning+f"Successfully added `{pronoun}`. Use `/pronouns <user:yourself>` to see your custom pronouns, and use `/removepronoun <pronoun>` to remove one",ephemeral=True)

    @app_commands.command(name="removepronoun",description="Remove one of your prevously added pronouns!")
    @app_commands.describe(pronoun="What pronoun do you want to remove (example: she/her, or :a)")
    async def removePronoun(self, itx: discord.Interaction, pronoun: str):
        collection = RinaDB["members"]
        query = {"member_id": itx.user.id}
        data = collection.find(query)
        try:
            pronouns = data[0]['pronouns']
        except IndexError:
            #see if this user already has data, if not, add empty
            await itx.response.send_message("You haven't added pronouns yet! Use `/addpronoun <pronoun>` to add one!",ephemeral=True)
            return
        if pronoun not in pronouns:
            await itx.response.send_message("You haven't added this pronoun yet, so I can't really remove it either! Use `/addpronoun <pronoun>` to add one, or `/pronouns <user:yourself>` to see what pronouns you have added", ephemeral=True)
            return
        pronouns.remove(pronoun)
        collection.update_one(query, {"$set":{f"pronouns":pronouns}}, upsert=True)
        await itx.response.send_message(f"Removed `{pronoun}` successfully!", ephemeral=True)

    async def getPronouns(self, itx, user):
        collection = RinaDB["members"]
        query = {"member_id": user.id}
        data = collection.find(query)
        noPronouns = False
        warning = ""
        try:
            pronouns = data[0]['pronouns']
        except IndexError:
            #see if this user already has data, if not, add empty
            pronouns = []
            noPronouns = True
            warning = "\nThis person hasn't added custom pronouns yet! (They need to use `/addpronoun <pronoun>` to add one)"
        else:
            if len(pronouns) == 0:
                noPronouns = True
                warning = "\nThis person hasn't added custom pronouns. (They need to use `/addpronoun <pronoun>` to add one)"

        list = []
        for pronoun in pronouns:
            if pronoun.startswith(":"):
                p = pronoun[:-1]
                pronoun = pronoun +" = "+', '.join([p, p, p+"'s", p+"'s", p+"self"])
            list.append("-> " + pronoun)

        roles = []
        loweredList = [i.lower() for i in list]
        pronounRoles = ["he/him", "she/her", "they/them", "it/its"]
        for role in user.roles:
            if role.name.lower() == "other" and len(list) == 0:
                roles.append("This person has the 'Other' role, so ask them if they have different pronouns.")
            if role.name.lower() in pronounRoles and role.name.lower() not in loweredList:
                roles.append("=> " + role.name+" (from role)")
        list += roles

        if len(list) == 0:
            await itx.response.send_message("This person doesn't have any pronoun roles and hasn't added any custom pronouns. Ask them to add a role in #self-roles, or to use `/addpronoun <pronoun>`\nThey might also have pronouns mentioned in their About Me.. I can't see that sadly, so you'd have to check yourself.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        else:
            await itx.response.send_message(f"{user.nick or user.name} ({user.id}) uses these pronouns:\n"+ '\n'.join(list)+warning, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="pronouns",description="Get someone's pronouns!")
    @app_commands.describe(user="Whose pronouns do you want to know?")
    async def pronounsCommand(self, itx: discord.Interaction, user: discord.Member):
        await self.getPronouns(itx, user)

    async def pronounsCtxUser(self, itx: discord.Interaction, user: discord.User):
        await self.getPronouns(itx, user)

    async def pronounsCtxMessage(self, itx: discord.Interaction, message: discord.Message):
        await self.getPronouns(itx, message.author)

async def setup(client):
    # client.add_command(getMemberData)
    await client.add_cog(Pronouns(client))

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
        await itx.response.send_message(warning+f"Successfully added `{pronoun}`. Use `/pronouns <user>` to see this person's pronouns",ephemeral=True)

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

    @app_commands.command(name="pronouns",description="Get someone's pronouns!")
    @app_commands.describe(user="Whose pronouns do you want to know?")
    async def pronouns(self, itx: discord.Interaction, user: discord.Member):
        collection = RinaDB["members"]
        query = {"member_id": user.id}
        data = collection.find(query)
        try:
            pronouns = data[0]['pronouns']
        except IndexError:
            #see if this user already has data, if not, add empty
            await itx.response.send_message("This person hasn't added pronouns yet! (They need to use `/addpronoun <pronoun>` to add one)",ephemeral=True)
            return
        if len(pronouns) == 0:
            await itx.response.send_message("This person hasn't added pronouns yet. (They need to use `/addpronoun <pronoun>` to add one)",ephemeral=True)
            return

        list = []
        for pronoun in pronouns:
            if pronoun.startswith(":"):
                p = pronoun[:-1]
                pronoun = pronoun +" = "+', '.join([p, p, p+"'s", p+"'s", p+"self"])
            list.append("-> " + pronoun)

        roles = []
        loweredList = [i.lower() for i in list]
        pronounRoles = ["he/him", "she/her", "they/them"]
        for role in user.roles:
            if role.name.lower() == "other" and len(list) == 0:
                roles.append("This person has the 'Other' role, so ask them if they have different pronouns.")
            if role.name.lower() in pronounRoles and role.name.lower() not in loweredList:
                roles.append("=> " + role.name+" (from role)")
        list += roles
        await itx.response.send_message(f"{user.nick or user.name} ({user.id}) uses these pronouns:\n"+ '\n'.join(list), ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

async def setup(client):
    # client.add_command(getMemberData)
    await client.add_cog(Pronouns(client))

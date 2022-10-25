import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *

import pymongo # for online database
from pymongo import MongoClient


class Pronouns(commands.Cog):
    def __init__(self, client):
        global RinaDB
        RinaDB = client.RinaDB
        self.client = client
        self.ctx_menu_user = app_commands.ContextMenu(
            name='Pronouns',
            callback=self.pronouns_ctx_user,
        )
        self.ctx_menu_message = app_commands.ContextMenu(
            name='Pronouns',
            callback=self.pronouns_ctx_message,
        )
        self.client.tree.add_command(self.ctx_menu_user)
        self.client.tree.add_command(self.ctx_menu_message)

    @app_commands.command(name="addpronoun",description="Let others know what pronouns you like to use!")
    @app_commands.describe(pronoun="What pronoun do you want to use (example: she/her, or :a)")
    async def add_pronoun(self, itx: discord.Interaction, pronoun: str):
        warning = ""
        if not ("/" in pronoun or pronoun.startswith(":")):
            warning = "Warning: Others may not be able to know what you mean with these pronouns (it doesn't use an `x/y` or `:x` format)\n"
        collection = RinaDB["members"]
        query = {"member_id": itx.user.id}
        data = collection.find_one(query)
        if data is None:
            #see if this user already has data, if not, add empty
            pronouns = []
        else:
            pronouns = data['pronouns']
        if pronoun in pronouns:
            await itx.response.send_message("You have already added this pronoun! You can't really put multiple of the same pronouns, that's be unnecessary..",ephemeral=True)
            return
        if len(pronouns) > 20:
            await itx.response.send_message("Having this many pronouns will make it difficult for others to pick one! Remove a few before adding a new one!",ephemeral=True)
            return
        if len(pronoun) > 90:
            await itx.response.send_message("Please make your pronouns shorter in length, or use this command multiple times / split up the text",ephemeral=True)
            return
        pronouns.append(pronoun)
        collection.update_one(query, {"$set":{f"pronouns":pronouns}}, upsert=True)
        cmd_mention = self.client.getCommandMention("pronouns")
        cmd_mention_del = self.client.getCommandMention("removepronoun")
        await itx.response.send_message(warning+f"Successfully added `{pronoun}`. Use {cmd_mention}` <user:yourself>` to see your custom pronouns, and use {cmd_mention_del}` <pronoun>` to remove one",ephemeral=True)

    @app_commands.command(name="removepronoun",description="Remove one of your prevously added pronouns!")
    @app_commands.describe(pronoun="What pronoun do you want to remove (example: she/her, or :a)")
    async def remove_pronoun(self, itx: discord.Interaction, pronoun: str):
        collection = RinaDB["members"]
        query = {"member_id": itx.user.id}
        data = collection.find_one(query)
        if data is None:
            #see if this user already has data, if not, add empty
            cmd_mention = self.client.getCommandMention("addpronoun")
            await itx.response.send_message(f"You haven't added pronouns yet! Use {cmd_mention}` <pronoun>` to add one!",ephemeral=True)
            return
        pronouns = data['pronouns']
        if pronoun not in pronouns:
            if isStaff(itx):
                # made possible with the annoying user '27', alt of Error, trying to break the bot :\
                try:
                    member_id, pronoun = pronoun.split(" | ",1)
                    query = {"member_id": int(member_id)}
                    data = collection.find_one(query)
                    if data is None:
                        #see if this user already has data, if not, add empty
                        cmd_mention = self.client.getCommandMention("addpronoun")
                        await itx.response.send_message(f"This person hasn't added pronouns yet! Tell them to use {cmd_mention}` <pronoun>` to add one!",ephemeral=True)
                        return
                    pronouns = data['pronouns']
                    del pronouns[int(pronoun)-1]
                except ValueError:
                    cmd_mention = self.client.getCommandMention("removepronoun")
                    await itx.response.send_message(f"If you are staff, and wanna remove a pronoun, then type \"pronoun:USERID | PronounYouWannaRemove\" like {cmd_mention} pronoun:4491185284728472 | 1\nThe pronoun/item you wanna remove will be in order of the pronouns, starting at 1 at the top. So if someone has 3 pronouns and you wanna remove the second one, type '2'.",ephemeral=True)
                    return
            else:
                cmd_mention = self.client.getCommandMention("addpronoun")
                await itx.response.send_message(f"You haven't added this pronoun yet, so I can't really remove it either! Use `/addpronoun <pronoun>` to add one, or `{cmd_mention} <user:yourself>` to see what pronouns you have added", ephemeral=True)
                return
        else:
            pronouns.remove(pronoun)
        collection.update_one(query, {"$set":{f"pronouns":pronouns}}, upsert=True)
        await itx.response.send_message(f"Removed `{pronoun}` successfully!", ephemeral=True)

    async def get_pronouns(self, itx, user):
        collection = RinaDB["members"]
        query = {"member_id": user.id}
        data = collection.find_one(query)
        warning = ""
        if data is None:
            pronouns = []
        else:
            pronouns = data['pronouns']
        if len(pronouns) == 0:
            cmd_mention = self.client.getCommandMention("addpronoun")
            warning = f"\nThis person hasn't added custom pronouns yet! (They need to use {cmd_mention}` <pronoun>` to add one)"

        list = []
        for pronoun in pronouns:
            if pronoun.startswith(":"):
                p = pronoun[:-1]
                pronoun = pronoun + " = " + ', '.join([p, p, p+"'s", p+"'s", p+"self"])
            elif len(pronoun) > 500:
                pronoun = pronoun[:500]
            list.append("-> " + pronoun)

        if type(user) == discord.User:
            await itx.response.send_message("This person isn't in the server (anymore), so I can't see their pronouns from their roles!\n" +
                                            "So if they had custom pronouns, here's their list:\n"+'\n'.join(list)+warning, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
            return

        roles = []
        lowered_list = [i.lower() for i in list]
        pronoun_roles = ["he/him", "she/her", "they/them", "it/its"]
        for role in user.roles:
            if role.name.lower() == "other" and len(list) == 0:
                roles.append("This person has the 'Other' role, so ask them if they have different pronouns.")
            if role.name.lower() in pronoun_roles and role.name.lower() not in lowered_list:
                roles.append("=> " + role.name+" (from role)")
        list += roles

        if len(list) == 0:
            cmd_mention = self.client.getCommandMention("addpronoun")
            await itx.response.send_message(f"This person doesn't have any pronoun roles and hasn't added any custom pronouns. Ask them to add a role in #self-roles, or to use {cmd_mention}` <pronoun>`\nThey might also have pronouns mentioned in their About Me.. I can't see that sadly, so you'd have to check yourself.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        else:
            await itx.response.send_message(f"{user.nick or user.name} ({user.id}) uses these pronouns:\n" + '\n'.join(list)+warning, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="pronouns",description="Get someone's pronouns!")
    @app_commands.describe(user="Whose pronouns do you want to know?")
    async def pronouns_command(self, itx: discord.Interaction, user: discord.Member):
        await self.get_pronouns(itx, user)

    async def pronouns_ctx_user(self, itx: discord.Interaction, user: discord.User):
        await self.get_pronouns(itx, user)

    async def pronouns_ctx_message(self, itx: discord.Interaction, message: discord.Message):
        await self.get_pronouns(itx, message.author)

async def setup(client):
    # client.add_command(getMemberData)
    await client.add_cog(Pronouns(client))

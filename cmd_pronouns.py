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
            cmd_mention = self.client.getCommandMention("pronouns")
            warning = f"\nThis person hasn't added custom pronouns yet! (They need to use {cmd_mention}` mode:Add argument:<pronoun>` to add one)"

        list = []
        for pronoun in pronouns:
            if pronoun.startswith(":"):
                p = pronoun[1:]
                if p[-1] == "s":
                    pronoun = pronoun + " = " + ', '.join([p, p, p + "'", p + "'", p + "self"])
                else:
                    pronoun = pronoun + " = " + ', '.join([p, p, p+"'s", p+"'s", p+"self"])
            elif len(pronoun) > 500:
                pronoun = pronoun[:500]
            list.append("-> " + pronoun)

        if type(user) is discord.User:
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
            cmd_mention = self.client.getCommandMention("pronouns")
            await itx.response.send_message(f"This person doesn't have any pronoun roles and hasn't added any custom pronouns. Ask them to add a role in #self-roles, or to use {cmd_mention}` mode:Add argument:<pronoun>`\nThey might also have pronouns mentioned in their About Me.. I can't see that sadly, so you'd have to check yourself.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())
        else:
            await itx.response.send_message(f"{user.nick or user.name} ({user.id}) uses these pronouns:\n" + '\n'.join(list)+warning, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    async def remove_pronoun_autocomplete(self, itx: discord.Interaction, current: str):
        if itx.namespace.mode == 1:
            results = []
            for member in itx.guild.members:
                if member.nick is not None:
                    nick = current in member.nick
                else:
                    nick = False
                if current in member.name or nick:
                    name = member.name + "    #"+member.discriminator
                    if member.nick is not None:
                        name = f"{member.nick}     ({member})"
                    results.append(app_commands.Choice(name=name, value=member.mention))
                if len(results) >= 10:
                    return results
            return results
        if itx.namespace.mode == 2:
            def get_pronouns():
                part = [
                    "She",
                    "Her",
                    "He",
                    "Him",
                    "They",
                    "Them",
                    "It",
                    "Its",
                ]
                part_loose = [
                    "Any",
                    "Any pronouns",
                    "Ask",
                    "Ask for pronouns",
                    "Hee/hee"
                ]
                results = []
                sections = current.split("/")
                if len(sections) < 2:
                    suggestions = part_loose
                    for x in part:
                        for y in part:
                            suggestions.append(x+"/"+y)
                    for suggestion in suggestions:
                        if current in suggestion:
                            results.append(suggestion)
                for pronoun_part in part_loose:
                    if current in pronoun_part:
                        results.append(pronoun_part)
                for pronoun_part in part:
                    if sections[-1].lower() in pronoun_part.lower():
                        suggestion = "/".join(sections[:-1])+"/"+pronoun_part
                        results.append(suggestion)
                results.append(current)
                return results

            _results = get_pronouns()
            _temp = []
            results = []

            for result in _results:
                if result not in _temp:
                    results.append(app_commands.Choice(name=result, value=result))
                    _temp.append(result)
                if len(results) >= 10:
                    break
            return results
        if itx.namespace.mode == 3:
            staff_overwrite = False
            data = None
            if isStaff(itx) and " |" in current:
                sections = current.split(" |")
                if len(sections) == 2:
                    try:
                        user_id = int(sections[0])
                        collection = RinaDB["members"]
                        query = {"member_id": user_id}
                        data = collection.find_one(query)
                        staff_overwrite = True
                        current = sections[1].strip()
                    except ValueError:
                        pass
            if not staff_overwrite:
                # find results in database
                collection = RinaDB["members"]
                query = {"member_id": itx.user.id}
                data = collection.find_one(query)
            if data is None:
                return []
            else:
                pronouns = data['pronouns']

            if len(pronouns) == 0:
                return []
            if staff_overwrite:
                return [
                    app_commands.Choice(name=pronouns[index], value=str(index))
                    for index in range(len(pronouns)) if pronouns[index].lower().startswith(current.lower())
                ]
            return [
                app_commands.Choice(name=pronoun, value=pronoun)
                for pronoun in pronouns if pronoun.lower().startswith(current.lower())
            ]

    @app_commands.command(name="pronouns",description="Get someone's pronouns!")
    @app_commands.describe(argument="Check a user or add/remove a pronoun here!")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Check: mention the user', value=1),
        discord.app_commands.Choice(name='Add pronoun: Add your custom pronoun (eg: she/her or :Alex)', value=2),
        discord.app_commands.Choice(name='Remove pronoun: Type the pronoun you wanna remove', value=3),
        discord.app_commands.Choice(name='Help', value=4),
    ])
    @app_commands.autocomplete(argument=remove_pronoun_autocomplete)
    async def pronouns_command(self, itx: discord.Interaction, mode: int, argument: str = None):
        if mode == 1:
            if argument is not None:
                user = argument
                for i in "<@>":
                    user = user.replace(i,"")
                try:
                    user_id = int(user)
                except ValueError:
                    await itx.response.send_message("You need to give a valid user to get their pronouns!", ephemeral=True)
                    return
                user = itx.guild.get_member(user_id)
                if user is None:
                    user = self.client.get_user(user_id)
                    if user is None:
                        await itx.response.send_message("I couldn't find a user with that ID! Did you mention the right person? Perhaps they're not in the server anymore", ephemeral=True)
            else:
                user = itx.user
            await self.get_pronouns(itx, user)
        elif mode == 2:
            if argument is None:
                await itx.response.send("You can add pronouns here. For example, \"she/her\", or \":Alex\". For more information about pronouns, "
                                        "or if you want to try out your own pronouns, check out <https://en.pronouns.page/pronouns>",ephemeral=True)
                return
            pronoun = argument
            warning = ""
            if not ("/" in pronoun or pronoun.startswith(":")):
                warning = "Warning: Others may not be able to know what you mean with these pronouns (it doesn't use an `x/y` or `:x` format)\n"
            collection = RinaDB["members"]
            query = {"member_id": itx.user.id}
            data = collection.find_one(query)
            if data is None:
                # see if this user already has data, if not, add empty
                pronouns = []
            else:
                pronouns = data['pronouns']
            if pronoun in pronouns:
                await itx.response.send_message(
                    "You have already added this pronoun! You can't really put multiple of the same pronouns, that's be unnecessary..",
                    ephemeral=True)
                return
            if len(pronouns) > 20:
                await itx.response.send_message(
                    "Having this many pronouns will make it difficult for others to pick one! Remove a few before adding a new one!",
                    ephemeral=True)
                return
            if len(pronoun) > 90:
                await itx.response.send_message(
                    "Please make your pronouns shorter in length, or use this command multiple times / split up the text",
                    ephemeral=True)
                return
            if pronoun.startswith(":") and len(pronoun) < 2:
                await itx.response.send_message("Please make your ':' pronoun more than 0 letters long...",
                                                ephemeral=True)
                return
            pronouns.append(pronoun)
            collection.update_one(query, {"$set": {f"pronouns": pronouns}}, upsert=True)
            cmd_mention = self.client.getCommandMention("pronouns")
            await itx.response.send_message(
                warning + f"Successfully added `{pronoun}`. Use {cmd_mention}` mode:Check` to see your custom pronouns, and use {cmd_mention}` mode:Remove argument:pronoun` to remove one",
                ephemeral=True)
        elif mode == 3:
            collection = RinaDB["members"]
            query = {"member_id": itx.user.id}
            data = collection.find_one(query)
            if data is None:
                # see if this user already has data, if not, add empty
                cmd_mention = self.client.getCommandMention("pronouns")
                await itx.response.send_message(
                    f"You haven't added pronouns yet! Use {cmd_mention}` mode:Add argument:<pronoun>` to add one!", ephemeral=True)
                return

            if argument is None:
                cmd_mention = self.client.getCommandMention("pronouns")
                await itx.response.send_message(f"You can remove pronouns with this command. Check the pronouns you have with the {cmd_mention}` mode:Check` command."
                                                f"If you have a pronoun you want to remove, write the pronoun in the 'argument' section of the command.",ephemeral=True)
                return
            pronoun = argument
            pronouns = data['pronouns']
            if pronoun not in pronouns:
                if isStaff(itx):
                    # made possible with the annoying user '27', alt of Error, trying to break the bot :\
                    try:
                        member_id, pronoun = pronoun.split(" | ", 1)
                        query = {"member_id": int(member_id)}
                        data = collection.find_one(query)
                        if data is None:
                            # see if this user already has data, if not, add empty
                            cmd_mention = self.client.getCommandMention("pronouns")
                            await itx.response.send_message(
                                f"This person hasn't added pronouns yet! Tell them to use {cmd_mention}` mode:Add <pronoun>` to add one!",
                                ephemeral=True)
                            return
                        pronouns = data['pronouns']
                        del pronouns[int(pronoun) - 1]
                    except ValueError:
                        cmd_mention = self.client.getCommandMention("pronouns")
                        await itx.response.send_message(
                            f"If you are staff, and wanna remove a pronoun, then type `argument:USERID | PronounYouWannaRemove` like {cmd_mention}` mode:Remove argument:4491185284728472 | 1`\nThe pronoun/item you wanna remove will be in order of the pronouns, starting at 1 at the top. So if someone has 3 pronouns and you wanna remove the second one, type '2'.",
                            ephemeral=True)
                        return
                else:
                    cmd_mention = self.client.getCommandMention("pronouns")
                    await itx.response.send_message(
                        f"You haven't added this pronoun yet, so I can't really remove it either! Use {cmd_mention}` mode:Add argument:<pronoun>` to add one, or `{cmd_mention} mode:Check` to see what pronouns you have added",
                        ephemeral=True)
                    return
            else:
                pronouns.remove(pronoun)
            collection.update_one(query, {"$set": {f"pronouns": pronouns}}, upsert=True)
            await itx.response.send_message(f"Removed `{pronoun}` successfully!", ephemeral=True)
        elif mode == 4:
            await itx.response.send_message("Oops, I forgot to add anything for this command! Ask Mia how it works eheh... \n    MysticMia#7612",ephemeral=True)

    async def pronouns_ctx_user(self, itx: discord.Interaction, user: discord.User):
        await self.get_pronouns(itx, user)

    async def pronouns_ctx_message(self, itx: discord.Interaction, message: discord.Message):
        await self.get_pronouns(itx, message.author)

async def setup(client):
    # client.add_command(getMemberData)
    await client.add_cog(Pronouns(client))

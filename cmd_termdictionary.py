import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *
import requests #grab from en.pronouns.page api (search)
import json # turn api request into dictionary
import re #use regex to remove API hyperlink definitions: {#Ace=asexual}

import pymongo # for online database
from pymongo import MongoClient

class TermDictionary(commands.Cog):
    def __init__(self, client):
        global RinaDB
        RinaDB = client.RinaDB
        self.client = client

    # @dictionary.autocomplete('term')
    async def dictionary_autocomplete(self, itx: discord.Interaction, current: str):
        def simplify(q):
            if type(q) is str:
                return q.lower().replace(" ","").replace("-","").replace("_","")
            if type(q) is list:
                return [text.lower().replace(" ","").replace("-","").replace("_","") for text in q]
        terms = []
        if current == '':
            return []

        # find results in custom dictionary
        collection = RinaDB["termDictionary"]
        query = {"synonyms": simplify(current)}
        search = collection.find(query)
        for item in search:
            if simplify(current) in simplify(item["synonyms"]):
                terms.append(item["term"])

        # get list of choices from online
        response_api = requests.get(f'https://en.pronouns.page/api/terms/search/{current}').text
        data = json.loads(response_api)
        # find exact results online
        for item in data:
            if item['term'].split("|")[0] in terms:
                continue
            if simplify(current) in simplify(item['term'].split('|')):
                terms.append(item['term'].split('|')[0])

        # then, find whichever other terms are there (append / last) online
        for item in data:
            if item['term'].split("|")[0] in terms:
                continue
            terms.append(item['term'].split("|")[0])
        # limit choices to the first 7
        terms = terms[:7]

        return [
            app_commands.Choice(name=term, value=term)
            for term in terms
        ]

    @app_commands.command(name="dictionary",description="Look for the definition of a trans-related term!")
    @app_commands.describe(term="This is your search query. What do you want to look for?",
                           source="Where do you want to search? Online? Custom Dictionary? Or just leave it default..",
                           public="Do you want to share the search results with the rest of the channel? (True=yes)")
    @app_commands.choices(source=[
            discord.app_commands.Choice(name='Search from whichever has an answer', value=1),
            discord.app_commands.Choice(name='Search from custom dictionary', value=3),
            discord.app_commands.Choice(name='Search from en.pronouns.page', value=2),
        ])
    @app_commands.autocomplete(term=dictionary_autocomplete)
    async def dictionary(self, itx: discord.Interaction, term: str, public: bool = False, source: int = 1):
        def simplify(q):
            if type(q) is str:
                return q.lower().replace(" ","").replace("-","").replace("_","")
            if type(q) is list:
                return [text.lower().replace(" ","").replace("-","").replace("_","") for text in q]
        # test if mode has been left unset or if mode has been selected: decides whether or not to move to the online API search or not.
        if source == 1 or source == 3:
            collection = RinaDB["termDictionary"]
            query = {"synonyms": term.lower()}
            search = collection.find(query)

            result = False
            results = []
            result_str = ""
            for item in search:
                if simplify(term) in simplify(item["synonyms"]):
                    results.append([item["term"],item["definition"]])
                    result = True
            if result:
                result_str += f"I found {len(results)} result{'s'*(len(results)>1)} for '{term}' in our dictionary:\n"
                for x in results:
                    result_str += f"> **{x[0]}**: {x[1]}\n"
            else:
                # if mode has been left unset, it will move to the online API dictionary to look for a definition there.
                # Otherwise, it will return the 'not found' result of the term, and end the function.
                if source == 1:
                    source = 4
                #public = False
                else:
                    cmd_mention = self.client.getCommandMention("dictionary_staff define")
                    result_str += f"No information found for '{term}'...\nIf you would like to add a term, message a staff member (to use {cmd_mention})"
                    # debug(f"{itx.user.name} ({itx.user.id}) searched for '{term}' in the terminology dictionary (specifically in here), but it yielded no results. Maybe we should add this term to the /dictionary command",color='light red')
                    cmd_mention = self.client.getCommandMention("dictionary")
                    await logMsg(itx.guild,f"**!! Alert:** {itx.user.name} ({itx.user.id}) searched for '{term}' in the terminology dictionary (specifically in here), but it yielded no results. Maybe we should add this term to the {cmd_mention} command")
            if len(result_str.split("\n")) > 3 and public:
                public = False
                result_str += "\nDidn't send your message as public cause it would be spammy, having this many results."
            if len(result_str) > 1999:
                result_str = f"Your search ({term}) returned too many results (discord has a 2000-character message length D:). (Please ask staff to fix this (synonyms and stuff).)"
                # debug(f"{itx.user.name} ({itx.user.id})'s dictionary search ('{term}') gave back a result that was larger than 2000 characters! Results:'\n"+', '.join(results),color="red")
                await logMsg(itx.guild,f"**!! Warning:** {itx.user.name} ({itx.user.id})'s dictionary search ('{term}') gave back a result that was larger than 2000 characters!'")
        if source == 2 or source == 4:
            response_api = requests.get(f'https://en.pronouns.page/api/terms/search/{term}').text
            data = json.loads(response_api)
            # if len(data) == 0:
            #     await itx.response.send_message(f"No results found for '{term}' on en.pronouns.page... :(",ephemeral=not public)
            #     return

            # edit definitions to hide links to other pages:
            search = []
            for item in data:
                item_db = item['definition']
                while item['definition'] == item_db:
                    replacement = re.search("(?<==).+?(?=})",item['definition'])
                    if replacement is not None:
                        item['definition'] = re.sub("{(#.+?=).+?}", replacement.group(), item['definition'],1)
                    if item['definition'] == item_db: #if nothing changed:
                        break
                    item_db = item['definition']
                while item['definition'] == item_db:
                    replacement = re.search("(?<={).+?(?=})",item['definition'])
                    if replacement is not None:
                        item['definition'] = re.sub("{.+?}", replacement.group(), item['definition'],1)
                    if item['definition'] == item_db: #if nothing changed:
                        break
                    item_db = item['definition']
                search.append(item)

            # if one of the search results matches exactly with the search, give that definition
            results = []
            for item in search:
                if simplify(term) in simplify(item['term'].split('|')):
                    results.append(item)
            if len(results) > 0:
                result_str = f"I found {len(results)} exact result{'s'*(len(results)!=1)} for '{term}' on en.pronouns.page! \n"
                for item in results:
                    result_str += f"> **{', '.join(item['term'].split('|'))}:** {item['definition']}\n"
                result_str += f"{len(search)-len(results)} other non-exact results found."*((len(search)-len(results)) > 0)
                if len(result_str) > 1999:
                    result_str = f"Your search ('{term}') returned a too-long result! (discord has a 2000-character message length D:). To still let you get better results, I've rewritten the terms so you might be able to look for a more specific one:"
                    for item in results:
                        result_str += f"> {', '.join(item['term'].split('|'))}\n"
                await itx.response.send_message(result_str,ephemeral=not public, suppress_embeds=True)
                return

            # if search doesn't exactly match with a result / synonym
            result_str = f"I found {len(search)} result{'s'*(len(results)!=1)} for '{term}' on en.pronouns.page! "
            if len(search) > 25:
                result_str += "Here is a list to make your search more specific:\n"
                results = []
                for item in search:
                    temp = item['term']
                    if "|" in temp:
                        temp = temp.split("|")[0]
                    results.append(temp)
                result_str += ', '.join(results)
                public = False
            elif len(search) > 2:
                result_str += "Here is a list to make your search more specific:\n"
                results = []
                for item in search:
                    if "|" in item['term']:
                        temp = "- __"  + item['term'].split("|")[0] + "__"
                        temp += " ("  + ', '.join(item['term'].split("|")[1:]) + ")"
                    else:
                        temp = "- __" + item['term'] + "__"
                    results.append(temp)
                result_str += '\n'.join(results)
                public = False
            elif len(search) > 0:
                result_str += "\n"
                for item in search:
                    result_str += f"> **{', '.join(item['term'].split('|'))}:** {item['definition']}\n"
            else:
                result_str = f"I didn't find any results for '{term}' on en.pronouns.page!"
                if source == 4:
                    result_str = f"I didn't find any results for '{term}' online or in our fancy dictionary"
                    # debug(f"{itx.user.name} ({itx.user.id}) searched for '{term}' in the terminology dictionary and online (en.pronouns.page), but there were no results. Maybe we should add this term to the /dictionary command (/define)",color='light red')
                    cmd_mention_dict = self.client.getCommandMention("dictionary")
                    cmd_mention_def = self.client.getCommandMention("dictionary_staff define")
                    await logMsg(itx.guild,f"**!! Alert:** {itx.user.name} ({itx.user.id}) searched for '{term}' in the terminology dictionary and online (en.pronouns.page), but there were no results. Maybe we should add this term to the {cmd_mention_dict} command ({cmd_mention_def})")
            msg_length = len(result_str)
            if msg_length > 1999:
                public = False
                result_str = f"Your search ('{term}') returned too many results ({len(search)} in total!) (discord has a 2000-character message length, and this message was {msg_length} characters D:). Please search more specifically.\n\
Here is a link for expanded info on each term: <https://en.pronouns.page/dictionary/terminology#{term.lower()}>"
            #print(response_api.status_code)
        else:
            result_str = "" # to make my IDE happy.
        await itx.response.send_message(result_str, ephemeral=not public, suppress_embeds=True)

    admin = app_commands.Group(name='dictionary_staff', description='Change custom entries in the dictionary')

    @admin.command(name="define",description="Add a dictionary entry for a word!")                                            #
    @app_commands.describe(term="This is the main word for the dictionary entry: Egg, Hormone Replacement Therapy (HRT), (case sens.)",
                           definition="Give this term a definition",
                           synonyms="Add synonyms (SEPARATE WITH \", \")")
    async def define(self, itx: discord.Interaction, term: str, definition: str, synonyms: str = ""):
        if not isStaff(itx):
            await itx.response.send_message("You can't add words to the dictionary without staff roles!", ephemeral=True)
            return
        def simplify(q):
            if type(q) is str:
                return q.lower().replace(" ","").replace("-","").replace("_","")
            if type(q) is list:
                return [text.lower().replace(" ","").replace("-","").replace("_","") for text in q]
        # Test if this term is already defined in this dictionary.
        collection = RinaDB["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is not None:
            cmd_mention = self.client.getCommandMention("dictionary")
            await itx.response.send_message(f"You have already previously defined this term (try to find it with {cmd_mention}).", ephemeral=True)
            return

        # Test if a synonym is already used before
        if synonyms != "":
            synonyms = synonyms.split(", ")
            synonyms = [simplify(i) for i in synonyms]
        else:
            synonyms = []
        if simplify(term) not in synonyms:
            synonyms.append(simplify(term))

        query = {"synonyms": {"$in": synonyms}}
        synonym_overlap = collection.find(query)
        warnings = ""
        for overlap in synonym_overlap:
            warnings += f"You have already given a synonym before in {overlap['term']}.\n"

        # Add term to dictionary
        post = {"term": term, "definition": definition, "synonyms": synonyms}
        collection.insert_one(post)

        await logMsg(itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) added the dictionary definition of '{term}' and set it to '{definition}', with synonyms: {synonyms}")
        await itx.response.send_message(warnings+f"Successfully added '{term}' to the dictionary (with synonyms: {synonyms}): {definition}", ephemeral=True)

    @admin.command(name="redefine",description="Edit a dictionary entry for a word!")
    @app_commands.describe(term="This is the main word for the dictionary entry (case sens.) Example: Egg, Hormone Replacement Therapy (HRT), etc.",
                           definition="Redefine this definition")
    async def redefine(self, itx: discord.Interaction, term: str, definition: str):
        if not isStaff(itx):
            await itx.response.send_message("You can't add words to the dictionary without staff roles!", ephemeral=True)
            return
        collection = RinaDB["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is None:
            cmd_mention = self.client.getCommandMention("dictionary_staff define")
            await itx.response.send_message(f"This term hasn't been added to the dictionary yet, and thus cannot be redefined! Use {cmd_mention}.",ephemeral=True)
            return
        collection.update_one(query, {"$set":{"definition":definition}})

        await logMsg(itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) changed the dictionary definition of '{term}' to '{definition}'")
        await itx.response.send_message(f"Successfully redefined '{term}'", ephemeral=True)

    @admin.command(name="undefine",description="Add a dictionary entry for a word!")
    @app_commands.describe(term="What word do you need to undefine (case sensitive). Example: Egg, Hormone Replacement Therapy (HRT), etc")
    async def undefine(self, itx: discord.Interaction, term: str):
        if not isStaff(itx):
            await itx.response.send_message("You can't remove words to the dictionary without staff roles!", ephemeral=True)
            return
        collection = RinaDB["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is None:
            await itx.response.send_message("This term hasn't been added to the dictionary yet, and thus cannot be undefined!",ephemeral=True)
            return
        await logMsg(itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) undefined the dictionary definition of '{term}' from '{search['definition']}' with synonyms: {search['synonyms']}")
        collection.delete_one(query)


        await itx.response.send_message(f"Successfully undefined '{term}'", ephemeral=True)

    @admin.command(name="editsynonym",description="Add a synonym to a previously defined word")
    @app_commands.describe(term="This is the main word for the dictionary entry (case sens.): Egg, Hormone Transfer Therapy, etc",
                           mode="Add or remove a synonym?",
                           synonym="Which synonym to remove?")
    @app_commands.choices(mode=[
            discord.app_commands.Choice(name='Add a synonym', value=1),
            discord.app_commands.Choice(name='Remove a synonym', value=2),
        ])
    async def edit_synonym(self, itx: discord.Interaction, term: str, mode: int, synonym: str):
        if not isStaff(itx):
            await itx.response.send_message("You can't add synonyms to the dictionary without staff roles!", ephemeral=True)
            return
        collection = RinaDB["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is None:
            cmd_mention = self.client.getCommandMention("dictionary_staff define")
            await itx.response.send_message(f"This term hasn't been added to the dictionary yet, and thus cannot get new synonyms! Use {cmd_mention}.",ephemeral=True)
            return

        if mode == 1:
            synonyms = search["synonyms"]
            if synonym.lower() in synonyms:
                await itx.response.send_message("This term already has this synonym!", ephemeral=True)
                return
            synonyms.append(synonym.lower())
            collection.update_one(query, {"$set":{"synonyms":synonyms}}, upsert=True)
            await logMsg(itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) added synonym '{synonym}' the dictionary definition of '{term}'")
            await itx.response.send_message("Successfully added synonym", ephemeral=True)
        if mode == 2:
            synonyms = search["synonyms"]
            if synonym.lower() not in synonyms:
                await itx.response.send_message("This term doesn't have this synonym!", ephemeral=True)
                return
            synonyms.remove(synonym.lower())
            if len(synonyms) < 1:
                await itx.response.send_message("You can't remove all the synonyms to a term! Then you can't find it in the dictionary anymore :P. First, add a synonym before removing one.", ephemeral=True)
                return
            collection.update_one(query, {"$set":{"synonyms":synonyms}}, upsert=True)
            await logMsg(itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) removed synonym '{synonym}' the dictionary definition of '{term}'")
            await itx.response.send_message("Successfully removed synonym", ephemeral=True)

async def setup(client):
    await client.add_cog(TermDictionary(client))
    # await client.add_cog(DictionaryGroup(client))

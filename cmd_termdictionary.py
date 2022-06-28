import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *
import requests #grab from en.pronouns.page api (search)
import json # turn api request into dictionary
import re #use regex to remove API hyperlink definitions: {#Ace=asexual}

mongoURI = open("mongo.txt","r").read()
cluster = MongoClient(mongoURI)
RinaDB = cluster["Rina"]

class TermDictionary(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="dictionary",description="Look for the definition of a trans-related term!")
    @app_commands.describe(term="This is your search query. What do you want to look for?",
                           source="Where do you want to search? Online? Custom Dictionary? Or just leave it default..",
                           public="Do you want to share the search results with the rest of the channel? (True=yes)")
    @app_commands.choices(source=[
            discord.app_commands.Choice(name='Search from whichever has an answer', value=1),
            discord.app_commands.Choice(name='Search from custom dictionary', value=3),
            discord.app_commands.Choice(name='Search from en.pronouns.page', value=2),
        ])
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
            resultStr = ""
            for item in search:
                if simplify(term) in simplify(item["synonyms"]):
                    overlaps = []
                    overlapper = ""
                    # for term1 in toneIndicators:
                    #     if term == term1:
                    #         continue
                    #     for def in toneIndicators[term1]:
                    #         if def in toneIndicators[term]:
                    #             overlapper = def
                    #             overlaps.append(term1)
                    #             break
                    results.append([item["term"],item["definition"],overlapper,overlaps])
                    result = True
            if result == True:
                resultStr += f"I found {len(results)} result{'s'*(len(results)>1)} for '{term}' in our dictionary:\n"
                for x in results:
                    resultStr += f"> {x[0]}: {x[1]}\n"
            else:
                # if mode has been left unset, it will move to the online API dictionary to look for a definition there.
                # Otherwise, it will return the 'not found' result of the term, and end the function.
                if source == 1:
                    source = 4
                #public = False
                else:
                    resultStr += f"No information found for '{term}'...\nIf you would like to add a term, message a staff member (to use /define)"
                    debug(f"{itx.user.name} ({itx.user.id}) searched for '{term}' in the terminology dictionary (specifically in here), but it yielded no results. Maybe we should add this term to the /dictionary command",color='light red')
                    await logMsg(itx.guild,f"**!! Alert:** {itx.user.name} ({itx.user.id}) searched for '{term}' in the terminology dictionary (specifically in here), but it yielded no results. Maybe we should add this term to the /dictionary command")
            if len(resultStr.split("\n")) > 3 and public:
                public = False
                resultStr += "\nDidn't send your message as public cause it would be spammy, having this many results."
            if len(resultStr) > 1999:
                resultStr = f"Your search ({term}) returned too many results (discord has a 2000-character message length D:). (Please ask staff to fix this (synonyms and stuff).)"
                debug(f"{itx.user.name} ({itx.user.id})'s dictionary search ('{term}') gave back a result that was larger than 2000 characters! Results:'\n"+', '.join(results),color="red")
                await logMmsg(itx.guild,f"**!! Warning:** {itx.user.name} ({itx.user.id})'s dictionary search ('{term}') gave back a result that was larger than 2000 characters!'")
        if source == 2 or source == 4:
            response_API = requests.get(f'https://en.pronouns.page/api/terms/search/{term}').text
            data = json.loads(response_API)
            if len(data) == 0:
                await itx.response.send_message(f"No results found for '{term}' on en.pronouns.page... :(",ephemeral=(public==False))
                return

            # edit definitions to hide links to other pages:
            search = []
            for item in data:
                itemDB = item['definition']
                while item['definition'] == itemDB:
                    replacement = re.search("(?<==).+?(?=})",item['definition'])
                    if replacement is not None:
                        item['definition'] = re.sub("{(#.+?=).+?}", replacement.group(), item['definition'],1)
                    if item['definition'] == itemDB: #if nothing changed:
                        break
                    itemDB = item['definition']
                while item['definition'] == itemDB:
                    replacement = re.search("(?<={).+?(?=})",item['definition'])
                    if replacement is not None:
                        item['definition'] = re.sub("{.+?}", replacement.group(), item['definition'],1)
                    if item['definition'] == itemDB: #if nothing changed:
                        break
                    itemDB = item['definition']
                search.append(item)


            # if one of the search results matches exactly with the search, give that definition
            results = []
            for item in search:
                if simplify(term) in simplify(item['term'].split('|')):
                    results.append(item)
            if len(results) > 0:
                resultStr = f"I found {len(results)} exact result{'s'*(len(results)!=1)} for '{term}' on en.pronouns.page! \n"
                for item in results:
                    resultStr += f"> **{', '.join(item['term'].split('|'))}:** {item['definition']}\n"
                resultStr += f"{len(search)-len(results)} other non-exact results found."*((len(search)-len(results))>0)
                if len(resultStr) > 1999:
                    resultStr = f"Your search ('{term}') returned a too-long result! (discord has a 2000-character message length D:). To still let you get better results, I've rewritten the terms so you might be able to look for a more specific one:"
                    for item in results:
                        resultStr += f"> {', '.join(item['term'].split('|'))}\n"
                await itx.response.send_message(resultStr,ephemeral=(public==False), suppress_embeds=True)
                return

            # if search doesn't exactly match with a result / synonym
            resultStr = f"I found {len(search)} result{'s'*(len(results)!=1)} for '{term}' on en.pronouns.page! "
            if len(search) > 25:
                resultStr += "Here is a list to make your search more specific:\n"
                results = []
                for item in search:
                    temp =  item['term']
                    if "|" in temp:
                        temp = temp.split("|")[0]
                    results.append(temp)
                resultStr += ', '.join(results)
                public = False
            elif len(search) > 2:
                resultStr += "Here is a list to make your search more specific:\n"
                results = []
                for item in search:
                    temp = ""
                    if "|" in item['term']:
                        temp = "- __"  +   item['term'].split("|")[0]   +  "__"
                        temp += " ("  +  ', '.join(item['term'].split("|")[1:])  +  ")"
                    else:
                        temp = "- __" + item['term'] + "__"
                    results.append(temp)
                resultStr += '\n'.join(results)
                public = False
            elif len(search) > 0:
                resultStr += "\n"
                for item in search:
                    resultStr += item["definition"]+"\n"
                    resultStr += f"> **{', '.join(item['term'].split('|'))}:** {item['definition']}\n"
            else:
                resultStr = f"I didn't find any results for '{term}' on en.pronouns.page!"
                if source == 4:
                    debug(f"{itx.user.name} ({itx.user.id}) searched for '{term}' in the terminology dictionary and online (en.pronouns.page), but there were no results. Maybe we should add this term to the /dictionary command (/define)",color='light red')
                    await logMsg(itx.guild,f"**!! Alert:** {itx.user.name} ({itx.user.id}) searched for '{term}' in the terminology dictionary and online (en.pronouns.page), but there were no results. Maybe we should add this term to the /dictionary command (/define)")
            msgLength = len(resultStr)
            if msgLength > 1999:
                public = False
                resultStr = f"Your search ('{term}') returned too many results ({len(search)} in total!) (discord has a 2000-character message length, and this message was {msgLength} characters D:). Please search more specifically.\n\
Here is a link for expanded info on each term: <https://en.pronouns.page/dictionary/terminology#{term.lower()}>"
            #print(response_API.status_code)
        await itx.response.send_message(resultStr,ephemeral=(public==False), suppress_embeds=True)

    @app_commands.command(name="define",description="Add a dictionary entry for a word!")                                            #
    @app_commands.describe(term="This is the main word for the dictionary entry: Egg, Hormone Replacement Therapy (HRT), (case sens.)",
                           definition="Give this term a definition",
                           synonyms="Add synonyms (SEPARATE WITH \", \")")
    async def define(self, itx: discord.Interaction, term: str, definition: str, synonyms: str = ""):
        if not isStaff(itx):
            await itx.response.send_message("You can't add words to the dictionary without staff roles!", ephemeral=True)
            return
        # Test if this term is already defined in this dictionary.
        collection = RinaDB["termDictionary"]
        query = {"term": term}
        search = collection.find(query)
        try:
            search = search[0]
            await itx.response.send_message("You have already previously defined this term (try to find it with /dictionary).", ephemeral=True)
            return
        except:
            pass

        # Test if a synonym is already used before
        if synonyms != "":
            synonyms = synonyms.split(", ")
            synonyms = [i.lower() for i in synonyms]
        else:
            synonyms = []
        if term.lower() not in synonyms:
            synonyms.append(term.lower())

        query = {"synonyms": {"$in": synonyms }}
        synonymOverlap = collection.find(query)
        warnings = ""
        for overlap in synonymOverlap:
            warnings += f"You have already given a synonym before in {overlap['term']}.\n"

        # Add term to dictionary
        post = {"term": term, "definition": definition, "synonyms": synonyms}
        collection.insert_one(post)

        await logMsg(itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) added the dictionary definition of '{term}' and set it to '{definition}', with synonyms: {synonyms}")
        await itx.response.send_message(warnings+f"Successfully added '{term}' to the dictionary (with synonyms: {synonyms}): {definition}", ephemeral=True)

    @app_commands.command(name="redefine",description="Edit a dictionary entry for a word!")
    @app_commands.describe(term="This is the main word for the dictionary entry (case sens.) Example: Egg, Hormone Replacement Therapy (HRT), etc.",
                           definition="Redefine this definition")
    async def redefine(self, itx: discord.Interaction, term: str, definition: str):
        if not isStaff(itx):
            await itx.response.send_message("You can't add words to the dictionary without staff roles!", ephemeral=True)
            return
        collection = RinaDB["termDictionary"]
        query = {"term": term}
        search = collection.find(query)
        try:
            search = search[0]
        except IndexError:
            await itx.response.send_message("This term hasn't been added to the dictionary yet, and thus cannot be redefined! Use /define.",ephemeral=True)
            return
        collection.update_one(query, {"$set":{"definition":definition}})

        await logMsg(itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) changed the dictionary definition of '{term}' to '{definition}'")
        await itx.response.send_message(f"Successfully redefined '{term}'", ephemeral=True)

    @app_commands.command(name="undefine",description="Add a dictionary entry for a word!")
    @app_commands.describe(term="What word do you need to undefine (case sensitive). Example: Egg, Hormone Replacement Therapy (HRT), etc")
    async def undefine(self, itx: discord.Interaction, term: str):
        if not isStaff(itx):
            await itx.response.send_message("You can't remove words to the dictionary without staff roles!", ephemeral=True)
            return
        collection = RinaDB["termDictionary"]
        query = {"term": term}
        search = collection.find(query)
        try:
            search = search[0]
        except IndexError:
            await itx.response.send_message("This term hasn't been added to the dictionary yet, and thus cannot be undefined!",ephemeral=True)
            return
        await logMsg(itx.guild, f"{itx.user.nick or itx.user.name} ({itx.user.id}) undefined the dictionary definition of '{term}' from '{search['definition']}' with synonyms: {search['synonyms']}")
        collection.delete_one(query)


        await itx.response.send_message(f"Successfully undefined '{term}'", ephemeral=True)

    @app_commands.command(name="editsynonym",description="Add a synonym to a previously defined word")
    @app_commands.describe(term="This is the main word for the dictionary entry (case sens.): Egg, Hormone Transfer Therapy, etc",
                           mode="Add or remove a synonym?",
                           synonym="Which synonym to remove?")
    @app_commands.choices(mode=[
            discord.app_commands.Choice(name='Add a synonym', value=1),
            discord.app_commands.Choice(name='Remove a synonym', value=2),
        ])
    async def editSynonym(self, itx: discord.Interaction, term: str, mode: int, synonym: str):
        if not isStaff(itx):
            await itx.response.send_message("You can't add synonyms to the dictionary without staff roles!", ephemeral=True)
            return
        collection = RinaDB["termDictionary"]
        query = {"term": term}
        search = collection.find(query)
        try:
            search = search[0]
        except IndexError:
            await itx.response.send_message("This term hasn't been added to the dictionary yet, and thus cannot be redefined! Use /define.",ephemeral=True)
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

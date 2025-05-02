import json
import re  # to parse and remove https:/pronouns.page/ in-text page linking
from datetime import datetime
import requests  # for API calls to dictionary apis

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.termdictionary.dictionary_data import DictionaryData
from extensions.termdictionary.dictionary_sources import DictionarySources
from resources.checks import is_staff_check  # for staff dictionary commands
from resources.customs import Bot
# for logging custom dictionary changes, or when a search query returns nothing or >2000 characters
from resources.utils.utils import log_to_guild

from extensions.termdictionary.views import DictionaryApi_PageView, UrbanDictionary_PageView


del_separators_table = str.maketrans({" ": "", "-": "", "_": ""})


def simplify(q: str | list[str]) -> str | list[str]:
    if type(q) is str:
        return q.lower().translate(del_separators_table)
    if type(q) is list:
        return [text.lower().translate(del_separators_table)
                for text in q]
    raise NotImplementedError()


async def dictionary_autocomplete(itx: discord.Interaction[Bot], current: str):

    terms = []
    if current == '':
        return []

    # find results in custom dictionary
    collection = itx.client.rina_db["termDictionary"]
    query = {"synonyms": simplify(current)}
    search = collection.find(query)
    for item in search:
        if simplify(current) in simplify(item["synonyms"]):
            terms.append(item["term"])

    # get list of choices from online
    response_api = requests.get(f'https://en.pronouns.page/api/terms/search/{current}').text
    data = json.loads(response_api)
    # find exact results online
    if len(data) != 0:
        for item in data:
            if item['term'].split("|")[0] not in terms:
                if simplify(current) in simplify(item['term'].split('|')):
                    terms.append(item['term'].split('|')[0])

        # then, find whichever other terms are there (append / last) online
        for item in data:
            if item['term'].split("|")[0] not in terms:
                terms.append(item['term'].split("|")[0])

    # Next to that, also add generic dictionary options if your query exactly matches that of the dictionary
    # but only if there aren't already 7 responses; to prevent extra loading time
    if len(terms) < 7:
        response_api = requests.get(f'https://api.dictionaryapi.dev/api/v2/entries/en/{current}').text
        data = json.loads(response_api)
        if type(data) is not dict:
            for result in data:
                if result["word"].capitalize() not in terms:
                    terms.append(result["word"].capitalize())
    # same for Urban Dictionary, searching only if there are no results for the others
    if len(terms) < 1:
        response_api = requests.get(f'https://api.urbandictionary.com/v0/define?term={current}').text
        data = json.loads(response_api)['list']
        for result in data:
            if result["word"].capitalize() + " ([from UD])" not in terms:
                terms.append(result["word"].capitalize() + " ([from UD])")

    # limit choices to the first 7
    terms = terms[:7]

    return [
        app_commands.Choice(name=term, value=term.replace(" ([from UD])", ""))
        for term in terms
    ]


async def _get_custom_dictionary_output(
        client: Bot, term: str
):
    collection = client.async_rina_db["termDictionary"]
    query = {"synonyms": term.lower()}
    search = collection.find(query)
    results: list[tuple[str, str]] = []
    async for item in search:
        item: DictionaryData
        if simplify(term) in simplify(item["synonyms"]):
            results.append((item["term"], item["definition"]))
    if not results:
        cmd_mention_define = client.get_command_mention(
            "dictionary_staff define")
        raise KeyError(
            f"No information found for '{term}' in the custom dictionary.\n"
            f"If you would like to add a term, message a staff member "
            f"(to use {cmd_mention_define})"
        )

    result_str = (f"I found {len(results)} result{'s' * (len(results) > 1)} "
                  f"for '{term}' in our dictionary:\n")
    for result_term, result_definition in results:
        result_str += f"> **{result_term}**: {result_definition}\n"

    long_line = False
    exceeding_line = False
    if len(result_str.split("\n")) > 3:
        long_line = True
        result_str += "\nDidn't send your message as public cause it would be spammy, having this many results."
    if len(result_str) > 1999:
        exceeding_line = True
        result_str = (
            f"Your search ({term}) returned too many results (discord has a 2000-character "
            f"message length D:). (Please ask staff to fix this (synonyms and stuff).)")
    return result_str, long_line, exceeding_line


async def _get_pronouns_page_output(public, result_str,
                                    source, term):
    http_safe_term = term.lower().replace("/", " ").replace("%", " ")
    response_api = requests.get(
        f'https://en.pronouns.page/api/terms/search/{http_safe_term}'
    ).text
    data = json.loads(response_api)
    if len(data) == 0:
        if source == 3:
            source = 5
        else:
            result_str = f"I didn't find any results for '{term}' on en.pronouns.page"
            public = False

    # edit definitions to hide links to other pages:
    else:
        search = []
        for item in data:
            item_db = item['definition']
            while item['definition'] == item_db:
                replacement = re.search("(?<==).+?(?=})",
                                        item['definition'])
                if replacement is not None:
                    item['definition'] = re.sub("{(#.+?=).+?}",
                                                replacement.group(),
                                                item['definition'], 1)
                if item['definition'] == item_db:  # if nothing changed:
                    break
                item_db = item['definition']
            while item['definition'] == item_db:
                replacement = re.search("(?<={).+?(?=})",
                                        item['definition'])
                if replacement is not None:
                    item['definition'] = re.sub("{.+?}",
                                                replacement.group(),
                                                item['definition'], 1)
                if item['definition'] == item_db:  # if nothing changed:
                    break
                item_db = item['definition']
            search.append(item)

        # if one of the search results matches exactly with the search, give that definition
        results: list[dict] = []
        for item in search:
            if simplify(term) in simplify(item['term'].split('|')):
                results.append(item)
        if len(results) > 0:
            result_str = (
                f"I found {len(results)} exact result{'s' * (len(results) != 1)} for "
                f"'{term}' on en.pronouns.page! \n")
            for item in results:
                result_str += f"> **{', '.join(item['term'].split('|'))}:** {item['definition']}\n"
            if (len(search) - len(results)) > 0:
                result_str += f"{len(search) - len(results)} other non-exact results found."
            if len(result_str) > 1999:
                result_str = (
                    f"Your search ('{term}') returned a too-long "
                    f"result! (discord has a 2000-character message "
                    f"length D:). To still let you get better results, "
                    f"I've rewritten the terms so you might be able "
                    f"to look for a more specific one:"
                )
                for item in results:
                    result_str += f"> {', '.join(item['term'].split('|'))}\n"
            raise OverflowError(result_str)

        # if search doesn't exactly match with a result / synonym
        result_str = (
            f"I found {len(search)} result{'s' * (len(results) != 1)} for "
            f"'{term}' on en.pronouns.page! ")
        if len(search) > 25:
            result_str += "Here is a list to make your search more specific:\n"
            results: list[str] = []
            for item in search:
                temp = item['term']
                if "|" in temp:
                    temp = temp.split("|")[0]
                results.append(temp)
            result_str += ', '.join(results)
            public = False
        elif len(search) > 2:
            result_str += "Here is a list to make your search more specific:\n"
            results: list[str] = []
            for item in search:
                if "|" in item['term']:
                    temp = "- __" + item['term'].split("|")[0] + "__"
                    temp += " (" + ', '.join(
                        item['term'].split("|")[1:]) + ")"
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
                source = 6
        msg_length = len(result_str)
        if msg_length > 1999:
            public = False
            result_str = (
                f"Your search ('{term}') returned too many results ({len(search)} in total!) "
                f"(discord has a 2000-character message length, and this message "
                f"was {msg_length} characters D:). Please search more specifically.\n"
                f"    Here is a link for expanded info on each term: "
                f"<https://en.pronouns.page/dictionary/terminology#{term.lower()}>")
    return public, result_str, source


async def _get_urban_dictionary_pages(data):
    pages = []
    page = 0
    for result in data:
        embed = discord.Embed(color=8481900,
                              title=f"__{result['word'].capitalize()}__",
                              description=result['definition'],
                              url=result['permalink'])
        post_date = int(
            datetime.strptime(
                result['written_on'][:-1],
                # "2009-03-04T01:16:08.000Z" ([:-1] to remove Z at end)
                "%Y-%m-%dT%H:%M:%S.%f"
            ).timestamp()
        )
        warning = ""
        if len(result['example']) > 800:
            warning = "... (shortened due to size)"
        embed.add_field(name="Example",
                        value=f"{result['example'][:800]}{warning}\n\n"
                              f"{result['thumbs_up']}:thumbsup: :thumbsdown: {result['thumbs_down']}\n"
                              f"Sent by {result['author']} on <t:{post_date}:d> at "
                              f"<t:{post_date}:T> (<t:{post_date}:R>)",
                        inline=False)
        pages.append(embed)
    return page, pages


def _get_dictionary_api_pages(data, results):
    for result in data:
        meanings = []
        synonyms = []
        antonyms = []
        for meaning in result["meanings"]:
            meaning_list = [meaning['partOfSpeech']]
            # **verb**:
            # meaning one is very useful
            # meaning two is not as useful
            for definition in meaning["definitions"]:
                meaning_list.append("- " + definition['definition'])
                for synonym in definition['synonyms']:
                    if synonym not in synonyms:
                        synonyms.append(synonym)
                for antonym in definition['antonyms']:
                    if antonym not in antonyms:
                        antonyms.append(antonym)
            for synonym in meaning['synonyms']:
                if synonym not in synonyms:
                    synonyms.append(synonym)
            for antonym in meaning['antonyms']:
                if antonym not in antonyms:
                    antonyms.append(antonym)
            meanings.append(meaning_list)

        results.append([
            # train
            result["word"],
            # [  ["noun", "- Hello there this is 1", "- number two"], ["verb", ...], [...]  ]
            meanings,
            ', '.join(synonyms),
            ', '.join(antonyms),
            '\n'.join(result["sourceUrls"])
        ])
    pages = []
    pages_detailed = []
    page = 0
    for result in results:
        result_id = 0
        page_detailed = []
        embed = discord.Embed(color=8481900,
                              title=f"__{result[0].capitalize()}__")
        for meaning_index in range(len(result[1])):
            _part = result[1][meaning_index][1:]
            part = []
            for definition in _part:
                page_detailed.append(
                    [result_id, f"__{result[0].capitalize()}__",
                     result[1][meaning_index][0].capitalize(),
                     definition])
                part.append(f"`{result_id}`" + definition)
                result_id += 1
            value = '\n'.join(part)
            if len(value) > 995:  # limit to 1024 chars in Value field
                value = value[:995] + "... (shortened due to size)"
            embed.add_field(name=result[1][meaning_index][0].capitalize(),
                            value=value,
                            inline=False)
        if len(result[2]) > 0:
            embed.add_field(name="Synonyms",
                            value=f"`{result_id}`" + result[2],
                            inline=False)
            page_detailed.append(
                [result_id, f"__{result[0].capitalize()}__", "Synonyms",
                 result[2]])
            result_id += 1
        if len(result[3]) > 0:
            embed.add_field(name="Antonyms",
                            value=f"`{result_id}`" + result[3],
                            inline=False)
            page_detailed.append(
                [result_id, f"__{result[0].capitalize()}__", "Antonyms",
                 result[3]])
            result_id += 1
        if len(result[4]) > 0:
            embed.add_field(name=f"`{result_id}`-" + "More info:",
                            value=result[4],
                            inline=False)
            page_detailed.append(
                [result_id, f"__{result[0].capitalize()}__", "More info:",
                 result[4]])
            result_id += 1
        pages.append(embed)
        pages_detailed.append(page_detailed)
        # [meaning, [type, definition1, definition2], synonym, antonym, sources]
    return page, pages, pages_detailed


class TermDictionary(commands.Cog):
    def __init__(self):
        pass

    @app_commands.command(name="dictionary",
                          description="Look for terms in online dictionaries!")
    @app_commands.describe(term="This is your search query. What do you want "
                                "to look for?",
                           source="Where do you want to search? Online? "
                                  "Custom Dictionary? Or just leave it "
                                  "default..",
                           public="Do you want to share the search results "
                                  "with the rest of the channel? (True=yes)")
    @app_commands.choices(source=[
        discord.app_commands.Choice(
            name='Search from whichever has an answer',
            value=DictionarySources.All.value
        ),
        discord.app_commands.Choice(
            name='Search from custom dictionary',
            value=DictionarySources.CustomDictionary.value
        ),
        discord.app_commands.Choice(
            name='Search from en.pronouns.page',
            value=DictionarySources.PronounsPage.value
        ),
        discord.app_commands.Choice(
            name='Search from dictionaryapi.dev',
            value=DictionarySources.DictionaryApi.value
        ),
        discord.app_commands.Choice(
            name='Search from urbandictionary.com',
            value=DictionarySources.UrbanDictionary.value
        ),
    ])
    @app_commands.autocomplete(term=dictionary_autocomplete)
    async def dictionary(
            self,
            itx: discord.Interaction[Bot],
            term: str,
            public: bool = False,
            source: DictionarySources = DictionarySources.All,
    ):
        # todo: rewrite this whole command.
        #  - Make the sources an enum.
        #  - Allow going to the next source if you're not satisfied with
        #    a dictionary's result.
        #  - Perhaps make a view with multi-selectable options for which
        #    sources you would want to search through
        #    though this sounds like a bad idea Xd.
        #  - Should also have an integration without custom dictionary
        #    that users can install.
        #  - Make all pageviews into actual PageView views.
        itx.response: discord.InteractionResponse  # noqa
        # test if mode has been left unset or if mode has been selected: decides whether to move to the
        # online API search or not.
        result_str = ""
        # to make my IDE happy. Will still crash on discord if it actually tries to send it tho: 'Empty message'
        results: list
        if (source == DictionarySources.All
                or source == DictionarySources.CustomDictionary):
            public, result_str, source = await _get_custom_dictionary_output(
                itx.client, term
            )
        if ((source == DictionarySources.All and not result_str)
                or source == DictionarySources.PronounsPage):
            try:
                public, result_str, source = \
                    await _get_pronouns_page_output(
                        public, result_str, source, term
                    )
            except OverflowError as ex:
                await itx.reponse.send_message(str(ex), ephemeral=True,
                                               suppress_embeds=True)
        if source == 5 or source == 6:
            await itx.response.defer(ephemeral=True)
            response_api = requests.get(
                f'https://api.dictionaryapi.dev/api/v2/entries/en/{term.lower().replace("/", "%2F")}').text
            try:
                data: any = json.loads(response_api)
            except json.decoder.JSONDecodeError:
                # if a bad api response is given, catch and continue as if empty results
                data: dict = {}  # specify class to make IDE happy
            results = []
            if type(data) is dict:
                if source == 5:
                    source = 7
                else:
                    result_str = f"I didn't find any results for '{term}' on dictionaryapi.dev!"
                    public = False
            else:
                page, pages, pages_detailed = \
                    _get_dictionary_api_pages(
                        data, results
                    )

                embed = pages[page]
                embed.set_footer(text="page: " + str(page + 1) + " / " + str(int(len(pages))))
                view = DictionaryApi_PageView(pages, pages_detailed, timeout=90)
                await itx.followup.send(f"I found the following `{len(results)}` results on dictionaryapi.dev: ",
                                        embed=embed, view=view, ephemeral=True)
                await view.wait()
                if view.value in [None, 1, 2]:
                    await itx.edit_original_response(view=None)
        if source == 7 or source == 8:
            if not itx.response.is_done():
                await itx.response.defer(ephemeral=True)
            response_api = requests.get(f'https://api.urbandictionary.com/v0/define?term={term.lower()}').text
            # who decided to put the output into a dictionary with a list named 'list'? {"list":[{},{},{}]}
            data = json.loads(response_api)['list']
            if len(data) == 0:
                if source == 7:
                    result_str = f"I didn't find any results for '{term}' online or in our fancy dictionaries"
                    cmd_mention_dict = itx.client.get_command_mention("dictionary")
                    cmd_mention_def = itx.client.get_command_mention("dictionary_staff define")
                    await log_to_guild(itx.client, itx.guild,
                                       f":warning: **!! Alert:** {itx.user.name} ({itx.user.id}) searched for "
                                       f"'{term}' in the terminology dictionary and online, but there were "
                                       f"no results. Maybe we should add this term to "
                                       f"the {cmd_mention_dict} command ({cmd_mention_def})")
                else:
                    result_str = f"I didn't find any results for '{term}' on urban dictionary"
                public = False
            else:
                page, pages = await _get_urban_dictionary_pages(data)

                embed = pages[page]
                embed.set_footer(text="page: " + str(page + 1) + " / " + str(int(len(pages))))
                view = UrbanDictionary_PageView(pages, timeout=90)
                await itx.followup.send(f"I found the following `{len(pages)}` results on urbandictionary.com: ",
                                        embed=embed, view=view, ephemeral=True)
                await view.wait()
                if view.value in [None, 1, 2]:
                    await itx.edit_original_response(view=None)
                return

        assert len(result_str) > 0
        if itx.response.is_done():
            await itx.followup.send(result_str, ephemeral=not public, suppress_embeds=True)
        else:
            await itx.response.send_message(result_str, ephemeral=not public, suppress_embeds=True)

    admin = app_commands.Group(name='dictionary_staff', description='Change custom entries in the dictionary')

    @app_commands.check(is_staff_check)
    @admin.command(name="define", description="Add a dictionary entry for a word!")
    @app_commands.describe(
        term="This is the main word for the dictionary entry: Egg, Hormone Replacement Therapy (HRT), (case sens.)",
        definition="Give this term a definition",
        synonyms="Add synonyms (SEPARATE WITH \", \")")
    async def define(self, itx: discord.Interaction[Bot], term: str, definition: str, synonyms: str = ""):
        # Test if this term is already defined in this dictionary.
        collection = itx.client.rina_db["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is not None:
            cmd_mention = itx.client.get_command_mention("dictionary")
            await itx.response.send_message(
                f"You have already previously defined this term (try to find it with {cmd_mention}).", ephemeral=True)
            return
        await itx.response.defer(ephemeral=True)
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

        await log_to_guild(itx.client, itx.guild,
                           f"{itx.user.nick or itx.user.name} ({itx.user.id}) added the dictionary definition "
                           f"of '{term}' and set it to '{definition}', with synonyms: {synonyms}")
        await itx.followup.send(
            content=warnings + f"Successfully added '{term}' to the dictionary "
                               f"(with synonyms: {synonyms}): {definition}",
            ephemeral=True)

    @app_commands.check(is_staff_check)
    @admin.command(name="redefine", description="Edit a dictionary entry for a word!")
    @app_commands.describe(
        term="This is the main word for the dictionary entry (case sens.) Example: Egg, Hormone "
             "Replacement Therapy (HRT), etc.",
        definition="Redefine this definition")
    async def redefine(self, itx: discord.Interaction[Bot], term: str, definition: str):
        collection = itx.client.rina_db["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is None:
            cmd_mention = itx.client.get_command_mention("dictionary_staff define")
            await itx.response.send_message(
                f"This term hasn't been added to the dictionary yet, and thus cannot be redefined! Use {cmd_mention}.",
                ephemeral=True)
            return
        collection.update_one(query, {"$set": {"definition": definition}})

        await log_to_guild(itx.client, itx.guild,
                           f"{itx.user.nick or itx.user.name} ({itx.user.id}) changed the dictionary definition "
                           f"of '{term}' to '{definition}'")
        await itx.response.send_message(f"Successfully redefined '{term}'", ephemeral=True)

    @app_commands.check(is_staff_check)
    @admin.command(name="undefine", description="Remove a dictionary entry for a word!")
    @app_commands.describe(
        term="What word do you need to undefine (case sensitive). Example: Egg, Hormone Replacement Therapy (HRT), etc")
    async def undefine(self, itx: discord.Interaction[Bot], term: str):
        collection = itx.client.rina_db["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is None:
            await itx.response.send_message(
                "This term hasn't been added to the dictionary yet, and thus cannot be undefined!", ephemeral=True)
            return
        await log_to_guild(itx.client, itx.guild,
                           f"{itx.user.nick or itx.user.name} ({itx.user.id}) undefined the dictionary "
                           f"definition of '{term}' from '{search['definition']}' with synonyms: {search['synonyms']}")
        collection.delete_one(query)

        await itx.response.send_message(f"Successfully undefined '{term}'", ephemeral=True)

    @app_commands.check(is_staff_check)
    @admin.command(name="editsynonym", description="Add a synonym to a previously defined word")
    @app_commands.describe(
        term="This is the main word for the dictionary entry (case sens.): Egg, Hormone Transfer Therapy, etc",
        mode="Add or remove a synonym?",
        synonym="Which synonym to add/remove?")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Add a synonym', value=1),
        discord.app_commands.Choice(name='Remove a synonym', value=2),
    ])
    async def edit_synonym(self, itx: discord.Interaction[Bot], term: str, mode: int, synonym: str):
        collection = itx.client.rina_db["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is None:
            cmd_mention = itx.client.get_command_mention("dictionary_staff define")
            await itx.response.send_message(
                f"This term hasn't been added to the dictionary yet, and thus cannot get "
                f"new synonyms! Use {cmd_mention}.",
                ephemeral=True)
            return

        if mode == 1:
            synonyms = search["synonyms"]
            if synonym.lower() in synonyms:
                await itx.response.send_message("This term already has this synonym!", ephemeral=True)
                return
            synonyms.append(synonym.lower())
            collection.update_one(query, {"$set": {"synonyms": synonyms}}, upsert=True)
            await log_to_guild(itx.client, itx.guild,
                               f"{itx.user.nick or itx.user.name} ({itx.user.id}) added synonym '{synonym}' "
                               f"the dictionary definition of '{term}'")
            await itx.response.send_message("Successfully added synonym", ephemeral=True)
        if mode == 2:
            synonyms = search["synonyms"]
            if synonym.lower() not in synonyms:
                await itx.response.send_message("This term doesn't have this synonym!", ephemeral=True)
                return
            synonyms.remove(synonym.lower())
            if len(synonyms) < 1:
                await itx.response.send_message(
                    "You can't remove all the synonyms to a term! Then you can't find it in the dictionary anymore :P. "
                    "First, add a synonym before removing one.",
                    ephemeral=True)
                return
            collection.update_one(query, {"$set": {"synonyms": synonyms}}, upsert=True)
            await log_to_guild(itx.client, itx.guild,
                               f"{itx.user.nick or itx.user.name} ({itx.user.id}) removed synonym '{synonym}' "
                               f"the dictionary definition of '{term}'")
            await itx.response.send_message("Successfully removed synonym", ephemeral=True)

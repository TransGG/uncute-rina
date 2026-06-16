import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

import aiohttp
import asyncio

from extensions.termdictionary.dictionaries import (
    # CustomDictionary,
    DictionaryApiDictionary,
    DictionaryBase,
    PronounsPageDictionary,
)
from extensions.termdictionary.dictionaries.UrbanDictionary import \
    UrbanDictionary
from extensions.termdictionary.dictionary_sources import DictionarySources
from extensions.termdictionary.utils import simplify

from resources.abc import GuildInteraction
from resources.checks import is_staff_check  # for staff dictionary commands
from resources.customs import Bot
# For logging custom dictionary changes, or when a search query returns
#  nothing or >2000 characters
from resources.utils.utils import log_to_guild


def instantiate_sources(
        sources: list[tuple[DictionarySources, type[DictionaryBase]]],
        session: aiohttp.ClientSession,
) -> list[tuple[DictionarySources, DictionaryBase]]:
    return [
        (dictionary[0], dictionary[1](session))
        for dictionary in sources
    ]


class TermDictionary(commands.Cog):
    def __init__(self) -> None:
        self._session = aiohttp.ClientSession()
        self._dictionary_sources: list[
            tuple[DictionarySources, type[DictionaryBase]]
        ] = [
            # (d.CustomDictionary, CustomDictionary(client=itx.client)),
            (DictionarySources.PronounsPage,
             PronounsPageDictionary),
            (DictionarySources.DictionaryApi,
             DictionaryApiDictionary),
            (DictionarySources.UrbanDictionary,
             UrbanDictionary),
        ]

    async def cog_unload(self) -> None:
        await self._session.close()

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
            name='All',
            value=DictionarySources.All.value
        ),
        # discord.app_commands.Choice(
        #     name='Custom dictionary',
        #     value=DictionarySources.CustomDictionary.value
        # ),
        discord.app_commands.Choice(
            name='en.pronouns.page',
            value=DictionarySources.PronounsPage.value
        ),
        discord.app_commands.Choice(
            name='dictionaryapi.dev',
            value=DictionarySources.DictionaryApi.value
        ),
        discord.app_commands.Choice(
            name='urbandictionary.com',
            value=DictionarySources.UrbanDictionary.value
        ),
    ])
    @app_commands.allowed_installs(
        guilds=True, users=True)
    @app_commands.allowed_contexts(
        guilds=True, private_channels=True, dms=True)
    async def dictionary(
            self,
            itx: discord.Interaction[Bot],
            term: str,
            public: bool = False,
            source: DictionarySources = DictionarySources.All,
    ) -> None:
        await itx.response.defer(ephemeral=not public)

        sources = self._dictionary_sources[:]
        if source != DictionarySources.All:
            # filter dictionary sources to only the enabled ones.
            sources = [
                dictionary for dictionary in sources
                if dictionary[0] == source
            ]

        sources = instantiate_sources(sources, self._session)

        await asyncio.gather(*[
            source.construct_response(term)
            for _, source in sources
        ])

        for dict_source, strategy in sources:
            if strategy.has_response:
                await strategy.send_response(itx, public)
                return
            elif dict_source == source:
                if public:
                    # remove public defer message so itx.followup.send
                    #  doesn't also send the deny message publicly.
                    await itx.delete_original_response()
                await strategy.handle_no_response(itx, term)
                return

        cmd_dictionary = itx.client.get_command_mention(
            "dictionary")
        cmd_define = itx.client.get_command_mention_with_args(
            "dictionary_staff define", term=" ", definition=" ")
        await log_to_guild(
            itx.client,
            itx.guild,
            f":warning: **!! Alert:** {itx.user.name} "
            f"({itx.user.id}) searched for '{term}' in the "
            f"terminology dictionary and online, but there were "
            f"no results. Maybe we should add this term to "
            f"the {cmd_dictionary} command ({cmd_define})"
        )

    @dictionary.autocomplete("term")
    async def dict_autocomplete_helper(
            self,
            itx: discord.Interaction[Bot],
            current: str
    ) -> list[discord.app_commands.Choice[str]]:
        if current == '':
            return []

        # select the right sources
        sources = self._dictionary_sources[:]
        if itx.namespace.source in DictionarySources:
            if type(itx.namespace.source) is not DictionarySources:
                source = DictionarySources(itx.namespace.source)
            else:
                source = itx.namespace.source

            sources = [
                dictionary
                for dictionary in self._dictionary_sources[:]
                if dictionary[0] == source
            ]
        sources = instantiate_sources(sources, self._session)

        # fetch autocompletion results
        async def fetch_with_timeout(dictionary: DictionaryBase) -> set[str]:
            try:
                return await asyncio.wait_for(
                    dictionary.get_autocomplete(current),
                    timeout=2.5,
                )
            except asyncio.TimeoutError:
                return set()

        tasks = [
            fetch_with_timeout(source)
            for _, source in sources
        ]
        results: tuple[set[str]] = await asyncio.gather(*tasks)

        terms: set[str] = set.union(*results)

        # respond with found autocompletion terms
        return [
            app_commands.Choice[str](name=term, value=term)
            for term in terms
        ][:7]  # limit choices to the first 7

    admin = app_commands.Group(
        name='dictionary_staff',
        description='Change custom entries in the dictionary'
    )

    @admin.command(name="define",
                   description="Add a dictionary entry for a word!")
    @app_commands.describe(
        term="This is the main word for the dictionary entry: "
             "Egg, Hormone Replacement Therapy (HRT), (case sens.)",
        definition="Give this term a definition",
        synonyms="Add synonyms (SEPARATE WITH \", \")"
    )
    @is_staff_check
    async def define(
            self,
            itx: GuildInteraction[Bot],
            term: str,
            definition: str,
            synonyms: str = "",
    ) -> None:
        # Test if this term is already defined in this dictionary.
        collection = itx.client.rina_db["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is not None:
            cmd_dictionary = itx.client.get_command_mention_with_args(
                "dictionary", term=term)
            await itx.response.send_message(
                f"You have already previously defined this term (try to find "
                f"it with {cmd_dictionary}).",
                ephemeral=True,
            )
            return
        await itx.response.defer(ephemeral=True)
        # Test if a synonym is already used before
        if synonyms != "":
            synonym_list = synonyms.split(", ")
            synonym_list = [simplify(i) for i in synonym_list]
        else:
            synonym_list = []
        if simplify(term) not in synonym_list:
            synonym_list.append(simplify(term))

        query = {"synonyms": {"$in": synonym_list}}
        synonym_overlap = collection.find(query)
        warnings = ""
        for overlap in synonym_overlap:
            warnings += (f"You have already given a synonym before "
                         f"in {overlap['term']}.\n")

        # Add term to dictionary
        post = {
            "term": term,
            "definition": definition,
            "synonyms": synonym_list
        }
        collection.insert_one(post)

        await log_to_guild(
            itx.client,
            itx.guild,
            f"{itx.user.name} ({itx.user.id}) added "
            f"the dictionary definition of '{term}' and set it to "
            f"'{definition}', with synonyms: {synonym_list}",
        )
        await itx.followup.send(
            content=warnings
            + f"Successfully added '{term}' to the dictionary "
              f"(with synonyms: {synonym_list}): {definition}",
            ephemeral=True,
        )

    @admin.command(name="redefine",
                   description="Edit a dictionary entry for a word!")
    @app_commands.describe(
        term="This is the main word for the dictionary entry (case sens.) "
             "Example: Egg, Hormone Replacement Therapy (HRT), etc.",
        definition="Redefine this definition"
    )
    @is_staff_check
    async def redefine(
            self,
            itx: GuildInteraction[Bot],
            term: str,
            definition: str
    ) -> None:
        collection = itx.client.rina_db["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is None:
            cmd_define = itx.client.get_command_mention_with_args(
                "dictionary_staff define", term=" ", definition=" ")
            await itx.response.send_message(
                f"This term hasn't been added to the dictionary yet, and "
                f"thus cannot be redefined! Use {cmd_define}.",
                ephemeral=True,
            )
            return
        collection.update_one(query, {"$set": {"definition": definition}})

        await log_to_guild(
            itx.client,
            itx.guild,
            f"{itx.user.name} ({itx.user.id}) changed the dictionary definition "
            f"of '{term}' to '{definition}'",
        )
        await itx.response.send_message(
            f"Successfully redefined '{term}'",
            ephemeral=True
        )

    @admin.command(name="undefine",
                   description="Remove a dictionary entry for a word!")
    @app_commands.describe(
        term="What word do you need to undefine (case sensitive). Example: "
             "Egg, Hormone Replacement Therapy (HRT), etc",
    )
    @is_staff_check
    async def undefine(self, itx: GuildInteraction[Bot], term: str) -> None:
        collection = itx.client.rina_db["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is None:
            await itx.response.send_message(
                "This term hasn't been added to the dictionary yet, and "
                "thus cannot be undefined!",
                ephemeral=True,
            )
            return
        await log_to_guild(
            itx.client,
            itx.guild,
            f"{itx.user.name} ({itx.user.id}) undefined the dictionary "
            f"definition of '{term}' from '{search['definition']}' with "
            f"synonyms: {search['synonyms']}",
        )
        collection.delete_one(query)

        await itx.response.send_message(
            f"Successfully undefined '{term}'",
            ephemeral=True
        )

    @admin.command(name="editsynonym",
                   description="Add a synonym to a previously defined word")
    @app_commands.describe(
        term="This is the main word for the dictionary entry (case sens.): "
             "Egg, Hormone Transfer Therapy, etc",
        mode="Add or remove a synonym?",
        synonym="Which synonym to add/remove?"
    )
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Add a synonym', value=1),
        discord.app_commands.Choice(name='Remove a synonym', value=2),
    ])
    @is_staff_check
    async def edit_synonym(
            self,
            itx: GuildInteraction[Bot],
            term: str,
            mode: int,
            synonym: str,
    ) -> None:
        collection = itx.client.rina_db["termDictionary"]
        query = {"term": term}
        search = collection.find_one(query)
        if search is None:
            cmd_define = itx.client.get_command_mention_with_args(
                "dictionary_staff define",
                term=" ",
                definition=" "
            )
            await itx.response.send_message(
                f"This term hasn't been added to the dictionary yet, and "
                f"thus cannot get new synonyms! Use {cmd_define}.",
                ephemeral=True)
            return

        if mode == 1:
            synonyms = search["synonyms"]
            if synonym.lower() in synonyms:
                await itx.response.send_message(
                    "This term already has this synonym!",
                    ephemeral=True,
                )
                return
            synonyms.append(synonym.lower())
            collection.update_one(
                query,
                {"$set": {"synonyms": synonyms}},
                upsert=True,
            )
            await log_to_guild(
                itx.client,
                itx.guild,
                f"{itx.user.name} ({itx.user.id}) added synonym '{synonym}' "
                f"the dictionary definition of '{term}'",
            )
            await itx.response.send_message(
                "Successfully added synonym",
                ephemeral=True,
            )
        if mode == 2:
            synonyms = search["synonyms"]
            if synonym.lower() not in synonyms:
                await itx.response.send_message(
                    "This term doesn't have this synonym!",
                    ephemeral=True,
                )
                return
            synonyms.remove(synonym.lower())
            if len(synonyms) < 1:
                await itx.response.send_message(
                    "You can't remove all the synonyms to a term! Then you "
                    "can't find it in the dictionary anymore :P. First, add "
                    "a synonym before removing one.",
                    ephemeral=True,
                )
                return
            collection.update_one(
                query,
                {"$set": {"synonyms": synonyms}},
                upsert=True,
            )
            await log_to_guild(
                itx.client,
                itx.guild,
                f"{itx.user.name} ({itx.user.id}) removed synonym '{synonym}' "
                f"the dictionary definition of '{term}'",
            )
            await itx.response.send_message(
                "Successfully removed synonym",
                ephemeral=True,
            )

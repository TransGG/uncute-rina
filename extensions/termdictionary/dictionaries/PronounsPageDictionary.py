import discord

import aiohttp
import json
import re  # to parse and remove https:/pronouns.page/ in-text page linking
from typing import override

from .DictionaryBase import DictionaryBase
from resources.customs import Bot
from extensions.termdictionary.utils import simplify
from .objects import PronounsPageEntry


class PronounsPageDictionary(DictionaryBase):
    """
    Implementation of DictionaryBase for querying the pronouns.page API.

    This class handles dictionary entry lookup, response construction,
    and result formatting specific to the pronouns.page service.
    It manages internal state for search results, response expansion,
    and Discord character limit constraints.

    :ivar _result_str: Final response string to send to the user, or
     ``None`` if no results found.
    :ivar _result_count: Number of matching results found for the
     current term.
    :ivar _character_overflow: Internal flag to track if response
     exceeds Discord's 2000-character limit.
    :ivar _expand_search: Boolean indicating whether to expand search
     to include synonyms/related terms.
    """

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__()
        self._session = session
        self._result_str: str | None = None
        self._result_count = 0
        self._character_overflow = False
        self._expand_search = False
        self._term: str | None = None

    @staticmethod
    def _clean_pronouns_page_response_links(
            data: list[PronounsPageEntry]
    ) -> list[PronounsPageEntry]:
        """
        Helper for removing links in pronouns.page responses.
        :param data: The api response to clean up.
        :return: The given response data with cleaned up descriptions.
        """
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
        return search

    @staticmethod
    def _get_expand_medium_search_string(result_str, search):
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
        return result_str

    @staticmethod
    def _get_expand_big_search_string(result_str, search):
        result_str += "Here is a list to make your search more specific:\n"
        results: list[str] = []
        for item in search:
            temp = item['term']
            if "|" in temp:
                temp = temp.split("|")[0]
            results.append(temp)
        result_str += ', '.join(results)
        return result_str

    @staticmethod
    def _select_exact_items(
            search: list[PronounsPageEntry], term
    ) -> list[PronounsPageEntry]:
        """
        Select search results whose key or synonyms exactly match the
        given term.

        :param search: The API response to filter.
        :param term: The term the user searched for.
        :return: The filtered search results.
        """
        # If one of the search results matches exactly with the
        #  search, give that definition.
        results: list[PronounsPageEntry] = []
        for item in search:
            if simplify(term) in simplify(item['term'].split('|')):
                results.append(item)
        return results

    @staticmethod
    def _get_result_string(
            results: list[PronounsPageEntry],
            search: list[PronounsPageEntry],
            term: str
    ) -> str:
        """
        Construct a response from the list of results.
        :param results: The selected search results containing the term.
        :param search: The api-provided search results (that may contain
         the term in the description, but not necessarily in the title
         or synonyms)
        :param term: The term the user searched for.
        :return: The constructed response.
        :raise OverflowError: If the API response has too many results.
        """
        result_str = (
            f"I found {len(results)} exact result{'s' * (len(results) != 1)} "
            f"for '{term}' on en.pronouns.page! \n")
        for item in results:
            result_str += (f"> **{', '.join(item['term'].split('|'))}:** "
                           f"{item['definition']}\n")
        if (len(search) - len(results)) > 0:
            result_str += (f"{len(search) - len(results)} other non-exact "
                           f"results found.")
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
        return result_str

    async def _get_api_response(
            self,
            term: str
    ) -> list[PronounsPageEntry]:
        http_safe_term = term.lower().replace("/", " ").replace("%", " ")
        url = f'https://en.pronouns.page/api/terms/search/{http_safe_term}'

        async with self._session.get(url) as response:
            response_api = await response.text()

        data = json.loads(response_api)
        return data

    @override
    async def get_autocomplete(self, current: str) -> set[str]:
        data = await self._get_api_response(current)
        # find exact results online (or synonyms)
        if len(data) == 0:
            return set()

        terms = set()
        for item in data:
            synonyms = item['term'].split("|")
            if simplify(current) in simplify(synonyms):
                terms.add(synonyms[0].capitalize())

        return terms

    @override
    async def construct_response(self, term: str) -> None:
        self._term = term
        data = await self._get_api_response(term)
        if len(data) == 0:
            return

        search = self._clean_pronouns_page_response_links(data)
        self._result_count = len(search)
        results = self._select_exact_items(search, term)

        if len(results) > 0:
            # there are results that match exactly.
            try:
                self._result_str = self._get_result_string(
                    results, search, term)
                self.has_response = True
            except OverflowError as ex:
                self._character_overflow = True
                self._result_str = str(ex)
            return

        # if search doesn't exactly match with a result / synonym
        start_string = (
            f"I found {len(search)} result{'s' * (len(results) != 1)} for "
            f"'{term}' on en.pronouns.page! ")
        if len(search) > 25:
            self._result_str = self._get_expand_big_search_string(
                start_string, search)
            self._expand_search = True
        elif len(search) > 2:
            self._result_str = self._get_expand_medium_search_string(
                start_string, search)
            self._expand_search = True
        elif len(search) > 0:
            start_string += "\n"
            for item in search:
                start_string += (f"> **{', '.join(item['term'].split('|'))}:**"
                                 f" {item['definition']}\n")
            self._result_str = start_string

        self.has_response = True

    @override
    async def send_response(
            self,
            itx: discord.Interaction[Bot],
            public: bool
    ) -> None:
        itx.followup: discord.Webhook  # type: ignore
        assert (self.has_response
                and self._result_str is not None
                and self._term is not None)
        msg_length = len(self._result_str)
        if msg_length > 1999:
            more_info_link = ("https://en.pronouns.page/dictionary/terminology"
                              f"?filter={self._term.lower()}")
            self._result_str = (
                f"Your search ('{self._term}') returned too many results "
                f"({self._result_count} in total!) (discord has a "
                f"2000-character message length, and this message was "
                f"{msg_length} characters D:). Please search more "
                f"specifically.\n Here is a link for expanded info on "
                f"each term: <{more_info_link}>")
            public = False

        if self._expand_search:
            public = False
        if self._character_overflow:
            public = False

        await itx.followup.send(
            self._result_str,
            ephemeral=not public,
            suppress_embeds=True,
            allowed_mentions=discord.AllowedMentions.none()
        )

    @override
    async def handle_no_response(
            self,
            itx: discord.Interaction[Bot],
            term: str
    ) -> None:
        itx.followup: discord.Webhook  # type: ignore

        if self._character_overflow:
            assert self._result_str is not None

            await itx.followup.send(
                self._result_str[:2000],
                ephemeral=True,
                suppress_embeds=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        await itx.followup.send(
            f"I didn't find any results for '{term}' on en.pronouns.page",
            ephemeral=True,
            suppress_embeds=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

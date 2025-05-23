import discord

import aiohttp
import json
from typing import override
import urllib.parse

from resources.customs import Bot
from extensions.termdictionary.dictionaries.DictionaryBase import \
    DictionaryBase
from extensions.termdictionary.dictionaries.objects import (
    DictionaryApiEntry,
    DetailedTermPage, term_page_to_embed
)
from extensions.termdictionary.views import DictionaryapiPageview


CompressedApiData = list[tuple[str, dict[str, list[str]], str, str, str]]


def _format_page_sections(antonyms, meanings, synonyms):
    page_sections: dict[str, list[str]] = {}
    for part_of_speech, definitions in meanings.items():
        part_of_speech = part_of_speech.capitalize()
        page_sections[part_of_speech] = definitions
    if synonyms:
        page_sections["Synonyms"] = [", ".join(synonyms)]
    if antonyms:
        page_sections["Antonyms"] = [", ".join(antonyms)]
    if "sourceUrls" in page_sections:
        page_sections["More info:"] \
            = ['\n'.join(page_sections["sourceUrls"])]
    return page_sections


def _extract_api_data(result):
    meanings: dict[str, list[str]] = {}
    synonyms: set[str] = set()
    antonyms: set[str] = set()
    for meaning in result["meanings"]:
        meaning_list = []
        for definition in meaning["definitions"]:
            meaning_list.append(definition['definition'])
            synonyms.update(definition['synonyms'])
            antonyms.update(definition['antonyms'])

        part_of_speech = meaning['partOfSpeech'].capitalize()
        meanings[part_of_speech] = meaning_list
        synonyms.update(meaning['synonyms'])
        antonyms.update(meaning['antonyms'])
    return antonyms, meanings, synonyms


class DictionaryApiDictionary(DictionaryBase):
    def __init__(self, session: aiohttp.ClientSession):
        super().__init__()
        self._session = session
        self._embed: discord.Embed | None = None
        self._view: DictionaryapiPageview | None = None

    @staticmethod
    def _get_pages(
            data: list[DictionaryApiEntry]
    ) -> list[DetailedTermPage]:
        """
        Helper to
        """
        pages = []
        for result in data:
            antonyms, meanings, synonyms = _extract_api_data(result)
            page_sections = _format_page_sections(antonyms, meanings, synonyms)
            pages.append((result["word"].capitalize(), page_sections))

        return pages

    async def _get_api_response(
            self,
            term: str
    ) -> list[DictionaryApiEntry] | None:
        url = (
            "https://api.dictionaryapi.dev/api/v2/entries/en/"
            + urllib.parse.quote(term.lower(), safe=())
            # ^ slashes aren't safe
        )
        async with self._session.get(url) as response:
            response_api = await response.text()

        try:
            data = json.loads(response_api)
            if type(data) is dict:
                # should be a list of entries
                return None

            assert type(data) is list
            return data
        except json.decoder.JSONDecodeError:
            return None

    @override
    async def get_autocomplete(self, current: str) -> set[str]:
        data = await self._get_api_response(current)
        if data is None:
            return set()

        terms = set()
        for result in data:
            terms.add(result["word"])
        return terms

    @override
    async def construct_response(self, term: str) -> None:
        data = await self._get_api_response(term)
        if data is None:
            return
        pages = DictionaryApiDictionary._get_pages(data)

        start_page = 0
        embed = term_page_to_embed(pages[start_page])
        embed.set_footer(
            text=f"page: 1 / {len(pages)}")

        self._embed = embed
        self._view = DictionaryapiPageview(pages, timeout=90)
        self.has_response = True

    @override
    async def send_response(
            self,
            itx: discord.Interaction[Bot],
            public: bool
    ) -> None:
        itx.followup: discord.Webhook  # type: ignore
        assert (self.has_response
                and self._view is not None
                and self._embed is not None)

        if public:
            self._view.delete_extra_buttons()

        await itx.followup.send(
            embed=self._embed,
            view=self._view
        )
        await self._view.wait()
        try:
            await itx.edit_original_response(view=None)
        except discord.NotFound:
            # message was deleted?
            pass

    @override
    async def handle_no_response(
            self,
            itx: discord.Interaction[Bot],
            term: str
    ) -> None:
        itx.followup: discord.Webhook  # type: ignore
        await itx.followup.send(
            f"I didn't find any results for '{term}' on dictionaryapi.dev!",
            ephemeral=True,
            suppress_embeds=True,
            allowed_mentions=discord.AllowedMentions.none()
        )

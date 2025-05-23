from typing import override

import discord

from resources.checks.permissions import is_staff
from resources.customs import Bot
from .DictionaryBase import DictionaryBase
from extensions.termdictionary.dictionaries.objects import \
    CustomDictionaryEntry
from extensions.termdictionary.utils import simplify


class CustomDictionary(DictionaryBase):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self._result_str: str | None = None
        self._long_line: bool = False
        self._character_overflow: bool = False

    async def _get_api_response(
            self,
            term: str
    ) -> list[tuple[str, str]]:
        """Helper to get custom dictionary data from the database."""
        collection = self.client.async_rina_db["termDictionary"]
        query = {"synonyms": term.lower()}
        search = collection.find(query)
        results: list[tuple[str, str]] = []
        async for item in search:
            item: CustomDictionaryEntry
            if simplify(term) in simplify(item["synonyms"]):
                results.append((item["term"], item["definition"]))

        return results

    @override
    async def get_autocomplete(self, current: str) -> set[str]:
        results = await self._get_api_response(current)
        if not results:
            return set()
        return set(current for current, _ in results)

    @override
    async def construct_response(self, term: str) -> None:
        results = await self._get_api_response(term)
        if not results:
            return
        self.has_response = True

        self._result_str = (
            f"I found {len(results)} result{'s' * (len(results) > 1)} "
            f"for '{term}' in our dictionary:\n"
        )
        for result_term, result_definition in results:
            self._result_str += f"> **{result_term}**: {result_definition}\n"

        if len(self._result_str.split("\n")) > 3:
            self._long_line = True

        if len(self._result_str) > 1999:
            self._character_overflow = True

    @override
    async def send_response(
            self,
            itx: discord.Interaction[Bot],
            public: bool
    ) -> None:
        itx.followup: discord.Webhook  # type: ignore
        assert self._result_str is not None

        if self._character_overflow:
            self._result_str = (
                "Your search returned too many results (discord has "
                "a 2000-character message length D:). (Please ask staff to "
                "fix this (synonyms and stuff).)\n\n"
                + self._result_str
            )[:2000]
            public = False

        if public and self._long_line:
            self._result_str += (
                "\nDidn't send your message as public cause it"
                " would be spammy, having this many results."
            )
            public = False

        await itx.followup.send(
            self._result_str, ephemeral=not public, suppress_embeds=True,
            allowed_mentions=discord.AllowedMentions.none()
        )

    @override
    async def handle_no_response(
            self,
            itx: discord.Interaction[Bot],
            term: str
    ) -> None:
        if is_staff(itx, itx.user):
            cmd_define = itx.client.get_command_mention_(
                "dictionary_staff define",
                term=term,
                definition=" ",
                synonyms="a, b, c"
            )
            result_str = (
                f"No information found in the custom dictionary for "
                f"this term.\n"
                f"If you would like to add a term,  use {cmd_define}."
            )
        else:
            cmd_define = itx.client.get_command_mention(
                "dictionary_staff define")
            result_str = (
                f"No information found in the custom dictionary for "
                f"this term.\n"
                f"If you would like to add a term, message a staff member "
                f"(to use {cmd_define})"
            )

        await itx.followup.send(
            result_str,
            ephemeral=True,
            suppress_embeds=True,
            allowed_mentions=discord.AllowedMentions.none()
        )

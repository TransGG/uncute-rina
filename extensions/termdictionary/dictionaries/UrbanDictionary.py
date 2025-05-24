
import discord

import aiohttp
from datetime import datetime
import json
import math
from typing import override

from extensions.termdictionary.dictionaries import DictionaryBase
from extensions.termdictionary.dictionaries.objects import (
    UrbanDictionaryEntry
)
from extensions.termdictionary.views import UrbanDictionaryPageView
from resources.customs import Bot


class UrbanDictionary(DictionaryBase):
    term_suffix = " [UD]"

    def __init__(self, session: aiohttp.ClientSession):
        super().__init__()
        self._session = session
        self._pages: list[discord.Embed] | None = None

    @staticmethod
    def _calculate_post_score(result: UrbanDictionaryEntry) -> float:
        # Based on the Wilson score interval:
        #  https://stackoverflow.com/a/10029645
        upvotes = result["thumbs_up"]
        downvotes = result["thumbs_down"]
        z = 1.96  # 95% confidence

        votes = upvotes + downvotes
        if votes == 0:
            # Avoid division by zero
            return 0
        phat = upvotes / votes

        score = (
            (phat
             + (z * z) / (2 * votes)
             - z * math.sqrt((phat * (1 - phat) + z * z / (4 * votes))
                             / votes)
             )
            / (1 + z * z / votes)
        )
        return score

    @staticmethod
    def _get_urban_dictionary_pages(data) -> list[discord.Embed]:
        data = sorted(
            data,
            key=lambda r: UrbanDictionary._calculate_post_score(r),
            reverse=True  # sort from highest to lowest
        )

        pages = []
        for result in data:
            embed = discord.Embed(
                title=f"__{result['word'].capitalize()}__",
                description=result['definition'],
                url=result['permalink'],
                color=8481900,
            )
            post_date = int(
                datetime.fromisoformat(result['written_on']).timestamp()
            )

            if len(result['example']) > 800:
                result['example'] = (result['example'][:800]
                                     + "... (shortened due to size)")
            embed.add_field(
                name="Example",
                value=f"{result['example']}\n\n"
                      f"{result['thumbs_up']}:thumbsup: "
                      f":thumbsdown: {result['thumbs_down']}\n"
                      f"Sent by {result['author']} "
                      f"on <t:{post_date}:d> "
                      f"at <t:{post_date}:T> (<t:{post_date}:R>)",
                inline=False
            )
            embed.set_footer(text=f"page: {len(pages) + 1} / {len(data)}")
            pages.append(embed)
        return pages

    async def _get_api_response(
            self,
            term: str
    ) -> list[UrbanDictionaryEntry]:
        params = {"term": term}
        url = "https://api.urbandictionary.com/v0/define"
        async with self._session.get(url, params=params) as response:
            response_api = await response.text()

        data: dict[str, list[UrbanDictionaryEntry]] = json.loads(response_api)
        return data['list']  # empty responses have {"list":[]}

    @override
    async def get_autocomplete(self, current: str) -> set[str]:
        data = await self._get_api_response(current)
        if len(data) == 0:
            return set()

        terms = set()
        for result in data:
            terms.add(result["word"].capitalize() + self.term_suffix)
        return terms

    @override
    async def construct_response(self, term: str) -> None:
        if term.endswith(self.term_suffix):
            term = term[:-len(self.term_suffix)]
        data = await self._get_api_response(term)
        if len(data) == 0:
            return

        self._pages = self._get_urban_dictionary_pages(data)
        self.has_response = True

    @override
    async def send_response(
            self,
            itx: discord.Interaction[Bot],
            public: bool
    ) -> None:
        assert (self.has_response
                and self._pages is not None)

        if public:
            # Remove public defer message to instead send this reply
            #  privately. (can often contain swears and unexpected info
            #  that you may not want to send publicly.
            await itx.delete_original_response()

        embed = self._pages[0]
        embed.set_footer(text=f"page: 1 / {len(self._pages)}")

        view = UrbanDictionaryPageView(self._pages, timeout=90)
        await itx.followup.send(
            f"I found the following `{len(self._pages)}` results on "
            f"urbandictionary.com: ",
            embed=embed,
            view=view,
            ephemeral=True,
        )
        await view.wait()
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
            f"I didn't find any results for '{term}' on urbandictionary.com",
            ephemeral=True,
            suppress_embeds=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )

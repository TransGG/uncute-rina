import json
import math
from datetime import datetime
import typing

import aiohttp
import discord

from extensions.termdictionary.dictionaries import DictionaryBase
from extensions.termdictionary.dictionaries.objects import UrbanDictionaryEntry
from extensions.termdictionary.views import UrbanDictionaryPageView
from resources.customs import Bot


class UrbanDictionary(DictionaryBase):
    term_suffix = " [UD]"

    def __init__(self, session: aiohttp.ClientSession) -> None:
        super().__init__(session)
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
    def _get_urban_dictionary_pages(
            data: list[UrbanDictionaryEntry],
    ) -> list[discord.Embed]:
        data = sorted(
            data,
            key=UrbanDictionary._calculate_post_score,
            reverse=True  # sort from highest to lowest
        )

        pages: list[discord.Embed] = []
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

    @typing.override
    async def get_autocomplete(self, current: str) -> set[str]:
        data = await self._get_api_response(current)
        if len(data) == 0:
            return set()

        terms = set()
        for result in data:
            terms.add(result["word"].capitalize() + self.term_suffix)
        return terms

    @typing.override
    async def construct_response(self, term: str) -> None:
        term = term.removesuffix(self.term_suffix)
        data = await self._get_api_response(term)
        if len(data) == 0:
            return

        self._pages = self._get_urban_dictionary_pages(data)
        self.has_response = True

    @typing.override
    async def send_response(
            self,
            itx: discord.Interaction[Bot],
            public: bool
    ) -> None:
        if (not self.has_response
                or self._pages is None):
            raise ValueError(
                f"has_response was false or _pages was None! "
                f"({not self.has_response}, {self._pages is None})",
            )

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

    @typing.override
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

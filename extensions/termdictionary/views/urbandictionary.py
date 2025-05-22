from typing import override

import discord

from resources.customs import Bot
from resources.views.generics import PageView


class UrbanDictionaryPageView(PageView):
    def __init__(self, pages: list[discord.Embed], timeout=None):
        super().__init__(
            starting_page=0,
            max_page_index=len(pages),
            timeout=timeout
        )
        self.timeout = timeout
        self.pages = pages

    @override
    async def update_page(self, itx: discord.Interaction[Bot], view: PageView):
        itx.response: discord.InteractionResponse[Bot]  # type: ignore
        await itx.response.edit_message(
            embed=self.pages[self.page],
            view=view
        )

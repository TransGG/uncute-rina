from typing import override

import discord

from extensions.termdictionary.dictionaries.objects import (
    term_page_to_embed,
    get_term_lines
)
from extensions.termdictionary.modals import DictionaryAPISendPageModal
from resources.customs import Bot
from resources.views.generics import PageView


DetailedTermPage = tuple[str, dict[str, list[str]]]


class DictionaryapiPageview(PageView):
    def __init__(
            self,
            pages: list[DetailedTermPage],
            timeout=90
    ):
        super().__init__(
            starting_page=0,
            max_page_index=len(pages),
            timeout=timeout,
        )
        self.timeout = timeout
        self.pages = pages

    @override
    async def update_page(
            self, itx: discord.Interaction[Bot], view: PageView
    ) -> None:
        embed = term_page_to_embed(self.pages[self.page])
        embed.set_footer(
            text=f"page: {self.page + 1} / {self.max_page_index + 1}")

        await itx.response.edit_message(
            embed=embed,
            view=view
        )

    @discord.ui.button(label='Send publicly', style=discord.ButtonStyle.gray)
    async def send_publicly(
            self,
            itx: discord.Interaction[Bot],
            _button: discord.ui.Button
    ):
        embed = term_page_to_embed(self.pages[self.page])
        await itx.followup.send(
            f"{itx.user.mention} shared a dictionary entry!",
            embed=embed,
            ephemeral=False,
            allowed_mentions=discord.AllowedMentions.none()
        )
        await itx.response.edit_message(
            content="Sent successfully!", embed=None)
        self.stop()

    @discord.ui.button(label='Send one entry', style=discord.ButtonStyle.gray)
    async def send_single_entry(
            self,
            itx: discord.Interaction[Bot],
            _button: discord.ui.Button
    ):
        term_lines = get_term_lines(self.pages[self.page])

        max_page_index = len(term_lines) - 1
        send_one_modal = DictionaryAPISendPageModal(max_page_index)
        await itx.response.send_modal(send_one_modal)
        await send_one_modal.wait()
        if not send_one_modal.succeeded:
            return
        assert send_one_modal.line is not None

        term: str = self.pages[self.page][0]
        page: tuple[str, str] = term_lines[send_one_modal.line]
        embed = discord.Embed(title=term, color=8481900)
        embed.add_field(name=page[0],  # section name
                        value=page[1],  # line content
                        inline=False)
        await itx.followup.send(
            f"{itx.user.mention} shared a section of a dictionary entry! "
            f"(item {send_one_modal.line})",
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
        )

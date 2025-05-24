import discord

from extensions.nameusage.modals.getnamemodal import GetNameModal
from resources.customs import Bot
from resources.views.generics import PageView


class GetTopPageView(PageView):
    def __init__(
            self,
            pages: list[str],
            embed_title,
            timeout: float | None = None
    ):
        super().__init__(
            starting_page=0,
            max_page_index=int(len(pages) / 2) - 1,
            timeout=timeout
        )
        self.pages = pages
        self.embed_title = embed_title

    def make_page(self) -> discord.Embed:
        result_page = self.pages[self.page * 2]
        result_page2 = self.pages[self.page * 2 + 1]
        embed = discord.Embed(color=8481900, title=self.embed_title)
        embed.add_field(name="Column 1", value=result_page)
        embed.add_field(name="Column 2", value=result_page2)
        embed.set_footer(
            text="page: "
                 + str(self.page + 1)
                 + " / "
                 + str(int(len(self.pages) / 2))
        )
        return embed

    async def update_page(
            self,
            itx: discord.Interaction[Bot],
            view: PageView
    ):
        itx.response: discord.InteractionResponse[Bot]  # type: ignore
        embed = self.make_page()
        await itx.response.edit_message(
            embed=embed,
            view=view
        )

    @discord.ui.button(
        label='Find my name',
        style=discord.ButtonStyle.blurple,
    )
    async def find_name(
            self,
            itx: discord.Interaction[Bot],
            _button: discord.ui.Button
    ):
        send_one = GetNameModal(self.pages)
        await itx.response.send_modal(send_one)
        await send_one.wait()
        if (send_one.return_interaction is not None
                and send_one.page is not None):
            self.page = send_one.page
            await self.update_page(send_one.return_interaction, self)

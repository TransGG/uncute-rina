import discord
from resources.modals.nameusage import GetNameModalNameUsageGetTop


class PageViewNameUsageGetTop(discord.ui.View):
    def __init__(self, pages, embed_title, timeout=None):
        super().__init__()
        self.value = None
        self.timeout = timeout
        self.page = 0
        self.pages = pages
        self.embed_title = embed_title

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Previous', style=discord.ButtonStyle.blurple)
    async def previous(self, itx: discord.Interaction, _button: discord.ui.Button):
        # self.value = "previous"
        self.page -= 1
        if self.page < 0:
            self.page = int(len(self.pages) / 2) - 1
        result_page = self.pages[self.page * 2]
        result_page2 = self.pages[self.page * 2 + 1]
        embed = discord.Embed(color=8481900, title=self.embed_title)
        embed.add_field(name="Column 1", value=result_page)
        embed.add_field(name="Column 2", value=result_page2)
        embed.set_footer(text="page: " + str(self.page + 1) + " / " + str(int(len(self.pages) / 2)))
        await itx.response.edit_message(embed=embed)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.blurple)
    async def next(self, itx: discord.Interaction, _button: discord.ui.Button):
        self.page += 1
        if self.page >= int(len(self.pages) / 2):
            self.page = 0
        result_page = self.pages[self.page * 2]
        result_page2 = self.pages[self.page * 2 + 1]
        embed = discord.Embed(color=8481900, title=self.embed_title)
        embed.add_field(name="Column 1", value=result_page)
        embed.add_field(name="Column 2", value=result_page2)
        embed.set_footer(text="page: " + str(self.page + 1) + " / " + str(int(len(self.pages) / 2)))
        await itx.response.edit_message(embed=embed)

    @discord.ui.button(label='Find my name', style=discord.ButtonStyle.blurple)
    async def find_name(self, itx: discord.Interaction, _button: discord.ui.Button):
        send_one = GetNameModalNameUsageGetTop(self.pages, self.embed_title)
        await itx.response.send_modal(send_one)
        await send_one.wait()
        if send_one.value in [None, 9]:
            pass
        else:
            self.page = send_one.page

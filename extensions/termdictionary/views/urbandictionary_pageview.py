import discord


class UrbanDictionary_PageView(discord.ui.View):
    def __init__(self, pages, timeout=None):
        # todo: just make this a PageView
        super().__init__()
        self.value = None
        self.timeout = timeout
        self.page = 0
        self.pages = pages

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.blurple)
    async def previous(self, itx: discord.Interaction, _button: discord.ui.Button):
        self.page -= 1
        if self.page < 0:
            self.page = len(self.pages) - 1
        embed = self.pages[self.page]
        embed.set_footer(text="page: " + str(self.page + 1) + " / " + str(int(len(self.pages))))
        await itx.response.edit_message(embed=embed)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.blurple)
    async def next(self, itx: discord.Interaction, _button: discord.ui.Button):
        self.page += 1
        if self.page >= (len(self.pages)):
            self.page = 0
        embed = self.pages[self.page]
        embed.set_footer(text="page: " + str(self.page + 1) + " / " + str(int(len(self.pages))))
        try:
            await itx.response.edit_message(embed=embed)
        except discord.errors.HTTPException:
            self.page -= 1
            await itx.response.send_message("This is the last page, you can't go to a next page!",
                                            ephemeral=True)

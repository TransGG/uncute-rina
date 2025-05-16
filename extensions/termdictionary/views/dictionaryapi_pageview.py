import discord

from extensions.termdictionary.modals import DictionaryAPISendPageModal
from resources.customs import Bot


class DictionaryApi_PageView(discord.ui.View):
    def __init__(self, pages, pages_detailed, timeout=None):
        super().__init__()
        self.value = None
        self.timeout = timeout
        self.page = 0
        self.pages = pages
        self.pages_detailed = pages_detailed

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.blurple)
    async def previous(self, itx: discord.Interaction[Bot], _button: discord.ui.Button):
        self.page -= 1
        if self.page < 0:
            self.page = len(self.pages) - 1
        embed = self.pages[self.page]
        embed.set_footer(text="page: " + str(self.page + 1) + " / " + str(int(len(self.pages))))
        await itx.response.edit_message(embed=embed)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.blurple)
    async def next(self, itx: discord.Interaction[Bot], _button: discord.ui.Button):
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

    @discord.ui.button(label='Send publicly', style=discord.ButtonStyle.gray)
    async def send_publicly(self, itx: discord.Interaction[Bot], _button: discord.ui.Button):
        self.value = 1
        embed = self.pages[self.page]
        await itx.response.edit_message(content="Sent successfully!", embed=None)
        await itx.followup.send(f"{itx.user.mention} shared a dictionary entry!", embed=embed,
                                ephemeral=False, allowed_mentions=discord.AllowedMentions.none())
        self.stop()

    @discord.ui.button(label='Send one entry', style=discord.ButtonStyle.gray)
    async def send_single_entry(self, itx: discord.Interaction[Bot], _button: discord.ui.Button):
        self.value = 2

        send_one = DictionaryAPISendPageModal(self.pages_detailed[self.page])
        await itx.response.send_modal(send_one)
        await send_one.wait()
        if send_one.value in [None, 9]:
            pass
        else:
            # # pages_detailed = [ [result_id: int,   term: str,   type: str,   value: str],    [...], [...] ]
            page = self.pages_detailed[self.page][send_one.id]
            # # page = [result_id: int,   term: str,   type: str,   value: str]
            embed = discord.Embed(color=8481900, title=page[1])
            embed.add_field(name=page[2],
                            value=page[3],
                            inline=False)
            await itx.followup.send(f"{itx.user.mention} shared a section of a dictionary entry! (item {page[0]})",
                                    embed=embed, allowed_mentions=discord.AllowedMentions.none())

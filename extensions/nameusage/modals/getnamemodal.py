import discord


class GetNameModal(discord.ui.Modal, title="Search page with word"):
    def __init__(self, pages, embed_title, timeout=None):
        super().__init__()
        self.value = None
        self.timeout = timeout
        self.embed_title = embed_title
        self.pages = pages
        self.page = None

        self.word = None
        self.question_text = discord.ui.TextInput(
            label='What word to look up in the server name list?',
            placeholder="The word you want to look up",
            # style=discord.TextStyle.short,
            # required=True
        )
        self.add_item(self.question_text)

    async def on_submit(self, itx: discord.Interaction):
        self.value = 9  # failed; placeholder
        self.word = self.question_text.value.lower()
        for page_id in range(len(self.pages)):
            # self.pages[page_id] returns ['15 nora\n13 rose\n9 brand\n8
            #  george\n4 rina\n3 grace\n2 eliza\n','_']
            # split at \n and " " to get [["15", "nora"],
            #  ["13", "rose"], ["9", "brand"], ["8", "george"]]
            #  and compare self.word with the names.
            if (self.word in [name.split(" ")[-1]
                              for name in self.pages[page_id].split("\n")]):
                self.page = int(page_id / 2)
                break
        else:
            await itx.response.send_message(
                content=f"I couldn't find '{self.word}' in any of the pages! "
                        f"Perhaps nobody chose this name!",
                ephemeral=True)
            return
        result_page = self.pages[self.page * 2]
        result_page2 = self.pages[self.page * 2 + 1]
        result_page = result_page.replace(f" {self.word}\n",
                                          f" **__{self.word}__**\n")
        result_page2 = result_page2.replace(f" {self.word}\n",
                                            f" **__{self.word}__**\n")
        embed = discord.Embed(color=8481900, title=self.embed_title)
        embed.add_field(name="Column 1", value=result_page)
        embed.add_field(name="Column 2", value=result_page2)
        embed.set_footer(
            text="page: "
                 + str(self.page + 1)
                 + " / "
                 + str(int(len(self.pages) / 2))
        )
        await itx.response.edit_message(embed=embed)
        self.value = 1
        self.stop()

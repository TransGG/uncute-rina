import discord

from resources.customs import Bot


class GetNameModal(discord.ui.Modal, title="Search page with word"):
    def __init__(
            self,
            pages,
            timeout: float | None = None
    ):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.page: int | None = None
        self.return_interaction: discord.Interaction[Bot] | None = None
        self.question_text = discord.ui.TextInput(
            label='What word to look up in the server name list?',
            placeholder="The word you want to look up",
            # style=discord.TextStyle.short,
            # required=True
        )
        self.add_item(self.question_text)

    async def on_submit(  # type: ignore (Interaction vs. Interaction[Bot])
            self,
            itx: discord.Interaction[Bot]
    ):
        word = self.question_text.value.lower()
        for page_id in range(len(self.pages)):
            # 1. self.pages[page_id] returns ['15 nora\n13 rose\n9
            #    brand\n8 george\n4 rina\n3 grace\n2 eliza\n','_']
            # 2. Split at \n and " " to get [["15", "nora"],
            #    ["13", "rose"], ["9", "brand"], ["8", "george"]]
            # 3. And compare the word with the names.
            if (word in [name.split(" ")[-1]
                         for name in self.pages[page_id].split("\n")]):
                self.page = int(page_id / 2)
                self.return_interaction = itx
                break
        else:
            await itx.response.send_message(
                content=f"I couldn't find '{word}' in any of the pages! "
                        f"Perhaps nobody chose this name!",
                ephemeral=True)
            return

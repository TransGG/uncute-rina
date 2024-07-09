import discord


class JumpToPageModal_HelpCommands_Help(discord.ui.Modal, title="Go to help page"):
    def __init__(self, page_count, timeout=None):
        super().__init__()
        self.value = None # itx if valid input is given, else None
        self.timeout = timeout
        self.page = None # numeric input, or None if non-numeric input (can be out of range)
        self.page_count = page_count

        self.question_text = discord.ui.TextInput(label='What help page do you want to jump to?',
                                                  placeholder=f"2",
                                                  # style=discord.TextStyle.short, required=True
                                                  )
        self.add_item(self.question_text)

    async def on_submit(self, itx: discord.Interaction):
        if not self.question_text.value.isnumeric():
            await itx.response.send_message("Error: Invalid number.\n"
                                            "\n"
                                            "This button lets you jump to a help page (number). To see what kinds of help pages there are, go to the index page (page 2, or click the :clipboard: button).\n"
                                            "An example of a help page is page 3: `Utility`. To go to this page, you can either use the previous/next buttons (◀️ and ▶️) to navigate there, or click the 🔢 button: This button opens a modal.\n"
                                            "In this modal, you can put in the page number you want to jump to. Following from our example, if you type in '3', it will bring you to page 3; `Utility`.\n"
                                            "Happy browsing!", ephemeral=True)
            return
        else:
            self.page = int(self.question_text.value)

            if self.page not in self.page_indexes:
                if self.page > self.page_indexes[-1]:
                    relative_page_location_details = f" (nearest pages to `{self.page}` are `{self.page_indexes[-1]}` and `{self.page_indexes[0]}`)"
                elif self.page < self.page_indexes[0]:
                    relative_page_location_details = f" (nearest pages to `{self.page}` are `{self.page_indexes[0]}` and `{self.page_indexes[-1]}`)"
                else:
                    min_index = self.page
                    max_index = self.page
                    while min_index not in self.page_indexes:
                        min_index -= 1
                    while max_index not in self.page_indexes:
                        max_index += 1
                    relative_page_location_details = f" (nearest pages to `{self.page}` are `{min_index}` and `{max_index}`)"
                await itx.response.send_message(f"Error: Number invalid. Please go to a valid help page" + relative_page_location_details + ".", ephemeral=True)
                return

            #self.page = self.page-1 # turn page number into index number
        self.value = itx
        self.stop()

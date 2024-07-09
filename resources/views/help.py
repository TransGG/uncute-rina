import discord
from resources.customs.help import HelpPage
from resources.customs.bot import Bot
from resources.modals.help import JumpToPageModal_HelpCommands_Help
from resources.utils.stringhelper import replace_string_command_mentions


class PageView_HelpCommands_Help(discord.ui.View):
    def __init__(self, pages: dict[int, HelpPage], start_page: int, client: Bot, timeout: float=None):
        super().__init__()
        self.timeout = timeout
        self.page    = start_page
        self.pages   = pages
        self.client = client

    async def update_page(self, itx: discord.Interaction):
        page_details = self.pages[self.page]

        embed = discord.Embed(color= discord.Color.from_hsv((180 + self.page*10)/360, 0.4, 1),
                              title=page_details["title"],
                              description=replace_string_command_mentions(page_details["description"], self.client))
        if "fields" in page_details:
            for field in page_details["fields"]:
                embed.add_field(name  = replace_string_command_mentions(field[0], self.client), 
                                value = replace_string_command_mentions(field[1], self.client), 
                                inline = False)
        embed.set_footer(text="page: "+str(self.page))

        await itx.response.edit_message(embed=embed)

    #region Buttons

    @discord.ui.button(emoji='📋', style=discord.ButtonStyle.gray) # index
    async def go_to_index(self, itx: discord.Interaction, _button: discord.ui.Button):
        self.page = 1 # page 2, but index 1
        await self.update_page(itx)

    @discord.ui.button(emoji='◀️', style=discord.ButtonStyle.blurple) # previous
    async def previous(self, itx: discord.Interaction, _button: discord.ui.Button):
        # get current page, find the index of it, subtract 1 from that index, and find the related page to match
        page_indexes = sorted(list(self.pages)) # sorting may be unnecessary, since it should already be sorted.
        current_page_index = page_indexes.index(self.page)
        if current_page_index - 1 < page_indexes[0]: # below lowest index
            self.page = page_indexes[-1] # set to highest index
        else:
            self.page = page_indexes[current_page_index - 1]

        await self.update_page(itx)

    @discord.ui.button(emoji='▶️', style=discord.ButtonStyle.blurple) # next
    async def next(self, itx: discord.Interaction, _button: discord.ui.Button):
        # get current page, find the index of it, add 1 to that index, and find the related page to match
        page_indexes = sorted(list(self.pages)) # sorting may be unnecessary, since it should already be sorted.
        current_page_index = page_indexes.index(self.page)
        if current_page_index + 1 > page_indexes[-1]: # above highest index
            self.page = page_indexes[0] # set to lowest index
        else:
            self.page = page_indexes[current_page_index + 1]

        await self.update_page(itx)

    @discord.ui.button(emoji='🔢', style=discord.ButtonStyle.gray) # go to page
    async def go_to_page(self, itx: discord.Interaction, _button: discord.ui.Button):
        jump_page_modal = JumpToPageModal_HelpCommands_Help(len(self.pages))
        await itx.response.send_modal(jump_page_modal)

        await jump_page_modal.wait()
        if jump_page_modal.value == None:
            pass
        else:
            self.page = jump_page_modal.page
            await self.update_page(jump_page_modal.value)

    #endregion Buttons

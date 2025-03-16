import discord
import random  # for random help page jump page number placeholder

from resources.customs.bot import Bot
from resources.modals.generics import SingleLineModal
from resources.utils.stringhelper import replace_string_command_mentions
from resources.views.generics import PageView, create_simple_button

from extensions.help.helppage import HelpPage


def generate_help_page_embed(page: HelpPage, page_number: int, client: Bot) -> discord.Embed:
    """
    Helper function to generate an embed for a specific help page. This command is mainly to
     prevent inconsistencies between the /help calling and updating functions.
    Page fields are appended after the description, in the order they are given in the list.

    Parameters
    -----------
    page: :class:`HelpPage`
        The help page to reference.
    page_number: :class:`int`
        The page number of the help page. This number is added as footer, but is also used for the
         hue (HSV) value of the embed color.
    client: :class:`Bot`
        The bot instance for get_command_mention().

    Returns
    --------
    :class:`discord.Embed`:
        An embed of the given help page.
    """
    embed = discord.Embed(color=discord.Color.from_hsv((180 + page_number * 10) / 360, 0.4, 1),
                          title=page["title"],
                          description=replace_string_command_mentions(page["description"], client))
    if "fields" in page:
        for field in page["fields"]:
            embed.add_field(name=replace_string_command_mentions(field[0], client),
                            value=replace_string_command_mentions(field[1], client),
                            inline=False)
    embed.set_footer(text="page: " + str(page_number))
    return embed


def get_nearest_help_pages_from_page(page: int, pages: list[int]) -> tuple[int, int]:
    """
    Get the two nearest page numbers to a given page number.

    Parameters
    -----------
    page: :class:`int`
        The page number to get the two nearest page numbers for.
    pages: :class:`list[int]`
        A (sorted) list of page numbers to reference (e.g.
        `[1, 2, 3, 4, 5, 6, 10, 11, 12, 21, 22, 23, 31, 32, 101, 111, 112]`)

    Returns
    --------
    :class:`tuple[int, int]`
        The two nearest page numbers. The first is found by looking before, the second looks ahead.
        If looping around, [0] may be greater than [1].
    """
    if page > pages[-1]:
        return pages[-1], pages[0]
    elif page < pages[0]:
        return pages[0], -1
    else:  # page is between two other pages
        min_index = page
        max_index = page
        while min_index not in pages:
            min_index -= 1
        while max_index not in pages:
            max_index += 1
        assert min_index != max_index, (f"'min_index' ({min_index}) and 'max_index' ({max_index}) should point to "
                                        f"the two nearest help pages to 'page' ({page}), being the same implies "
                                        f"the page was in-range in the first place.")
        return min_index, max_index


class HelpPageView(PageView):
    async def update_page(self, itx: discord.Interaction, view: PageView) -> None:
        page_key = list(self.pages)[self.page]
        embed = generate_help_page_embed(self.pages[page_key], page_key, self.client)
        await itx.response.edit_message(
            embed=embed,
            view=view
        )

    # region buttons
    @discord.ui.button(emoji="📋", style=discord.ButtonStyle.gray)
    async def go_to_index(self, itx: discord.Interaction, _: discord.ui.Button):
        self.page = 1  # page 2, but index 1
        self.update_button_colors()
        await self.update_page(itx, self)

    @discord.ui.button(emoji="🔢", style=discord.ButtonStyle.gray)
    async def jump_to_page(self, itx: discord.Interaction, _: discord.ui.Button):
        help_page_indexes = list(self.pages)
        jump_page_modal = SingleLineModal(
            "Jump to a help page",
            "What help page do you want to jump to?",
            placeholder=str(random.choice(help_page_indexes))
        )
        await itx.response.send_modal(jump_page_modal)
        await jump_page_modal.wait()
        if jump_page_modal.itx is None:
            return

        try:
            if not jump_page_modal.question_text.value.isnumeric():
                raise ValueError
            page_guess = int(jump_page_modal.question_text.value)
        except ValueError:
            await jump_page_modal.itx.response.send_message(
                "Error: Invalid number.\n"
                "\n"
                "This button lets you jump to a help page (number). To see what kinds of help "
                "pages there are, go to the index page (page 2, or click the 📋 button).\n"
                "An example of a help page is page 3: `Utility`. To go to this page, you can "
                "either use the previous/next buttons (◀️ and ▶️) to navigate there, or click "
                "the 🔢 button: This button opens a modal.\n"
                "In this modal, you can put in the page number you want to jump to. Following "
                "from our example, if you type in '3', it will bring you to page 3; `Utility`.\n"
                "Happy browsing!", ephemeral=True)
            return

        if page_guess not in help_page_indexes:
            min_index, max_index = get_nearest_help_pages_from_page(page_guess, help_page_indexes)
            relative_page_location_details = f" (nearest pages are `{min_index}` and `{max_index}`)."
            await jump_page_modal.itx.response.send_message(
                replace_string_command_mentions(
                    (f"This page (`{page_guess}`) does not exist! "
                     if page_guess != 404 else "`404`: Page not found!") +  # easter egg
                    f" {relative_page_location_details} Try %%help%% `page:1` or use the page keys "
                    f"to get to the right page number!",
                    self.client),
                ephemeral=True)
            return

        self.page = list(self.pages).index(page_guess)
        self.update_button_colors()
        await self.update_page(jump_page_modal.itx, self)
    # endregion buttons

    def __init__(self, client: Bot, first_page_key: int, page_dict: dict[int, HelpPage]) -> None:
        self.client = client
        self.pages = page_dict
        first_page_index = list(self.pages).index(first_page_key)
        super().__init__(first_page_index, len(self.pages) - 1, self.update_page)
        self._children.append(self._children.pop(1))

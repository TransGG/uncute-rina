import discord

from resources.customs import Bot
from resources.utils.stringhelper import replace_string_command_mentions

from extensions.help.helppage import HelpPage


def generate_help_page_embed(
        page: HelpPage,
        page_number: int,
        client: Bot
) -> discord.Embed:
    """
    Helper function to generate an embed for a specific help page. This
    command is mainly to prevent inconsistencies between the /help
    calling and updating functions. Page fields are appended after the
    description, in the order they are given in the list.

    :param page: The help page to reference.
    :param page_number: The page number of the help page. This number is
     added as footer, but is also used for the hue (HSV) value of the
     embed color.
    :param client: The bot instance for :py:meth:`Client.get_command_mention`.

    :return: An embed of the given help page.
    """
    embed = discord.Embed(
        color=discord.Color.from_hsv(
            h=(180 + page_number * 10) / 360,
            s=0.4,
            v=1
        ),
        title=page["title"],
        description=replace_string_command_mentions(
            page["description"],
            client
        ),
    )
    if "fields" in page:
        for field in page["fields"]:
            embed.add_field(
                name=replace_string_command_mentions(field[0], client),
                value=replace_string_command_mentions(field[1], client),
                inline=False
            )
    embed.set_footer(text="page: " + str(page_number))
    return embed


def get_nearest_help_pages_from_page(
        page: int,
        pages: list[int]
) -> tuple[int, int]:
    """
    Get the two nearest page numbers to a given page number.

    :param page: The page number to get the two nearest page
     numbers for.
    :param pages: A (sorted) list of page numbers to reference (e.g.
     `[1, 2, 3, 4, 5, 6, 10, 11, 12, 21, 22, 23, 31, 32, 101, 111, 112]`)

    :return: The two nearest page numbers. The first is found by looking
     before, the second looks ahead. If looping around, [0] may
     greater than [1].
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
        assert min_index != max_index, (
            f"'min_index' ({min_index}) and 'max_index' ({max_index}) should "
            f"point to the two nearest help pages to 'page' ({page}), being "
            f"the same implies the page was in-range in the first place."
        )
        return min_index, max_index

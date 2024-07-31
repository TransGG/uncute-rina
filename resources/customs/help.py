from __future__ import annotations
from typing import TypedDict
from resources.customs.bot import Bot
import discord
from resources.utils.stringhelper import replace_string_command_mentions


def generate_help_page_embed(page: HelpPage, page_number: int, client: Bot) -> discord.Embed:
    """
    Helper function to generate an embed for a specific help page. This command is mainly to prevent inconsistencies between the /help calling and updating functions.
    Page fields are appended after the description, in the order they are given in the list.

    Parameters
    -----------
    page: :class:`HelpPage`
        The help page to reference.
    page_number: :class:`int`
        The page number of the help page. This number is added as footer, but is also used for the hue (HSV) value of the embed color.
    client: :class:`Bot`
        The bot instance for get_command_mention().

    Returns
    --------
    :class:`discord.Embed`:
        An embed of the given help page.
    """
    embed = discord.Embed(color = discord.Color.from_hsv((180 + page_number*10)/360, 0.4, 1),
                          title = page["title"],
                          description = replace_string_command_mentions(page["description"], client))
    if "fields" in page:
        for field in page["fields"]:
            embed.add_field(name  = replace_string_command_mentions(field[0], client), 
                            value = replace_string_command_mentions(field[1], client), 
                            inline = False)
    embed.set_footer(text="page: "+str(page_number))
    return embed


class HelpPage(TypedDict):
    """
    A simple shell for a /help page, used for discord embeds

    Parameters
    -----------
    title: :class:`str`
        Typically the title of the embed.  
    description: :class:`str`
        Typically the description of the embed.
    fields: :class:`list[tuple[name, value]]`
        A list with tuples of the name and value of an embed field.  
        Note: Discord embeds only allow up to 10 fields.
    """
    title: str
    description: str
    fields: list[tuple[str,str]]
    staff_only: bool = False

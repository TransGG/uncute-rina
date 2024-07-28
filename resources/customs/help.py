from typing import TypedDict

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

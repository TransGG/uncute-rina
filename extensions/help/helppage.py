from typing import TypedDict


class HelpPage(TypedDict):
    """
    A simple shell for a /help page, used for discord embeds

    :param title: Typically the title of the embed.
    :param description: Typically the description of the embed.
    :param fields: A list with tuples of the name and value of an embed field.

    .. note::

        Discord embeds only allow up to 10 fields.
    """
    title: str
    description: str
    fields: list[tuple[str, str]]
    staff_only: bool

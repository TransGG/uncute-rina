from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from resources.customs import Bot


def replace_string_command_mentions(text: str, client: Bot) -> str:
    """
    Converts strings with "%%command%%" into a command mention
    (</command:12345678912345678>).

    :param text: The text in which to look for command mentions.
    :param client: The client with which to convert the command into
     a command mention.

    :return: The input text, with every command instance replaced with
     its matching command mention.

    .. note::

        If the command does not exist, it will fill the mention with
        "/command" instead of "</command:1>".
    """
    while "%%" in text:
        command_start_index = text.index("%%")
        command_end_index = text.index("%%", command_start_index + 2)
        command_string = text[command_start_index + 2: command_end_index]
        command_string = command_string.removeprefix("/")

        text = (text[:command_start_index]
                + client.get_command_mention(command_string)
                + text[command_end_index + 2:])
    return text


def ellipsize_string(text: str, max_length: int) -> str:
    """
    Add ellipses to a string if it's longer than **max_length**.

    Strings that are shorter than max_length stay unchanged.
     Strings that exceed max_length are trimmed and given ellipses at the end,
     giving them a length equal to max_length.

    :param text: The text to check length for.
    :param max_length: The maximum length the string may be.
    :return: A string with perhaps added ellipses.
    :raise ValueError: If the max_length parameter is less than 3:
     Can't replace text with "..." and achieve fewer than 3 characters.
    """
    if max_length < 3:
        raise ValueError("Can't ellipsize text to a size less than 3!")
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text

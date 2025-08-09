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
        if command_string.startswith("/"):
            command_string = command_string[1:]

        text = (text[:command_start_index]
                + client.get_command_mention(command_string)
                + text[command_end_index + 2:])
    return text

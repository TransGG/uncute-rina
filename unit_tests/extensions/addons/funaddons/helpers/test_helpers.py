import pytest
from unittest import mock
import discord

from extensions.addons.cogs.funaddons import (
    _product_of_list,
    _handle_awawa_reaction,
)


@pytest.mark.parametrize("query, expected", [
    ([1, 2, 3], 1*2*3),  # Positive
    ([-1, -2, -3], -1*-2*-3),  # Negative
    ([1.2, 0.3], 1.2*0.3),  # floats
    ([-1, 2, 3], -1*2*3),  # Mixed
    ([994, 943, 0], 0),  # Zero
    ([], 1),  # empty list
])
def test_product_of_list[T](
        query: list[T],
        expected: T,
) -> None:
    result = _product_of_list(query)
    assert result == expected


@pytest.mark.parametrize("content, react", [
    ("ababab", False),  # doesn't start and end with "a"
    ("abbaba", False),  # doesn't follow ababa pattern
    ("abababa", True),  # truly abababa
    ("awawawa", True),  # also awawawa
    ("ABABABA", True),  # OH MY GOD
    ("abababababababababababababababa", True),  # long but valid
    ("abwabwabwabwab", True),  # now we're getting in bean territory bwaa
    ("abawabawabawabawabawa", True),  # waba waba pacman moment
    ("meow", False),  # HEY THAT'S NOT A BWA!
    ("abwa", False),  # no that simply won't do
    ("bwaaaaaaaaaaaaaaa", False),  # nahh it's not an abwa
    ("abwaaaaaaaaaaaaaaa", True),  # that's more like it.
])
@pytest.mark.asyncio
async def test_handle_awawa_reaction(content, react) -> None:
    mock_message = mock.Mock(discord.Message)
    mock_message.content = content
    mock_emoji = mock.Mock(discord.Emoji)

    response = await _handle_awawa_reaction(mock_message, mock_emoji)
    assert response == react

    if react:
        mock_message.add_reaction.assert_called_once_with(mock_emoji)
    else:
        mock_message.add_reaction.assert_not_called()

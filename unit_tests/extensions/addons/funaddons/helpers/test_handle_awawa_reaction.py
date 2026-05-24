import pytest
from unittest import mock
import discord

from extensions.addons.cogs.funaddons import _handle_awawa_reaction


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
    ("meow meow meow meow meow meow", False),  # OH MY GOD MAKE IT STOP
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


@pytest.mark.parametrize("content", [
    "abababa",
    "abababb",
    "ababababababa",
    "abwabwabwabwab",
    "meow",
    "meowmeowmeowmeowmeowmeow",
])
@pytest.mark.asyncio
async def test_handle_awawa_reaction_blocked(content) -> None:
    mock_message = mock.Mock(discord.Message)
    mock_message.content = content
    mock_emoji = mock.Mock(discord.Emoji)

    class MockForbidden(discord.Forbidden):
        # Why can't I throw a mocked discord.Forbidden -_-
        def __init__(self):
            pass

    mock_message.add_reaction.side_effect = MockForbidden()

    response = await _handle_awawa_reaction(mock_message, mock_emoji)
    assert response == False
    # add_reaction does still get called once but fails: Forbidden mock

    # Test if a given input would have given a reaction.
    # If so, the previously raised exception should have also
    #  tried to give a reaction (but failed).
    # Otherwise, it would have just failed because it's not worth reacting to.
    mock_message.add_reaction.side_effect = None
    response = await _handle_awawa_reaction(mock_message, mock_emoji)
    if response:
        assert mock_message.add_reaction.call_count == 2
    else:
        assert mock_message.add_reaction.call_count == 0

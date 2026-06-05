import pytest
from unittest import mock
import discord

from extensions.addons.cogs.funaddons import _check_awawa_reaction


@pytest.mark.parametrize("content, react", [
    ("ababab", False),  # doesn't start and end with "a"
    ("abbaba", False),  # doesn't follow ababa pattern
    ("aaaaa", False),   # just aaaaaaa ;-;
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
    ("aaaaaaaaaaaaaaaaaa", False),  # hey this is just screaming...
])
def test_check_awawa_reaction(content, react) -> None:
    mock_message = mock.Mock(discord.Message)
    mock_message.content = content

    response = _check_awawa_reaction(mock_message)
    assert response == react

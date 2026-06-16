import discord
import discord.app_commands
import pytest

from resources.abc import ApiTokenDict
from resources.customs import Bot


def fake_api_token_dictionary() -> ApiTokenDict:
    # noinspection PyArgumentList
    return ApiTokenDict({
        "Equaldex": "",
        "MongoDB": "",
        "Open Exchange Rates": "",
        "Wolfram Alpha": "",
    })


def default_bot() -> Bot:
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    bot = Bot(
        fake_api_token_dictionary(),
        "0.0.0.0",
        rina_db=None,
        async_rina_db=None,
        intents=intents,
        command_prefix="/!\"@:\\#",
        # case_insensitive=True,
        # activity=discord.Game(name="with slash (/) commands!"),
        allowed_mentions=discord.AllowedMentions(everyone=False),
    )
    return bot


random_command_id = 1000


def get_random_snowflake() -> int:
    global random_command_id
    random_command_id += 1
    return random_command_id


def make_command(
        command_id: int,
        *,
        command_str: str,
        subcommand_str: str | None,
        subcommandgroup_str: str | None,
) -> discord.app_commands.AppCommand:
    command_base = {
        "id": command_id,
        "application_id": get_random_snowflake(),
        "name": "MISSING",
        "contexts": [],
        "integration_types": [],
        "version": get_random_snowflake()
    }

    command_option_base = {
        "name": "MISSING",
        "description": "",
        "type": -1,
        "options": []
    }

    command_data = command_base.copy()
    command_data["name"] = command_str
    command_data["description"] = ""
    command_data["type"] = 1
    command_data["options"] = []

    subcommand = None
    if subcommand_str is not None:
        subcommand = command_option_base.copy()
        subcommand["name"] = subcommand_str
        subcommand["type"] = 2

    if subcommandgroup_str is not None:
        assert subcommand is not None
        subcommandgroup = command_option_base.copy()
        subcommandgroup["name"] = subcommandgroup_str
        subcommandgroup["type"] = 1
        subcommandgroup["options"] = [subcommand]
        command_data["options"].append(subcommandgroup)  # type: ignore[attr-defined]
    elif subcommand_str is not None:
        command_data["options"].append(subcommand)  # type: ignore[attr-defined]

    return discord.app_commands.AppCommand(
        data=command_data,  # type: ignore[arg-type]
        state=None,
    )


@pytest.mark.parametrize("command_id, command, subcommand_group, subcommand, expected", [
    (10, "say", None, None, "</say:10>"),
    (109, "vctable", None, "mute", "</vctable mute:109>"),
    (1, "vctable", "edit", "mute", "</vctable edit mute:1>"),
])
def test_get_command_mention(
        command_id: int,
        command: str,
        subcommand_group: str | None,
        subcommand: str | None,
        expected: str,
) -> None:
    # Arrange
    bot = default_bot()

    commands = [
        make_command(
            command_id,
            command_str=command,
            subcommandgroup_str=subcommand_group,
            subcommand_str=subcommand,
        )
    ]
    bot.slash_command_list = commands

    command_string = command
    if subcommand_group is not None:
        command_string += f" {subcommand_group}"
    if subcommand is not None:
        command_string += f" {subcommand}"

    # Act
    out = bot.get_command_mention(command_string)

    # Assert
    assert out == expected


@pytest.mark.parametrize("command, subcommand_group, subcommand, expected", [
    ("say", None, None, "/say"),
    ("vctable", None, "mute", "/vctable mute"),
    ("vctable", "edit", "mute", "/vctable edit mute"),
])
def test_get_command_mention_no_commands(
        command: str,
        subcommand_group: str | None,
        subcommand: str | None,
        expected: str,
) -> None:
    # Arrange
    bot = default_bot()
    bot.slash_command_list = []

    command_string = command
    if subcommand_group is not None:
        command_string += f" {subcommand_group}"
    if subcommand is not None:
        command_string += f" {subcommand}"

    # Act
    out = bot.get_command_mention(command_string)

    # Assert
    assert out == expected

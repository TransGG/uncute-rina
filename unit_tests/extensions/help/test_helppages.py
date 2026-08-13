import typing

import pytest

from extensions.help.helppage import HelpPage
from extensions.help.helppages import aliases, help_pages
from extensions.help.utils import generate_help_page_embed
from unit_tests.utils import get_embed_issues
from unit_tests.utils.object import CustomObject

if typing.TYPE_CHECKING:
    from resources.customs.bot import Bot


def test_help_pages_integer_key() -> None:
    # Arrange
    invalid_keys = []

    # Act
    for page in help_pages:
        if type(page) is not int:
            invalid_keys.append(page)

    # Assert
    assert invalid_keys == [], "All help pages should have an integer key."


def test_help_pages_sorted() -> None:
    # Arrange
    page_keys = list(help_pages)

    # Act
    sorted_page_keys = sorted(page_keys)

    # Assert
    assert page_keys == sorted_page_keys, \
        "All help pages should be sorted by default."


def test_help_pages_attributes() -> None:
    # Arrange
    invalid_pages = []
    allowed_keys = HelpPage.__annotations__

    for page_number, helppage in help_pages.items():
        for section_name in helppage:
            if section_name not in allowed_keys:
                invalid_pages.append((page_number, section_name))

    assert invalid_pages == [], \
        ("All pages should only have fields that are one of these "
         "attributes: title, description, fields, staff_only")


def test_embed_lengths() -> None:
    # Arrange
    fake_client: Bot = CustomObject()  # type: ignore[assignment]

    def fake_get_command_mention(command_string: str) -> str:
        fake_id = "0" * 19  # discord ids are roughly this length, I guess?
        return f"</{command_string}:{fake_id}>"

    fake_client.get_command_mention = fake_get_command_mention   # type: ignore[method-assign]

    for page_number, helppage in help_pages.items():
        page_embed = generate_help_page_embed(
            helppage, page_number, fake_client)

        potential_issues, _ = get_embed_issues(page_embed)

        if potential_issues:
            issues = (f"Page '{page_number}' embed issues:\n"
                      f"- " + "\n- ".join(potential_issues))
            pytest.fail(issues)


def test_aliases_for_each_help_page() -> None:
    assert len(aliases) == len(help_pages)  # all pages have an alias

    for alias_page in aliases:
        assert alias_page in help_pages, alias_page


def test_each_alias_list_is_not_empty() -> None:
    empty_alias_lists = []
    for page, alias in aliases.items():
        if len(alias) == 0:
            empty_alias_lists.append(page)

    assert empty_alias_lists == []

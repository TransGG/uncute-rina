import pytest

from unit_tests.object import CustomObject
from unit_tests.utils import get_embed_issues

from extensions.help.helppage import HelpPage
from extensions.help.helppages import help_pages
from extensions.help.utils import generate_help_page_embed


def test_help_pages_integer_key():
    # Arrange
    invalid_keys = []

    # Act
    for page in help_pages:
        if type(page) is not int:
            invalid_keys.append(page)

    # Assert
    assert invalid_keys == [], "All help pages should have an integer key."


def test_help_pages_sorted():
    # Arrange
    page_keys = list(help_pages)

    # Act
    sorted_page_keys = sorted(page_keys)

    # Assert
    assert page_keys == sorted_page_keys, "All help pages should be sorted by default."


def test_help_pages_attributes():
    # Arrange
    invalid_pages = []
    allowed_keys = HelpPage.__annotations__

    for page_number, helppage in help_pages.items():
        for section_name in helppage:
            if section_name not in allowed_keys:
                invalid_pages.append((page_number, section_name))

    assert invalid_pages == [], \
        "All pages should only have fields that are one of these attributes: title, description, fields, staff_only"


def test_embed_lengths():
    # Arrange
    fake_client = CustomObject()

    def fake_get_command_mention(cmd: str):
        return "</" + cmd + ":" + "0"*19 + ">"

    fake_client.get_command_mention = fake_get_command_mention

    for page_number, helppage in help_pages.items():
        page_embed = generate_help_page_embed(helppage, page_number, fake_client)

        potential_issues = get_embed_issues(page_embed)

        if potential_issues:
            issues = f"Page '{page_number}' embed issues:\n- " + "\n- ".join(potential_issues)
            pytest.fail(issues)

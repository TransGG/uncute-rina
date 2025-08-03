import pytest

import discord
from types import UnionType, NoneType
import typing

from extensions.settings.objects import (
    ServerAttributes,
    ServerAttributeIds,
    EnabledModules,
    AttributeKeys, get_attribute_type, MessageableGuildChannel,
)


def test_matching_keys():
    # Arrange
    at = ServerAttributes.__annotations__.keys()
    atid = ServerAttributeIds.__annotations__.keys()
    atk = set(i for i in dir(AttributeKeys) if not i.startswith("_"))

    # Assert
    assert at == atid
    assert set(at) == atk
    # for assurance
    assert sorted(set(at)) == sorted(at)


@pytest.mark.parametrize("attribute", ServerAttributes.__annotations__.keys())
def test_attribute_types(attribute: str):
    attribute_type = ServerAttributes.__annotations__[attribute]

    origin = typing.get_origin(attribute_type)
    assert (origin is UnionType
            or origin is list)

    if origin is UnionType:
        # It must be of the form "type1 | type2 | ... | None".
        #  with at least 1 type and 1 None.
        # The given types cannot be lists or further nested unions.
        has_none = False
        for sub_type in typing.get_args(attribute_type):
            assert sub_type is not list
            assert sub_type is not UnionType
            if sub_type is NoneType:
                has_none = True
        assert has_none
    elif origin is list:
        # Lists must not contain `None`s. Only the expected types.
        #  It also shouldn't contain nested lists.
        # It should not contain unions, but instead have every possible
        #  subtype as argument::
        #
        #     list[str, int, bool] instead of
        #     list[str | int | bool].
        #
        for sub_type in typing.get_args(attribute_type):
            assert sub_type is not NoneType
            assert sub_type is not list

            if sub_type is UnionType:
                for list_subtype in typing.get_args(sub_type):
                    assert typing.get_origin(list_subtype) is not list
                    assert typing.get_origin(list_subtype) is not UnionType
                    assert typing.get_origin(list_subtype) is not NoneType
    else:
        pytest.fail(f"Invalid origin type: {origin.__name__}")


@pytest.mark.parametrize("attribute, expected_output", [
    (AttributeKeys.parent_server, ([discord.Guild], False)),
    (AttributeKeys.developer_request_channel,
     ([discord.TextChannel], False)),
    (AttributeKeys.log_channel, ([MessageableGuildChannel], False)),
    (AttributeKeys.vctable_prefix, ([str], False)),
    (AttributeKeys.admin_roles, ([discord.Role], True)),  # list
])
def test_get_attribute_types(
        attribute: str,
        expected_output: tuple[list[type] | None, bool]
):
    assert get_attribute_type(attribute) == expected_output


def test_attribute_key_attribute_match_value():
    attribute_keys = [i for i in dir(AttributeKeys) if not i.startswith("_")]
    incorrect_keys = []

    for attribute_key in attribute_keys:
        if getattr(AttributeKeys, attribute_key) != attribute_key:
            incorrect_keys.append(attribute_key)

    assert incorrect_keys == []


def test_no_bad_attribute_names():
    # Arrange
    invalid_names = []

    # Act
    for attribute_key in ServerAttributes.__annotations__:
        if "." in attribute_key or attribute_key.startswith("$"):
            invalid_names.append(attribute_key)

    # Assert
    if invalid_names:
        pytest.fail("Attributes should not contain a '.' or start with '$', "
                    "because MongoDB won't let you have keys with those "
                    "characters. The names in question:\n- "
                    + "\n- ".join(invalid_names))


def test_no_bad_attribute_id_names():
    # Arrange
    invalid_names = []

    # Act
    for attribute_id_key in ServerAttributeIds.__annotations__:
        if "." in attribute_id_key or attribute_id_key.startswith("$"):
            invalid_names.append(attribute_id_key)

    # Assert
    if invalid_names:
        pytest.fail("Attribute Ids should not contain a '.' or start with "
                    "'$', because MongoDB won't let you have keys with those "
                    "characters. The names in question:\n- "
                    + "\n- ".join(invalid_names))


def test_no_bad_module_names():
    # Arrange
    invalid_names = []

    # Act
    for enabled_module_key in EnabledModules.__annotations__:
        if "." in enabled_module_key or enabled_module_key.startswith("$"):
            invalid_names.append(enabled_module_key)

    # Assert
    if invalid_names:
        pytest.fail("Module keys should not contain a '.' or start with '$', "
                    "because MongoDB won't let you have keys with those "
                    "characters. The names in question:\n- "
                    + "\n- ".join(invalid_names))


def test_all_modules_bools():
    # Arrange
    module_types = typing.get_type_hints(EnabledModules)
    invalid_types = []

    # Act
    for module, module_type in module_types.items():
        if module_type != bool:
            invalid_types.append(module)

    # Assert
    assert invalid_types == []

import pytest

import typing

from extensions.settings.objects import (
    ServerAttributes,
    ServerAttributeIds,
    EnabledModules,
    AttributeKeys,
)


inputs = [
    {
        "_id": "62ae5233b537066a27c729fa",
        "guild_id": 985931648094834798,
        "vcHub": 986295510103121990,
        "vcLog": 986304081234624554,
        "vcCategory": 986295362715267153,
        "vcNoMic": 985936782740848671,
        "starboardChannel": 1043639116341968927,
        "starboardCountMinimum": 1,
        "starboardBlacklistedChannels": [0],
        "starboardDownvoteInitValue": 99,
        "starboardEmoji": 987791037684662302
    },
    {
        "_id": "63bc74ce4def2a2bad0a7e50",
        "guild_id": 981615050664075404,
        "vcHub": 1085617780696567818,
        "vcLog": 1062396920187863111,
        "vcCategory": 1085617535296229416,
        "vcNoMic": 1085617711628959775,
        "starboardChannel": 1108819731542180031,
        "starboardCountMinimum": 1,
        "bumpChannel": 1101557685293416560,
        "bumpRole": 1101452891572666439,
        "pollReactionsBlacklist": [1046086282377429083],
        "bumpBot": 302050872383242240,
        "starboardBlacklistedChannels": [1046086440011964487],
        "starboardEmoji": 989259317146439690,
        "starboardDownvoteInitValue": 1,
    },
    {
        "_id": "6497796ff5117edf93f50346",
        "guild_id": 1122297355669086348,
        "vcLog": 1122304251184545812,
        "starboardEmoji": 1122305972870856805,
        "starboardChannel": 1122305224388911124,
        "starboardCountMinimum": 5,
        "starboardBlacklistedChannels": [1122304251184545812],
        "starboardDownvoteInitValue": 10,
        "vcHub": 1122306424740003882,
        "vcCategory": 1122304219974737930,
        "vcNoMic": 1122304251184545812,
        "pollReactionsBlacklist": [1122304251184545812],
    },
    {
        "_id": "65841edad45f30a9ca021ad7",
        "guild_id": 1034084825482661939,
        "vcLog": 1187353118757884015,
        "vcActivityLogChannel": 1187344559940833420,
    }
]


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

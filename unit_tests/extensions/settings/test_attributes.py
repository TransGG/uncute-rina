import pytest

from extensions.settings.objects import ServerAttributes, ServerAttributeIds


def test_matching_keys():
    # Arrange
    missing = []
    at = list(ServerAttributes.__required_keys__) + list(ServerAttributes.__optional_keys__)
    atid = list(ServerAttributeIds.__required_keys__) + list(ServerAttributeIds.__optional_keys__)

    # Act
    for i in at:
        for j in atid:
            if i not in atid and i not in missing:
                missing.append(i)
            if j not in at and j not in missing:
                missing.append(j)

    # Assert
    assert missing == []

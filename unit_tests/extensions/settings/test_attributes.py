import pytest

from extensions.settings.objects import ServerAttributes, ServerAttributeIds, ServerSettings


def test_matching_keys():
    # Arrange
    at = ServerAttributes.__required_keys__.union(ServerAttributes.__optional_keys__)
    atid = ServerAttributeIds.__required_keys__.union(ServerAttributeIds.__optional_keys__)

    # Assert
    assert at == atid

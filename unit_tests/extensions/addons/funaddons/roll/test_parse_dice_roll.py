import pytest
from extensions.addons.roll import _parse_dice_roll
# AI wrote the template for this file :)
# (mainly me not yet knowing how to write parameterized tests)
# (Woah, especially parameterized exceptions. Neat.)


@pytest.mark.parametrize("query, expected", [
    ("2d6", (2, 6)),
    ("1d20", (1, 20)),
    ("0d6", (0, 6)),  # Zero dice
    ("-3d6", (-3, 6)),  # Negative dice
    ("1d-2", (1, -2)),  # Negative faces
    ("12345678901234567890", (12345678901234567890, None)),  # big number
    ("99999999999d88888888888", (99999999999, 88888888888)),  # big dice rolls
    ("4", (4, None)),  # small constant
    ("123", (123, None)),  # larger constant
    ("-456", (-456, None)),  # negative constant
    ("0", (0, None)),  # zero.
    ("+789", (789, None)),  # Leading '+' is allowed by int()
    # ^ dang, AI, that's nasty. But my program doesn't parse
    #  it that way, haha.
])
def test_valid_cases(query, expected):
    assert _parse_dice_roll(query) == expected


@pytest.mark.parametrize("query, expected_exception", [
    ("AAAA", ValueError),  # Invalid input entirely
    ("AA123", ValueError),  # ^
    ("123AA", ValueError),  # ^
    ("dddd", ValueError),  # Invalid input with multiple d's
    ("AdB", ValueError),  # Invalid left and right parts.
    # should raise an exception for whichever first error it encounters.
    ("Ad99", ValueError),  # Invalid dice
    ("d99", ValueError),  # Empty dice part
    ("99dA", ValueError),  # Invalid faces
    ("99d", ValueError),  # Empty faces part
    ("99d99d99", ValueError),  # Multiple 'd's in right format
    ("", ValueError),  # Empty input
    ("9-9d99", ValueError),  # Invalid characters in dice part
    ("99d9-9", ValueError),  # Invalid characters in faces part
])
def test_invalid_cases(query, expected_exception):
    with pytest.raises(expected_exception):
        _parse_dice_roll(query)

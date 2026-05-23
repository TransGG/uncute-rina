import pytest
from unittest import mock
from extensions.addons.roll import generate_roll
import random
# AI wrote the template for this file
# (mainly me not yet knowing how best to mock other libraries and
#  functions. I must say, this is pretty neat.)


@pytest.mark.parametrize("query, expected", [
    ("5", [5]),  # Constant value
    ("-5", [-5]),  # Negative constant value
    ("2d6", [1, 1]),  # Default random values
    ("1d20", [1]),  # Single roll
    ("-3d6", [-1, -1, -1]),  # Negative dice
    ("0d6", []),  # Zero dice
])
def test_generate_roll_cases(
        query: str,
        expected: list[int],
) -> None:
    with mock.patch.object(random, 'randint', return_value=1):
        result = list(generate_roll(query))
        assert result == expected


@pytest.mark.parametrize("query, dice_count", [
    ("2d6", 2),
    ("1d100", 1),
    ("-4d6", 4),
])
def test_roll_count(query: str, dice_count: int) -> None:
    with mock.patch.object(random, 'randint', return_value=1):
        result = list(generate_roll(query))
        assert len(result) == dice_count


@pytest.mark.parametrize("query, min_val, max_val", [
    ("2d6", 1, 6),
    ("1d20", 1, 20),
    ("-3d6", -6, -1),  # Range adjusted for negative
])
def test_roll_range(query: str, min_val: int, max_val: int) -> None:
    with mock.patch.object(random, 'randint', return_value=1):
        result = list(generate_roll(query))
        assert all(min_val <= x <= max_val for x in result)


def test_negative_dice_negates_values() -> None:
    with mock.patch.object(random, 'randint', return_value=5):
        result = list(generate_roll("-2d6"))
        assert result == [-5, -5]

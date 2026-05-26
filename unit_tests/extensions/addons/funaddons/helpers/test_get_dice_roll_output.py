import pytest
from unittest import mock
import random
from extensions.addons.cogs.funaddons import _get_dice_roll_output


@pytest.mark.parametrize("dice, faces, mod, expected", [
    (1, 1, None,
     "You rolled 1 die with 1 face: 1"),
    (1, 1, 1,
     "You rolled 1 die with 1 face and a modifier of 1:\n(1) + 1  =  2"),
    (6, 6, 6,
     "You rolled 6 dice with 6 faces and a modifier of 6:\n(1 + 1 + 1 + 1 + 1 + 1) + 6  =  12"),
    (6, 6, None,
     "You rolled 6 dice with 6 faces:\n1 + 1 + 1 + 1 + 1 + 1  =  6"),
    (1, 10000, None,
     "You rolled 1 die with 10,000 faces: 1"),
])
def test_get_dice_roll_output_short(
        dice: int,
        faces: int,
        mod: int | float | None,
        expected: str
) -> None:
    with mock.patch.object(random, 'randint', return_value=1):
        output, too_long = _get_dice_roll_output(dice, faces, mod)
        assert output == expected
        assert too_long == False


@pytest.mark.parametrize("dice, faces, mod, expected", [
    (10000, 10000, None,
        "You rolled 10,000 dice with 10,000 faces:\n"
        "With this many numbers, I've simplified it a little. "
        "You rolled `10,000`.\n"
        "You rolled '1'x10000"),
])
def test_get_dice_roll_output_long_short(
        dice: int,
        faces: int,
        mod: int | float | None,
        expected: str
) -> None:
    with mock.patch.object(random, 'randint', return_value=1):
        output, too_long = _get_dice_roll_output(dice, faces, mod)
        assert output == expected
        assert too_long == False


def test_get_dice_roll_output_much_too_long() -> None:
    dice = 10000
    faces = 10000
    mod = None

    expected = (
        "You rolled 10,000 dice with 10,000 faces:\n"
        "With this many numbers, I've simplified it a little. "
        f"You rolled `{(10000*(1+10000))//2:,}`.\n"
        # sum from 1 to 10000 due to custom 'get_random_output' function
    )
    random_output = 0

    def get_random_output(*_):
        nonlocal random_output
        random_output += 1
        return random_output

    with mock.patch.object(random, 'randint', side_effect=get_random_output):
        output, too_long = _get_dice_roll_output(dice, faces, mod)
        assert output == expected
        # It has been compressed to a size where it is short enough again lol.
        assert too_long == False


def test_get_dice_roll_output_long_long() -> None:
    dice = 100
    faces = 1
    mod = None
    random_output = 0
    # I don't really care about the string output.
    # It just compresses it into '1'x1 etc. for 1 to 100
    # But doesn't compress it further because it's just barely long enough.

    def get_random_output(dice, faces):
        nonlocal random_output
        random_output += 1
        return random_output

    with mock.patch.object(random, 'randint', side_effect=get_random_output):
        output, too_long = _get_dice_roll_output(dice, faces, mod)
        assert too_long == True

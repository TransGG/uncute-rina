import pytest
from extensions.addons.roll import _validate_dice_and_faces


@pytest.mark.parametrize("dice, faces, expected", [
    (2, 6, True),  # simple 2d6 :D
    (99, 99, True),  # normal number of dice/faces
    (0, 99, True),  # zero dice
    (-99, 99, True),  # negative dice
    (99, 1, True),  # low but non-zero faces
    # Zero or negative faces won't be accepted, because I don't think
    #  dice should have negative faces.
    (999999, 99, True),  # almost a million dice
    (99, 999999, True),  # almost a million faces
])
def test_valid_cases(dice: int, faces: int, expected: bool):
    assert _validate_dice_and_faces(dice, faces) == expected


@pytest.mark.parametrize("dice, faces, expected_exception", [
    (0, 0, ValueError),  # Zero faces
    (0, -1, ValueError),  # Negative faces
    (1000000, 1, OverflowError),  # a million dice
    (0, 1000000, OverflowError),  # a million faces
])
def test_invalid_cases(dice: int, faces: int, expected_exception):
    with pytest.raises(expected_exception):
        _validate_dice_and_faces(dice, faces)

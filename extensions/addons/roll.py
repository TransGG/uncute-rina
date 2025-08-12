import collections.abc
import random


def _parse_dice_roll(query: str) -> tuple[int, int | None]:
    """Split the query into dice and faces components."""
    # print(query)
    parts: list[str | int] = query.split("d")
    # 2d4 = ["2","4"]
    # 2d3d4 = ["2","3","4"] (huh?)
    # 4 = 4
    # [] (huh?)
    if len(parts) > 2:
        raise ValueError("Can't have more than 1 'd' in the "
                         "query of your die!")
    elif len(parts) == 2:
        return (
            _parse_number("dice", parts[0]),
            _parse_number("faces", parts[1])
        )
    else:
        assert len(parts) == 1, (
            f"Expected the dice roll to have 1 part, but it had "
            f"{len(parts)} instead: {parts}"
        )
        # length of `parts` can't be zero if .split() is provided with a
        #  delimiter. "".split("d") will return a list with
        #  1 string: [""]. Only .split() with a whitespace string and
        #  without split parameters can return an empty list:
        #  "abcdef".split() -> []
        return _parse_number("dice", parts[0]), None


def _parse_number(source: str, value: str) -> int:
    """Parse a string to integer with error handling."""
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Invalid number format for {source}: {value}")


def _validate_dice_and_faces(
        dice: int, faces: int
) -> bool:
    """Confirm the values of the dice are within range"""
    if faces <= 0:
        raise ValueError("Faces count must be positive")
    if dice >= 1000000:
        raise OverflowError(
            f"Sorry, if I let you roll `{dice:,}` dice, the universe will "
            f"implode, and Rina will stop responding to commands. "
            f"Please stay below 1 million dice..."
        )
    if faces >= 1000000:
        raise OverflowError(
            f"Uh.. At that point, you're basically rolling a sphere. Even "
            f"earth has less than `{faces:,}` faces. Please bowl with a "
            f"sphere of fewer than 1 million faces..."
        )

    return True


def generate_roll(query: str) -> collections.abc.Generator[int]:
    """
    A helper command to generate a dice roll from a dice string
    representation "2d6"

    :param query: The string representing the dice roll.
    :return: A list of outcomes following from the dice roll. 2d6 will
     return a list with 2 integers, ranging from 1-6.
    :raise ValueError: If the given query does not match the format
     "1d2" where "1" and "2" are numbers; or if "2" is negative.
    :raise OverflowError: If the number of dice or faces
     exceeds 1 000 000.
    """
    dice, faces = _parse_dice_roll(query)  # raises ValueError
    if faces is None:
        # it's a constant, not a dice roll
        yield dice
        return
    negative = dice < 0
    if negative:
        dice = -dice

    _validate_dice_and_faces(dice, faces)  # raises ValueError, OverflowError

    negativity_modifier = -1 if negative else 1
    for _ in range(dice):
        yield negativity_modifier * random.randint(1, faces)

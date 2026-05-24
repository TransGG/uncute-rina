import pytest
from extensions.addons.cogs.funaddons import _simplify_roll_output


@pytest.mark.parametrize("rolls, expected", [
    ([1], "'1'x1"),
    ([1, 1, 1], "'1'x3"),
    ([1, 2, 3], "'1'x1, '2'x1, '3'x1"),
])
def test_valid_cases(
        rolls: list[int], expected: str
) -> None:
    assert _simplify_roll_output(rolls) == "You rolled " + expected

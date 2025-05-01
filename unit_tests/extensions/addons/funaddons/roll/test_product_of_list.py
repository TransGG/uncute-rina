import pytest
from extensions.addons.cogs.funaddons import _product_of_list


@pytest.mark.parametrize("input_list, expected", [
    ([], 1),  # Empty list
    ([5], 5),  # Single element
    ([2, 3, 4], 24),  # Multiple elements
    ([0, 1, 2], 0),  # A '0' element
    ([-3, 2], -6),  # Negative element
    ([12, 2.5], 30),  # Floating point
    ([0.5, 0.5], 0.25),  # Floating point result
    ([-0.5, -0.5], 0.25),  # Double negative floating point
    ([9] * 20, 9**20),  # big number
    ([1] * 100, 1),  # longer list
])
def test_valid_cases(
        input_list: list[int | float], expected: int | float
):
    assert _product_of_list(input_list) == expected

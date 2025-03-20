import pytest

from resources.utils.timeparser import TimeParser, TIMETERMS


# region Correct functionality
def test_parse_simple():
    # Arrange
    terms = [
        (200, "days"),
        (199, "seconds"),
    ]
    expected = [
        (200, "d"),
        (199, "s"),
    ]
    # Act
    output = TimeParser.shrink_time_terms(terms)

    # Assert
    assert output == expected


def test_parse_all():
    # Arrange
    expected_values = []
    terms = []
    for unit in TIMETERMS:
        for term in TIMETERMS[unit]:
            terms.append((1, term))
            expected_values.append((1, unit))

    # Act
    output = TimeParser.shrink_time_terms(terms)

    # Assert
    assert output == expected_values

# endregion Correct functionality


# region Malformed input
def test_exception_invalid_time_term():
    # Arrange
    unknown_term = "NONEXISTENT TIME TERM"
    assert unknown_term not in [val for key in TIMETERMS for val in TIMETERMS[key]]
    terms = [
        (1, unknown_term)
    ]
    # Assert
    with pytest.raises(ValueError):
        TimeParser.shrink_time_terms(terms)

# endregion Malformed input




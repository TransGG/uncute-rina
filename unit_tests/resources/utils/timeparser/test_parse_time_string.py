import pytest

from resources.utils.timeparser import (
    TimeParser,
    MissingQuantityException,
    MissingUnitException,
)


# region Correct functionality
def test_parse_simple():
    # Assign
    parse = TimeParser.parse_time_string("2d")
    expected = [(2, "d")]

    # Assert
    assert expected == parse


def test_parse_longer():
    # Assign
    parse = TimeParser.parse_time_string("2days21hours10minutes4seconds")
    expected = [(2.0, 'days'), (21.0, 'hours'),
                (10.0, 'minutes'), (4.0, 'seconds')]

    # Assert
    assert expected == parse


def test_parse_decimal():
    # Assign
    parse = TimeParser.parse_time_string("4.3days")
    expected = [(4.3, 'days')]

    # Assert
    assert expected == parse


def test_parse_decimals_longer():
    # Assign
    parse = TimeParser.parse_time_string(
        "2.123days"
        "21.53hours"
        "10.3242minutes"
        "4.432seconds"
    )
    expected = [(2.123, 'days'), (21.53, 'hours'),
                (10.3242, 'minutes'), (4.432, 'seconds')]

    # Assert
    assert expected == parse


def test_parse_overflow():
    # this function is not particularly interesting since it should
    #  just split them, but oh well.
    # Assign
    parse = TimeParser.parse_time_string("50days50hours100minutes400seconds")
    expected = [(50.0, 'days'), (50.0, 'hours'),
                (100.0, 'minutes'), (400.0, 'seconds')]

    # Assert
    assert expected == parse

# endregion Correct Functionality


# region Malformed input
def test_parse_missing_quantity():
    with pytest.raises(MissingQuantityException):
        TimeParser.parse_time_string("days")


def test_parse_missing_quantity2():
    with pytest.raises(MissingQuantityException):
        TimeParser.parse_time_string("days30minutes")


def test_parse_missing_unit():
    with pytest.raises(MissingUnitException):
        TimeParser.parse_time_string("20")


def test_parse_missing_unit2():
    with pytest.raises(MissingUnitException):
        TimeParser.parse_time_string("20days30")

# endregion Malformed input

from datetime import datetime, timedelta
from dateutil.tz.tz import tzoffset

from resources.utils.timeparser import TimeParser

# todo: add tests for ValueError and expected crashes


# region Correct functionality
def test_parse_simple():
    # Arrange
    now = datetime.now()

    # Act
    output = TimeParser.parse_date("10d5h3m1s", now)
    expected = now + timedelta(days=10, hours=5, minutes=3, seconds=1)

    # Assert
    assert expected == output


def test_parse_duplicates():
    # Arrange
    now = datetime.now()

    # Act
    output = TimeParser.parse_date("3d4d5d", now)
    expected = now + timedelta(days=12)

    # Assert
    assert expected == output


def test_output_nochange_match():
    # Arrange
    now = datetime.now()

    # Act
    output = TimeParser.parse_date("0d", now)

    # Assert
    assert now == output


def test_timezone():
    # Arrange
    now = datetime.now(tzoffset("-", timedelta(seconds=60 * 60 * 9)))  # UTC+9

    # Act
    output = TimeParser.parse_date("0d", now)

    # Assert
    assert now == output
    assert now.tzinfo == output.tzinfo


# endregion Correct functionality

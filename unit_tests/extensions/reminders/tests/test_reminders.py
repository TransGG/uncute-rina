import pytest

from datetime import datetime, timedelta, timezone
from time import mktime
import asyncio

from unit_tests.object import CustomObject

from extensions.reminders.objects.reminderobject import _parse_reminder_time
from extensions.reminders.exceptions import (
    UnixTimestampInPastException, TimestampParseError, MalformedISODateTimeException
)


# region Helper functions
def _get_current_time_formatted():
    start_time = datetime.now()
    start_time = start_time.replace(tzinfo=None, microsecond=0)  # itx.created_at has no microseconds or timezone
    return start_time


def _get_custom_time1():
    # Set a custom datetime. This is mainly done to make sure the tests for "%I" and "%H" are correctly different.
    # These tests check whether hour = "4" vs "04" makes a difference. If hour >= 10, using datetime wouldn't
    # let these tests show their potential.
    start_time = datetime(year=2025, month=3, day=1, hour=4, minute=1, second=5, microsecond=9265)  # datetime.now()
    start_time = start_time.replace(tzinfo=None, microsecond=0)  # itx.created_at has no microseconds or timezone
    return start_time

# endregion Helper functions


# region Functional mechanics
def test_output_nochange_match():
    # Arrange
    current_time = _get_current_time_formatted()
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, "0d")

    # Act
    reminder_time, now = asyncio.run(func)

    # Assert
    assert current_time == now
    assert current_time == reminder_time

def test_output_timezones_match():
    # Arrange
    current_time = _get_current_time_formatted().astimezone(datetime.now().tzinfo)
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, "0d")

    # Act
    reminder_time, now = asyncio.run(func)
    current_time = current_time.astimezone(timezone.utc)
    reminder_time = reminder_time.astimezone(timezone.utc)

    # Assert
    assert current_time == now
    assert current_time == reminder_time


def test_relative_offset():
    # Arrange
    current_time = _get_current_time_formatted()
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, "500d,1h,1m,1s")

    # Act
    reminder_time, _ = asyncio.run(func)
    expected_time = current_time + timedelta(days=500, hours=1, minutes=1, seconds=1)

    # Assert
    assert expected_time == reminder_time


def test_discord_timestamp():
    # Arrange
    current_time = _get_custom_time1()
    new_time = current_time + timedelta(days=1)
    unix_timestamp = int(new_time.timetuple())
    print(new_time, new_time.tzinfo)
    discord_format = f"<t:{unix_timestamp}:F>"
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, discord_format)

    # Act
    reminder_time, _ = asyncio.run(func)
    expected_time = current_time + timedelta(days=1)

    # Assert
    assert expected_time == reminder_time


def test_iso_date_timeshort_timezone():
    # Arrange
    current_time = _get_custom_time1()
    datetime_string = current_time.strftime('%Y-%m-%dT%I:%M:%S+0100')  # 2025-03-01T4:01:05+0100
    current_time = current_time.replace(tzinfo=None)
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, datetime_string)

    # Act
    reminder_time, _ = asyncio.run(func)

    # Assert
    assert current_time == reminder_time


def test_iso_date_matches_unix_timestamp():
    # Arrange
    date_string1 = "2025-03-01T04:01:05+0900"
    date_string2 = "1740801665"

    itx = CustomObject(created_at=datetime.now())  # not relevant
    func1 = _parse_reminder_time(itx, date_string1)
    func2 = _parse_reminder_time(itx, date_string2)

    # Act
    reminder_time1, _ = asyncio.run(func1)
    reminder_time2, _ = asyncio.run(func2)
    timezone_correction1 = reminder_time1 + timedelta(hours=9)

    # Assert
    assert timezone_correction1 == reminder_time2

def test_iso_date_timelong_timezone():
    # Arrange
    current_time = _get_custom_time1()
    date_string1 = current_time.strftime('%Y-%m-%dT%H:%M:%S+0900')  # 2025-03-01T04:01:05+0100
    date_string2 = current_time.strftime('%Y-%m-%dT%H:%M:%S+1000')  # 2025-03-01T04:01:05+0100

    assert date_string1.endswith("+0900")
    assert date_string2.endswith("+1000")
    assert date_string1 != date_string2

    itx = CustomObject(created_at=current_time)
    func1 = _parse_reminder_time(itx, date_string1)
    func2 = _parse_reminder_time(itx, date_string2)

    # Act
    reminder_time1, _ = asyncio.run(func1)
    reminder_time2, _ = asyncio.run(func2)

    correct_1equality = reminder_time1 + timedelta(hours=1)

    # Assert
    assert reminder_time1 != reminder_time2
    assert correct_1equality == reminder_time2


def test_iso_time_timezone():
    # Arrange
    current_time = _get_custom_time1().astimezone(datetime.now().tzinfo)  # to get %z working
    datetime_string = current_time.strftime('%H:%M:%S%z')  # 04:01:05+0100
    current_time = current_time.replace(tzinfo=None)
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, datetime_string)

    # Act
    reminder_time, _ = asyncio.run(func)

    # Assert
    # same as test_..._timeshort(), but using %H instead of %I. This means the time will be padded to 2 characters.
    assert current_time == reminder_time

# endregion Functional mechanics


# region Exception testing

def test_exception_american_format_ymd():
    # Arrange
    current_time = _get_current_time_formatted()
    datetime_string = current_time.strftime('2025/03/03 10:32:33PM')  # eg. 2025
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, datetime_string)

    # Assert
    with pytest.raises(MalformedISODateTimeException):
        reminder_time, _ = asyncio.run(func)


def test_exception_american_format_dmy():
    # Arrange
    current_time = _get_current_time_formatted()
    datetime_string = current_time.strftime('03/03/2025 10:32:33PM')  # eg. 2025
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, datetime_string)

    # Assert
    with pytest.raises(MalformedISODateTimeException):
        reminder_time, _ = asyncio.run(func)


def test_exception_american_format_with_t_ymd():
    # Arrange
    current_time = _get_current_time_formatted()
    datetime_string = current_time.strftime('2025/03/03T10:32:33PM')  # eg. 2025
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, datetime_string)

    # Assert
    with pytest.raises(MalformedISODateTimeException):
        reminder_time, _ = asyncio.run(func)


def test_exception_american_format_with_t_dmy():
    # Arrange
    current_time = _get_current_time_formatted()
    datetime_string = current_time.strftime('03/03/2025T10:32:33PM')  # eg. 2025
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, datetime_string)

    # Assert
    with pytest.raises(MalformedISODateTimeException):
        reminder_time, _ = asyncio.run(func)


def test_malformed_year():
    # Arrange
    current_time = _get_current_time_formatted()
    datetime_string = current_time.strftime('%Y')  # eg. 2025
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, datetime_string)

    # Assert
    with pytest.raises(TimestampParseError):
        reminder_time, _ = asyncio.run(func)


def test_malformed_year_month():
    # Arrange
    current_time = _get_current_time_formatted()
    datetime_string = current_time.strftime('%Y-%M')  # eg. 2025
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, datetime_string)

    # Assert
    with pytest.raises(TimestampParseError):
        reminder_time, _ = asyncio.run(func)


def test_exception_iso_date_timeshort():  # no timezone
    # Arrange
    current_time = _get_custom_time1()
    datetime_string = current_time.strftime('%Y-%m-%dT%I:%M')  # 2025-03-01T4:01:05
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, datetime_string)

    # Assert
    with pytest.raises(TimestampParseError):
        # It should follow the path of YYYY-MM-DD T HH:MM or HH:MM:SS, requiring a timezone +0000.
        # The timezone isn't provided by the strftime, and as such the code should run into an exception.
        # This exception must be handled by the command in the Cog instead.
        reminder_time, _ = asyncio.run(func)


def test_exception_iso_date_timelong():  # no timezone
    # Arrange
    current_time = _get_custom_time1()
    datetime_string = current_time.strftime('%Y-%m-%dT%H:%M')  # 2025-03-01T4:01:05
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, datetime_string)

    # Assert
    with pytest.raises(TimestampParseError):
        # same as test_..._timeshort(), but using %H instead of %I. This means the time will be padded to 2 characters.
        reminder_time, _ = asyncio.run(func)


def test_exception_iso_date():
    # Arrange
    current_time = _get_current_time_formatted()
    datetime_string = current_time.strftime('%Y-%m-%d')  # eg. 2025-03-17
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, datetime_string)

    # Assert
    with pytest.raises(AttributeError):
        # It should follow the path of YYYY-MM-DD, asking for a time of day when you want to be reminded.
        # This would be directly handled using itx.response, which the test doesn't provide, resulting in
        # an Attribute error.
        reminder_time, _ = asyncio.run(func)


def test_exception_12_hour_clock():
    # Arrange
    current_time = _get_current_time_formatted()
    datetime_string = current_time.strftime('2025-03-17T10:32:33PM')
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, datetime_string)

    # Assert
    with pytest.raises(TimestampParseError):
        reminder_time, _ = asyncio.run(func)


def test_exception_12_hour_clock_timezone():
    # Arrange
    current_time = _get_current_time_formatted().astimezone(datetime.now().tzinfo)
    datetime_string = current_time.strftime('2025-03-17T10:32:33PM+0100')
    current_time.replace(tzinfo=None)
    itx = CustomObject(created_at=current_time)
    func = _parse_reminder_time(itx, datetime_string)

    # Assert
    with pytest.raises(TimestampParseError):
        reminder_time, _ = asyncio.run(func)

# endregion Exception testing

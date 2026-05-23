from datetime import datetime


class MalformedISODateTimeException(Exception):
    def __init__(self, ex: Exception) -> None:
        self.inner_exception = ex


class TimestampParseException(Exception):
    def __init__(self, inner_exception: Exception) -> None:
        self.inner_exception = inner_exception


class UnixTimestampInPastException(Exception):
    def __init__(self, distance: datetime, creation_time: datetime) -> None:
        self.distance = distance
        self.creation_time = creation_time


class ReminderTimeSelectionMenuTimeOut(Exception):
    def __init__(self) -> None:
        pass

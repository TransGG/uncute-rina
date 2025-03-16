from datetime import datetime


class MalformedISODateTimeException(Exception):
    def __init__(self, ex: Exception):
        self.inner_exception = ex


class TimestampParseError(Exception):
    def __init__(self, inner_exception):
        self.inner_exception = inner_exception


class UnixTimestampInPastException(Exception):
    def __init__(self, unix_timestamp_string: str, creation_time: datetime):
        self.unix_timestamp_string = unix_timestamp_string
        self.creation_time = creation_time

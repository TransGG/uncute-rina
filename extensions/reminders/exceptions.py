from datetime import datetime


class MalformedISODateTimeException(Exception):
    def __init__(self, ex: Exception):
        self.inner_exception = ex


class TimestampParseException(Exception):
    def __init__(self, inner_exception):
        self.inner_exception = inner_exception


class UnixTimestampInPastException(Exception):
    def __init__(self, distance: datetime, creation_time: datetime):
        self.distance = distance
        self.creation_time = creation_time

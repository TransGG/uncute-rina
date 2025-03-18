import enum


class TimestampFormats(enum.Enum):
    DateTimeToSeconds = 0  # YYYY-MM-DDtHH:MM:SS
    DateTimeToMinutes = 1  # YYYY-MM-DDtHH:MM
    DateNoTime = 2  # YYYY-MM-DD

from typing import TypedDict, Required


# noinspection SpellCheckingInspection
class ReminderDict(TypedDict):
    creationtime: int
    remindertime: int
    reminder: str


class DatabaseData(TypedDict, total=False):
    userID: Required[int]
    reminders: list[ReminderDict]

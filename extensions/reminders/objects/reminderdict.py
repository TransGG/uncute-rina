from typing import TypedDict


# noinspection SpellCheckingInspection
class ReminderDict(TypedDict):
    creationtime: int
    remindertime: int
    reminder: str


class DatabaseData(TypedDict):
    userID: int
    reminders: list[ReminderDict]

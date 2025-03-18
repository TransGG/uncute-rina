from typing import TypedDict


# noinspection SpellCheckingInspection
class ReminderDict(TypedDict):
    creationtime: int
    remindertime: int
    reminder: str

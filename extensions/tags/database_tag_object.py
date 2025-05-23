from typing import TypedDict


class DatabaseTagObject(TypedDict):
    title: str
    description: str
    color: tuple[int, int, int]
    report_to_staff: bool

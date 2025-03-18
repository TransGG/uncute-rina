from typing import TypedDict


class VcLogGraphData(TypedDict):
    User: list[str]
    Start: list[float]
    Finish: list[float]
    
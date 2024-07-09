from typing import TypedDict

class HelpPage(TypedDict):
    title: str
    description: str
    fields: list[tuple[str,str]]

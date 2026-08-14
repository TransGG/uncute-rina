from typing import TypedDict


class CustomDictionaryEntry(TypedDict):
    term: str
    definition: str
    synonyms: list[str]

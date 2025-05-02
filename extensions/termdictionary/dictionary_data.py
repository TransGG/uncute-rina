from typing import TypedDict


class DictionaryData(TypedDict):
    term: str
    definition: str
    synonyms: list[str]

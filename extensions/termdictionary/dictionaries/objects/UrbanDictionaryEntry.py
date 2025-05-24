from typing import TypedDict


class UrbanDictionaryEntry(TypedDict):
    definition: str
    permalink: str
    thumbs_up: int
    author: str
    word: str
    defid: int
    current_vote: str
    written_on: str  # ISO YYYY-mm-dd T HH:MM:SS.fff Z
    example: str
    thumbs_down: int

from typing import TypedDict, Required, Any


class PronousPageLocaleEntry(TypedDict, total=False):
    # Mostly same as PronounsPageEntry. Only missing `versions`
    id: str
    term: Required[str]
    original: str
    definition: Required[str]
    locale: str  # everything except 'en' (English)
    approved: int
    base_id: Any
    author_id: str
    deleted: int
    flags: str
    category: str
    images: str
    key: str
    author: str


class PronounsPageEntry(TypedDict, total=False):
    id: str
    term: Required[str]
    original: str
    definition: Required[str]
    locale: str  # by default just 'en' (English) I think
    approved: int
    base_id: Any  # no clue what this is supposed to be
    author_id: str
    deleted: int
    flags: str  # "[]"
    category: str
    images: str
    key: str
    author: str
    versions: list[PronousPageLocaleEntry]

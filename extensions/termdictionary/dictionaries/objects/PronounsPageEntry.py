from typing import TypedDict, Required, Any


class PronousPageLocaleEntry(TypedDict, total=False):
    # Mostly same as PronounsPageEntry. Only missing `versions`
    id: str  # 26-char alphanumeric string
    locale: str  # everything except the PronounsPageEntry[locale] (e.g. "en")
    approved: bool  # integer technically
    deleted: bool  # integer technically
    term: Required[str]
    original: str
    definition: Required[str]
    base_id: str | None  # can be null?
    author_id: str
    flags: str
    category: str
    images: str
    key: str
    author: str


class PronounsPageEntry(TypedDict, total=False):
    # https://docs.api.pronouns.page/operation/operation-get-terms-search-parameter
    id: str  # 26-char alphanumeric string
    locale: str  # by default just 'en' (English) I think
    approved: bool  # integer technically
    deleted: bool  # integer technically
    term: Required[str]
    original: str
    definition: Required[str]
    base_id: str | None  # 26-char alphanumeric string (but also null?)
    author_id: str  # 26-char alphanumeric string
    flags: str  # "[]" ... Api docs say it's supposed to be an Array[String]
    category: str
    images: str  # comma-separated list of image IDs
    key: str  # "key for the term version, often derived from the publication date and term"
    author: str  # name
    versions: list[PronousPageLocaleEntry]

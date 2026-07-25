__all__ = [
    "CustomDictionaryEntry",
    "DetailedTermPage",
    "DictionaryApiEntry",
    "PronounsPageEntry",
    "UrbanDictionaryEntry",
    "get_term_lines",
    "term_page_to_embed",
]

from .CustomDictionaryEntry import CustomDictionaryEntry
from .DictionaryApiEntry import (
    DetailedTermPage,
    DictionaryApiEntry,
    get_term_lines,
    term_page_to_embed,
)
from .PronounsPageEntry import PronounsPageEntry
from .UrbanDictionaryEntry import UrbanDictionaryEntry

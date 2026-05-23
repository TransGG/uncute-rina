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
from .PronounsPageEntry import PronounsPageEntry
from .DictionaryApiEntry import (
    DictionaryApiEntry,
    DetailedTermPage,
    term_page_to_embed,
    get_term_lines,
)
from .UrbanDictionaryEntry import UrbanDictionaryEntry

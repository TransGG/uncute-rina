__all__ = [
    "CustomDictionaryEntry",
    "DetailedTermPage",
    "DictionaryApiEntry",
    "PronounsPageEntry",
    "UrbanDictionaryEntry",
    "get_term_lines",
    "term_page_to_embed",
]

from .custom_dictionary_entry import CustomDictionaryEntry
from .dictionary_api_entry import (
    DetailedTermPage,
    DictionaryApiEntry,
    get_term_lines,
    term_page_to_embed,
)
from .pronouns_page_entry import PronounsPageEntry
from .urban_dictionary_entry import UrbanDictionaryEntry

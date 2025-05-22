import typing

import discord


class MeaningDefinitions(typing.TypedDict):
    definition: str
    synonyms: list[str]
    antonyms: list[str]


class EntryMeanings(typing.TypedDict):
    partOfSpeech: str  # think 'Noun', 'Verb', 'Interjection'
    definitions: list[MeaningDefinitions]
    synonyms: list[str]
    antonyms: list[str]


class DictionaryApiEntry(typing.TypedDict):
    word: str
    meanings: list[EntryMeanings]  # each EntryMeanings.partOfSpeech is unique
    sourceUrls: list[str]


DetailedTermPage = tuple[str, dict[str, list[str]]]


def term_page_to_embed(page: DetailedTermPage) -> discord.Embed:
    """
    Convert and format a term page into a Discord embed.

    Each section's values are prefixed with line IDs and displayed in
    a field. If a section exceeds character limits, it is truncated.

    :param page: The page to format.
    :return: The formatted embed matching the given term page.
    """
    word, sections = page
    embed = discord.Embed(title=f"__{word.capitalize()}__",
                          color=8481900)

    line_id = 0
    for section_name, section_values in sections.items():
        section_text = ""
        for value in section_values:
            section_text += f"{line_id}-{value}\n"
            line_id += 1
        if len(section_text) > 995:
            # limit to 1024 chars in Value field
            section_text = section_text[:995] + "... (shortened due to size)"

        embed.add_field(name=section_name,
                        value=section_text or "null",
                        # ^ prevent possible crash from empty field.
                        #  idk if this actually happens, but still.
                        inline=False)

    return embed


def get_term_lines(page: DetailedTermPage) -> list[tuple[str, str]]:
    """
    Get a list of lines from a term page.

    :param page: The page to get lines for.
    :return: A list of tuples of the section a line came from, and the
     line itself.
    """
    word, sections = page
    lines: list[tuple[str, str]] = []
    for section_name, section_values in sections.items():
        for value in section_values:
            lines.append((
                section_name,
                f"{len(lines)}-{value}"
            ))
    return lines

from typing import TypeVar


del_separators_table = str.maketrans({" ": "", "-": "", "_": ""})


StringOrStrings = TypeVar("StringOrStrings", str, list[str])


def simplify(query: StringOrStrings) -> StringOrStrings:
    if isinstance(query, str):
        return query.lower().translate(del_separators_table)
    if isinstance(query, list):
        return [text.lower().translate(del_separators_table)
                for text in query]

    raise NotImplementedError("...")

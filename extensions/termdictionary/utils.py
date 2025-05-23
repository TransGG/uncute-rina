from typing import TypeVar


del_separators_table = str.maketrans({" ": "", "-": "", "_": ""})


StringOrStrings = TypeVar("StringOrStrings", str, list[str])


def simplify(query: StringOrStrings) -> StringOrStrings:
    if type(query) is str:
        return query.lower().translate(del_separators_table)
    if type(query) is list:
        return [text.lower().translate(del_separators_table)
                for text in query]
    raise NotImplementedError()

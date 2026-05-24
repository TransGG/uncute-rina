from typing import TypedDict


# this format is necessary to keep the spaces in "Open Exchange Rates" etc.
# I could rename the key to use snake_case, but oh well.
ApiTokenDict = TypedDict(
    'ApiTokenDict',
    {
        'MongoDB': str,
        'Open Exchange Rates': str,
        'Wolfram Alpha': str,
        'Equaldex': str
    }
)

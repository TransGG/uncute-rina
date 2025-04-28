from typing import TypedDict, Required, NotRequired


class EmojiStatsData(TypedDict, total=False):
    id: Required[str]  # unique
    name: Required[str]
    messageUsedCount: NotRequired[int]
    lastUsed: Required[int]
    animated: Required[bool]
    reactionUsedCount: NotRequired[int]

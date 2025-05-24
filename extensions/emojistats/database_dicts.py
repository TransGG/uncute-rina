from typing import TypedDict, Required, NotRequired


class EmojiStatsData(TypedDict, total=False):
    id: Required[str]  # emoji.id (unique)
    name: Required[str]  # emoji.name
    messageUsedCount: NotRequired[int]
    # ^ how often messages have contained this emoji
    lastUsed: Required[int]
    # ^ unix timestamp of when this emoji was last used
    animated: Required[bool]  # emoji.animated
    reactionUsedCount: NotRequired[int]
    # ^ how often messages have been replied to with this emoji

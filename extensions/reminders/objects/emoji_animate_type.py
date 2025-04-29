from enum import Enum


class EmojiAnimateType(Enum):
    """
    A representation for the animation type of an emoji. Used for `get_unused_emojis`.
    """
    static = 1
    animated = 2
    both = 3

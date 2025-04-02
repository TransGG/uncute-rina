from typing import TypedDict, Literal


class EnabledModules(TypedDict, total=False):
    starboard: bool
    headpat_reactions: bool
    poll_reactions: bool
    compliments: bool
    custom_vcs: bool
    vc_tables: bool
    qotw: bool
    dev_requests: bool
    bump_reminder: bool
    selfies_channel_deletion: bool
    tags: bool
    custom_dictionary: bool
    watchlist: bool


class ModuleKeys:
    """
    A class to allow enum-like conversion from class attribute to string. This can be used in
    :py:func:`~resources.customs.bot.Bot.is_module_enabled` by simply referencing this class' attribute
    rather than using magic strings.
    """
    starboard: Literal["starboard"] = "starboard"
    headpat_reactions: Literal["headpat_reactions"] = "headpat_reactions"
    poll_reactions: Literal["poll_reactions"] = "poll_reactions"
    compliments: Literal["compliments"] = "compliments"
    custom_vcs: Literal["custom_vcs"] = "custom_vcs"
    vc_tables: Literal["vc_tables"] = "vc_tables"
    qotw: Literal["qotw"] = "qotw"
    dev_requests: Literal["dev_requests"] = "dev_requests"
    bump_reminder: Literal["bump_reminder"] = "bump_reminder"
    selfies_channel_deletion: Literal["selfies_channel_deletion"] = "selfies_channel_deletion"
    tags: Literal["tags"] = "tags"
    custom_dictionary: Literal["custom_dictionary"] = "custom_dictionary"
    watchlist: Literal["watchlist"] = "watchlist"

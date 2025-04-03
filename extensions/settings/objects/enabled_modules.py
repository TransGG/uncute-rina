from typing import TypedDict


class EnabledModules(TypedDict, total=False):
    starboard: bool
    headpat_reactions: bool
    awawawa_reactions: bool
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
    starboard = "starboard"
    headpat_reactions = "headpat_reactions"
    awawawa_reactions = "awawawa_reactions"
    poll_reactions = "poll_reactions"
    compliments = "compliments"
    custom_vcs = "custom_vcs"
    vc_tables = "vc_tables"
    qotw = "qotw"
    dev_requests = "dev_requests"
    bump_reminder = "bump_reminder"
    selfies_channel_deletion = "selfies_channel_deletion"
    tags = "tags"
    custom_dictionary = "custom_dictionary"
    watchlist = "watchlist"

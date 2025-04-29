from typing import TypedDict

from .attribute_keys import AttributeKeys


class EnabledModules(TypedDict, total=False):
    """
    A dictionary of all toggleable bot modules.

    This is stored in the database and the client.
    """
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
    aegis_ping_reactions: bool
    ban_appeal_reactions: bool
    vc_log_reader: bool
    remove_role_command: bool
    report_tags_to_staff: bool
    polls_only_channel: bool
    change_channel: bool


class ModuleKeys:
    """
    A class to allow enum-like conversion from class attribute to
     string. This can be used in
     :py:func:`~resources.customs.bot.Bot.is_module_enabled` by simply
     referencing this class' attribute rather than using magic strings.
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
    aegis_ping_reactions = "aegis_ping_reactions"
    ban_appeal_reactions = "ban_appeal_reactions"
    vc_log_reader = "vc_log_reader"
    remove_role_command = "remove_role_command"
    report_tags_to_staff = "report_tags_to_staff"
    polls_only_channel = "polls_only_channel"
    change_channel = "change_channel"


module_required_attributes = {
    # todo: finish.
    ModuleKeys.starboard: (
        AttributeKeys.starboard_channel,
        AttributeKeys.starboard_upvote_emoji,
        AttributeKeys.starboard_blacklisted_channels,
        AttributeKeys.starboard_minimum_upvote_count,
        AttributeKeys.starboard_minimum_vote_count_for_downvote_delete,
    ),

    ModuleKeys.report_tags_to_staff: (
        AttributeKeys.staff_reports_channel,
    ),

    ModuleKeys.custom_vcs: (
        AttributeKeys.custom_vc_blacklisted_channels,
        AttributeKeys.custom_vc_blacklist_prefix,
        AttributeKeys.custom_vc_category,
        AttributeKeys.custom_vc_create_channel,
        AttributeKeys.vctable_prefix,
    ),

    ModuleKeys.polls_only_channel: (
        AttributeKeys.polls_only_channel,
        AttributeKeys.polls_channel_reaction_role,
    ),

    ModuleKeys.change_channel: (),
}

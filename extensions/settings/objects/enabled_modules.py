import dataclasses

from .attribute_keys import AttributeKeys


@dataclasses.dataclass
class EnabledModules:
    """
    A class of all toggleable bot modules.

    This is stored in the database and the client.
    """
    starboard: bool = False
    headpat_reactions: bool = False
    awawawa_reactions: bool = False
    poll_reactions: bool = False
    compliments: bool = False
    custom_vcs: bool = False
    vc_tables: bool = False
    qotw: bool = False
    dev_requests: bool = False
    bump_reminder: bool = False
    selfies_channel_deletion: bool = False
    tags: bool = False
    custom_dictionary: bool = False
    watchlist: bool = False
    aegis_ping_reactions: bool = False
    ban_appeal_reactions: bool = False
    vc_log_reader: bool = False
    remove_role_command: bool = False
    report_tags_to_staff: bool = False
    polls_only_channel: bool = False
    change_channel: bool = False
    anonymous_report_reactions: bool = False


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
    anonymous_report_reactions = "anonymous_report_reactions"


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

    ModuleKeys.vc_tables: (
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

    ModuleKeys.anonymous_report_reactions: (
        AttributeKeys.anonymous_reports_webhook_id,
    ),

    ModuleKeys.vc_log_reader: (
        AttributeKeys.voice_channel_activity_logs_channel,
    ),

    ModuleKeys.watchlist: (
        AttributeKeys.watchlist_channel,
        AttributeKeys.watchlist_reaction_role,
        # AttributeKeys.staff_reports_channel,
        AttributeKeys.staff_logs_category,
        AttributeKeys.badeline_bot,
    ),

    ModuleKeys.poll_reactions: (
        AttributeKeys.log_channel,
        AttributeKeys.poll_reaction_blacklisted_channels,
    ),

    ModuleKeys.custom_dictionary: (
        AttributeKeys.log_channel,
    ),

    ModuleKeys.selfies_channel_deletion: (
        AttributeKeys.log_channel,
        AttributeKeys.selfies_channel,
    ),
}

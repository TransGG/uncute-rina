from typing import Literal


class AttributeKeys:
    """
    A class to allow enum-like conversion from class attribute to string. This can be used in
    :py:func:`~resources.customs.bot.Bot.get_guild_attribute` by simply referencing this class' attribute
    rather than using magic strings.
    """
    parent_server: Literal["parent_server"] = "parent_server"
    child_servers: Literal["child_servers"] = "child_servers"

    admin_roles: Literal["admin_roles"] = "admin_roles"
    staff_roles: Literal["staff_roles"] = "staff_roles"

    qotw_suggestions_channel: Literal["qotw_suggestions_channel"] = "qotw_suggestions_channel"
    developer_request_channel: Literal["developer_request_channel"] = "developer_request_channel"
    watchlist_channel: Literal["watchlist_channel"] = "watchlist_channel"
    staff_reports_channel: Literal["staff_reports_channel"] = "staff_reports_channel"
    ticket_create_channel: Literal["ticket_create_channel"] = "ticket_create_channel"
    staff_logs_category: Literal["staff_logs_category"] = "staff_logs_category"
    badeline_bot: Literal["badeline_bot"] = "badeline_bot"
    ban_appeal_reaction_role: Literal["ban_appeal_reaction_role"] = "ban_appeal_reaction_role"
    watchlist_reaction_role: Literal["watchlist_reaction_role"] = "watchlist_reaction_role"
    developer_request_reaction_role: Literal["developer_request_reaction_role"] = "developer_request_reaction_role"
    aegis_ping_role: Literal["aegis_ping_role"] = "aegis_ping_role"

    ban_appeal_webhook: Literal["ban_appeal_webhook"] = "ban_appeal_webhook"
    vctable_prefix: Literal["vctable_prefix"] = "vctable_prefix"

    custom_vc_create_channel: Literal["custom_vc_create_channel"] = "custom_vc_create_channel"
    log_channel: Literal["log_channel"] = "log_channel"
    custom_vc_category: Literal["custom_vc_category"] = "custom_vc_category"
    starboard_channel: Literal["starboard_channel"] = "starboard_channel"
    starboard_minimum_upvote_count: Literal["starboard_minimum_upvote_count"] = "starboard_minimum_upvote_count"
    bump_reminder_channel: Literal["bump_reminder_channel"] = "bump_reminder_channel"
    bump_reminder_role: Literal["bump_reminder_role"] = "bump_reminder_role"

    poll_reaction_blacklisted_channels: Literal["poll_reaction_blacklisted_channels"] = \
        "poll_reaction_blacklisted_channels"
    bump_reminder_bot: Literal["bump_reminder_bot"] = "bump_reminder_bot"

    starboard_blacklisted_channels: Literal["starboard_blacklisted_channels"] = "starboard_blacklisted_channels"
    starboard_upvote_emoji: Literal["starboard_upvote_emoji"] = "starboard_upvote_emoji"
    starboard_minimum_vote_count_for_downvote_delete: Literal["starboard_minimum_vote_count_for_downvote_delete"] = \
        "starboard_minimum_vote_count_for_downvote_delete"
    voice_channel_logs_channel: Literal["voice_channel_logs_channel"] = "voice_channel_logs_channel"

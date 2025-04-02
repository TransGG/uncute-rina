class AttributeKeys:
    """
    A class to allow enum-like conversion from class attribute to string. This can be used in
    :py:func:`~resources.customs.bot.Bot.get_guild_attribute` by simply referencing this class' attribute
    rather than using magic strings.
    """
    parent_server = "parent_server"
    child_servers = "child_servers"

    admin_roles = "admin_roles"
    staff_roles = "staff_roles"

    log_channel = "log_channel"
    qotw_suggestions_channel = "qotw_suggestions_channel"
    developer_request_channel = "developer_request_channel"
    developer_request_reaction_role = "developer_request_reaction_role"
    watchlist_channel = "watchlist_channel"
    watchlist_reaction_role = "watchlist_reaction_role"
    staff_reports_channel = "staff_reports_channel"
    ticket_create_channel = "ticket_create_channel"
    staff_logs_category = "staff_logs_category"
    badeline_bot = "badeline_bot"
    ban_appeal_webhook = "ban_appeal_webhook"

    ban_appeal_reaction_role = "ban_appeal_reaction_role"
    aegis_ping_role = "aegis_ping_role"

    vctable_prefix = "vctable_prefix"
    custom_vc_create_channel = "custom_vc_create_channel"
    custom_vc_category = "custom_vc_category"
    starboard_channel = "starboard_channel"
    starboard_upvote_emoji = "starboard_upvote_emoji"
    starboard_blacklisted_channels = "starboard_blacklisted_channels"
    starboard_minimum_upvote_count = "starboard_minimum_upvote_count"

    starboard_minimum_vote_count_for_downvote_delete = "starboard_minimum_vote_count_for_downvote_delete"
    bump_reminder_channel = "bump_reminder_channel"

    bump_reminder_role = "bump_reminder_role"
    bump_reminder_bot = "bump_reminder_bot"
    poll_reaction_blacklisted_channels = "poll_reaction_blacklisted_channels"
    voice_channel_activity_logs_channel = "voice_channel_activity_logs_channel"

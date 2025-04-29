from typing import TypedDict

import discord


class ServerAttributes(TypedDict):
    """A dictionary containing all customizable guild attributes.

    This is stored in the client.
    """
    # When adding a new key to this class, make sure to add the same
    #  key to the ServerAttributes class.
    # If you're giving it a new type, make sure it gets parsed in
    #  ServerSettings.get_attributes().
    parent_server: discord.Guild | None

    admin_roles: list[discord.Role]
    staff_roles: list[discord.Role]

    log_channel: discord.abc.Messageable | None

    qotw_suggestions_channel: discord.abc.Messageable | None
    developer_request_channel: discord.TextChannel | None
    # ^ needs to be able to have threads
    developer_request_reaction_role: discord.Role | None

    watchlist_channel: discord.TextChannel | None
    # ^ needs to be able to have threads
    watchlist_reaction_role: discord.Role | None
    staff_reports_channel: discord.abc.Messageable | None
    ticket_create_channel: discord.abc.Messageable | None
    staff_logs_category: discord.CategoryChannel | None
    badeline_bot: discord.User | None

    # Webhooks require async fetching, so instead I opted for storing
    #  only their ID, so they can be compared with Message.webhook_id.
    anonymous_reports_webhook_id: int | None  # Webhook
    ban_appeal_webhook_id: int | None  # Webhook
    ban_appeal_reaction_role: discord.Role | None
    aegis_ping_role: discord.Role | None

    vctable_prefix: str | None
    custom_vc_blacklist_prefix: str | None
    custom_vc_blacklisted_channels: list[discord.VoiceChannel]
    custom_vc_create_channel: discord.VoiceChannel | None
    custom_vc_category: discord.CategoryChannel | None

    starboard_channel: discord.abc.Messageable | None
    starboard_upvote_emoji: discord.Emoji | None
    starboard_blacklisted_channels: list[discord.abc.Messageable]
    starboard_minimum_upvote_count: int | None
    starboard_minimum_vote_count_for_downvote_delete: int | None

    bump_reminder_channel: discord.abc.Messageable | None
    bump_reminder_role: discord.Role | None
    bump_reminder_bot: discord.User | None

    poll_reaction_blacklisted_channels: list[discord.abc.Messageable]

    selfies_channel: discord.abc.Messageable | None

    voice_channel_activity_logs_channel: discord.abc.Messageable | None

    headpat_emoji: discord.Emoji | None
    awawawa_emoji: discord.Emoji | None

    polls_only_channel: discord.TextChannel | None
    # ^ needs to be able to have threads
    polls_channel_reaction_role: discord.Role | None

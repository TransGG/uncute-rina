from typing import TypedDict

import discord


class ServerAttributes(TypedDict):
    # When adding a new key to this class, make sure to add the same key to the ServerAttributes class
    # If you're giving it a new type, make sure it gets parsed in ServerSettings.get_attributes()
    parent_server: discord.Guild | None
    child_servers: list[discord.Guild]

    admin_roles: list[discord.Role]
    staff_roles: list[discord.Role]

    qotw_suggestions_channel: discord.abc.Messageable | None
    developer_request_channel: discord.TextChannel | None  # needs to be able to have threads
    watchlist_channel: discord.TextChannel | None  # needs to be able to have threads
    staff_reports_channel: discord.abc.Messageable | None
    ticket_create_channel: discord.abc.Messageable | None
    staff_logs_category: discord.CategoryChannel | None
    badeline_bot: discord.User | None
    ban_appeal_reaction_role: discord.Role | None
    watchlist_reaction_role: discord.Role | None
    developer_request_reaction_role: discord.Role | None
    aegis_ping_role: discord.Role | None

    ban_appeal_webhook: discord.User | None

    vctable_prefix: str | None
    custom_vc_create_channel: discord.VoiceChannel | None
    custom_vc_category: discord.CategoryChannel | None

    log_channel: discord.abc.Messageable | None
    starboard_channel: discord.abc.Messageable | None
    starboard_minimum_upvote_count: int | None
    bump_reminder_channel: discord.abc.Messageable | None
    bump_reminder_role: discord.Role | None
    poll_reaction_blacklisted_channels: list[discord.abc.Messageable]
    bump_reminder_bot: discord.User | None
    starboard_blacklisted_channels: list[discord.abc.Messageable]
    starboard_upvote_emoji: discord.Emoji | None
    starboard_minimum_vote_count_for_downvote_delete: int | None
    voice_channel_logs_channel: discord.abc.Messageable | None

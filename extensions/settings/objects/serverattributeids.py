from typing import TypedDict


GuildId = int
UserId = int
RoleId = int
EmojiId = int
TextChannelId = int
VoiceChannelId = int
CategoryChannelId = int
MessageableChannelId = int


class ServerAttributeIds(TypedDict):
    server: GuildId
    parent_server: GuildId | None
    child_servers: list[GuildId] | None
    #
    qotw_suggestions_channel: MessageableChannelId | None
    developer_request_channel: MessageableChannelId | None
    watchlist_channel: MessageableChannelId | None
    staff_reports_channel: MessageableChannelId | None
    ticket_create_channel: MessageableChannelId | None
    staff_logs_category: CategoryChannelId | None
    badeline_bot: UserId | None
    ban_appeal_reaction_role: RoleId | None
    watchlist_reaction_role: RoleId | None
    developer_request_reaction_role: RoleId | None
    aegis_ping_role: RoleId | None
    #
    staff_roles: list[RoleId]
    admin_roles: list[RoleId]
    owner_roles: list[RoleId]
    #
    ban_appeal_webhook: int | None
    vctable_prefix: str | None
    #
    custom_vc_create_channel: VoiceChannelId | None
    log_channel: MessageableChannelId | None
    custom_vc_category: CategoryChannelId | None
    starboard_channel: MessageableChannelId | None  # todo: confirm that changing from TextChannelId didn't break
    starboard_minimum_upvote_count: int | None
    bump_reminder_channel: MessageableChannelId | None
    bump_reminder_role: RoleId | None
    # todo: confirm that changing from list[int] to list[MessageableChannelId] didn't break anything
    poll_reaction_blacklisted_channels: list[MessageableChannelId]
    bump_reminder_bot: UserId | None
    # todo: confirm that changing from list[int] to list[MessageableChannelId] didn't break anything
    starboard_blacklisted_channels: list[MessageableChannelId]
    starboard_upvote_emoji: EmojiId | None
    starboard_minimum_vote_count_for_downvote_delete: int | None
    voice_channel_logs_channel: MessageableChannelId | None


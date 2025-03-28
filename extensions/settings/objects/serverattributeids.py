from typing import TypedDict


GuildId = int
UserId = int
RoleId = int
EmojiId = int
TextChannelId = int
VoiceChannelId = int
CategoryChannelId = int
MessageableChannelId = int


class ServerAttributeIds(TypedDict, total=False):
    parent_server: GuildId
    child_servers: list[GuildId]
    #
    qotw_suggestions_channel: MessageableChannelId
    developer_request_channel: MessageableChannelId
    watchlist_channel: MessageableChannelId
    staff_reports_channel: MessageableChannelId
    ticket_create_channel: MessageableChannelId
    staff_logs_category: CategoryChannelId
    badeline_bot: UserId
    ban_appeal_reaction_role: RoleId
    watchlist_reaction_role: RoleId
    developer_request_reaction_role: RoleId
    aegis_ping_role: RoleId
    #
    staff_roles: list[RoleId]
    admin_roles: list[RoleId]
    owner_roles: list[RoleId]
    #
    ban_appeal_webhook: int
    vctable_prefix: str
    #
    custom_vc_create_channel: VoiceChannelId
    log_channel: MessageableChannelId
    custom_vc_category: CategoryChannelId
    starboard_channel: MessageableChannelId  # todo: confirm that changing from TextChannelId didn't break
    starboard_minimum_upvote_count: int
    bump_reminder_channel: MessageableChannelId
    bump_reminder_role: RoleId
    # todo: confirm that changing from list[int] to list[MessageableChannelId] didn't break anything
    poll_reaction_blacklisted_channels: list[MessageableChannelId]
    bump_reminder_bot: UserId
    # todo: confirm that changing from list[int] to list[MessageableChannelId] didn't break anything
    starboard_blacklisted_channels: list[MessageableChannelId]
    starboard_upvote_emoji: EmojiId
    starboard_minimum_vote_count_for_downvote_delete: int
    voice_channel_logs_channel: MessageableChannelId


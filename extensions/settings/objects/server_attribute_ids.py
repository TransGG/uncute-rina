from typing import TypedDict


GuildId = int
UserId = int
WebhookId = int
RoleId = int
EmojiId = int
TextChannelId = int
VoiceChannelId = int
CategoryChannelId = int
MessageableChannelId = int


class ServerAttributeIds(TypedDict, total=False):
    """A dictionary of all customizable attribute ids for a guild.

    This is stored in the database.
    """
    # When adding a new key to this class, make sure to add the same key
    #  to the ServerAttributes class

    parent_server: GuildId

    admin_roles: list[RoleId]
    staff_roles: list[RoleId]

    log_channel: MessageableChannelId

    qotw_suggestions_channel: MessageableChannelId
    developer_request_channel: TextChannelId
    developer_request_reaction_role: RoleId

    watchlist_channel: TextChannelId
    watchlist_reaction_role: RoleId
    staff_reports_channel: MessageableChannelId
    ticket_create_channel: MessageableChannelId
    staff_logs_category: CategoryChannelId
    badeline_bot: UserId

    anonymous_reports_webhook_id: WebhookId
    ban_appeal_webhook_id: WebhookId
    ban_appeal_reaction_role: RoleId
    aegis_ping_role: RoleId

    vctable_prefix: str
    custom_vc_blacklist_prefix: str
    custom_vc_blacklisted_channels: list[VoiceChannelId]
    custom_vc_create_channel: VoiceChannelId
    custom_vc_category: CategoryChannelId

    starboard_channel: MessageableChannelId
    starboard_upvote_emoji: EmojiId
    starboard_blacklisted_channels: list[MessageableChannelId]
    starboard_minimum_upvote_count: int
    starboard_minimum_vote_count_for_downvote_delete: int

    bump_reminder_channel: MessageableChannelId
    bump_reminder_role: RoleId
    bump_reminder_bot: UserId

    poll_reaction_blacklisted_channels: list[MessageableChannelId]

    selfies_channel: MessageableChannelId

    voice_channel_activity_logs_channel: MessageableChannelId

    headpat_emoji: EmojiId
    awawawa_emoji: EmojiId

    polls_only_channel: TextChannelId
    polls_channel_reaction_role: RoleId

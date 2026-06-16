import dataclasses
from resources.abc import MessageableGuildChannel

import discord


type GuildAttributeType = (
    str | int
    | discord.Guild
    | MessageableGuildChannel | list[MessageableGuildChannel]
    | discord.TextChannel
    | discord.CategoryChannel
    | discord.Emoji
    | discord.Role | list[discord.Role]
    | discord.User
    | discord.VoiceChannel
    | discord.ForumChannel
)


@dataclasses.dataclass
class ServerAttributes:
    """A dictionary containing all customizable guild attributes.

    This is stored in the client.
    """

    # When adding a new key to this class, make sure to add the same
    #  key to the ServerAttributes class.
    # If you're giving it a new type, make sure it gets parsed in
    #  ServerSettings.get_attributes().

    parent_server: discord.Guild | None = None

    admin_roles: list[discord.Role] = dataclasses.field(default_factory=list)
    staff_roles: list[discord.Role] = dataclasses.field(default_factory=list)

    log_channel: MessageableGuildChannel | None = None

    qotw_suggestions_channel: discord.TextChannel | None = None
    developer_request_channel: discord.TextChannel | None = None
    # ^ needs to be able to have threads
    developer_request_reaction_role: discord.Role | None = None

    watchlist_channel: discord.TextChannel | None = None
    # ^ needs to be able to have threads
    watchlist_reaction_role: discord.Role | None = None
    staff_reports_channel: MessageableGuildChannel | None = None
    ticket_create_channel: MessageableGuildChannel | None = None
    staff_logs_category: discord.CategoryChannel | None = None
    badeline_bot: discord.User | None = None

    # Webhooks require async fetching, so instead I opted for storing
    #  only their ID, so they can be compared with Message.webhook_id.
    anonymous_reports_webhook_id: int | None = None  # Webhook = None
    ban_appeal_webhook_id: int | None = None  # Webhook = None
    ban_appeal_reaction_role: discord.Role | None = None
    aegis_ping_role: discord.Role | None = None

    vctable_prefix: str | None = None
    custom_vc_blacklist_prefix: str | None = None
    custom_vc_blacklisted_channels: list[discord.VoiceChannel] = dataclasses.field(default_factory=list)
    custom_vc_create_channel: discord.VoiceChannel | None = None
    custom_vc_category: discord.CategoryChannel | None = None

    starboard_channel: MessageableGuildChannel | None = None
    starboard_upvote_emoji: discord.Emoji | None = None
    starboard_blacklisted_channels: list[MessageableGuildChannel] = dataclasses.field(default_factory=list)
    starboard_minimum_upvote_count: int | None = None
    starboard_minimum_vote_count_for_downvote_delete: int | None = None

    bump_reminder_channel: MessageableGuildChannel | None = None
    bump_reminder_role: discord.Role | None = None
    bump_reminder_bot: discord.User | None = None

    poll_reaction_blacklisted_channels: list[MessageableGuildChannel] = dataclasses.field(default_factory=list)

    selfies_channel: MessageableGuildChannel | None = None

    voice_channel_activity_logs_channel: MessageableGuildChannel | None = None

    headpat_emoji: discord.Emoji | None = None
    awawawa_emoji: discord.Emoji | None = None

    polls_only_channel: discord.TextChannel | None = None
    # ^ needs to be able to have threads
    polls_channel_reaction_role: discord.Role | None = None


def default_server_attributes[T](default: T | None = None) -> ServerAttributes:
    out = ServerAttributes()
    if default is not None:
        # replace None values with `default`.
        for attr in dir(out):
            if out.__dict__[attr] is None:
                out.__dict__[attr] = default
    return out

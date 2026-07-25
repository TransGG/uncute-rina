import dataclasses
import typing

import discord

from resources.abc import MessageableGuildChannel

if typing.TYPE_CHECKING:
    from resources.customs.bot import Bot


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
    _guild_id: int

    parent_server: discord.Guild | None = None

    admin_roles: list[discord.Role] = dataclasses.field(default_factory=list)
    staff_roles: list[discord.Role] = dataclasses.field(default_factory=list)

    log_channel: MessageableGuildChannel | None = None

    qotw_suggestions_channel: discord.TextChannel | None = None
    developer_request_channel: discord.TextChannel | None = None
    # ^ needs to be able to have threads
    developer_request_reaction_role: discord.Role | None = None
    developer_request_bot_prefixes: list[str] = dataclasses.field(default_factory=list)

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

    def get_exclusively_child_guilds(self, bot: Bot) -> set[int]:
        """Get a list of *just this server's* child guild ids"""
        guild_ids: set[int] = set()
        if bot.server_settings is None:
            return guild_ids  # todo: raise error?

        for guild_id, settings in bot.server_settings.items():
            if getattr(settings.attributes.parent_server, "id", -1) == self._guild_id:
                guild_ids.add(guild_id)

        return guild_ids

    def get_all_child_guilds(self, bot: Bot) -> set[int]:
        """Get a *recursive* list of child guild ids"""
        # Is a O(n^n) function.
        if bot.server_settings is None:
            return set()  # todo: raise error?

        guild_ids: set[int] = self.get_exclusively_child_guilds(bot)
        child_accumulator: set[int] = set()
        # ^ so you don't update the set while iterating.
        for guild_id in guild_ids:
            child_attributes = bot.server_settings[guild_id].attributes
            child_map = child_attributes.get_all_child_guilds(bot)
            child_accumulator.update(child_map)
        guild_ids.update(child_accumulator)

        return guild_ids


def default_server_attributes[T](default: T | None = None) -> ServerAttributes:
    out = ServerAttributes(0)
    if default is not None:
        # replace None values with `default`.
        for attr in dir(out):
            if out.__dict__[attr] is None:
                out.__dict__[attr] = default
    return out

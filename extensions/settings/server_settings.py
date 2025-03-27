from __future__ import annotations
import motor.core

import discord

from resources.customs.bot import Bot


GuildId = int
MessageChannel = discord.TextChannel | discord.Thread


def get_channel_argument(
        invalid_arguments: dict[str, str | list[str]],
        invalid_argument_name: str,
        client: Bot,
        channel_id: int,
) -> (
        discord.VoiceChannel |
        discord.StageChannel |
        discord.ForumChannel |
        discord.TextChannel |
        discord.CategoryChannel |
        discord.Thread |
        discord.abc.PrivateChannel |
        None
):
    """
    Try to get the channel corresponding to a channel id. If the channel is not found, add the argument name to
    invalid_arguments.

    Parameters
    -----------
    invalid_arguments :class:`dict[str, str | list[str]]`:
        A dictionary of previous invalid arguments with which to add the argument name if the requested channel is
        not found.
    invalid_argument_name :class:`str`:
        The argument name to add to the invalid_arguments dictionary, if the requested channel is not found.
    client :class:`Bot`:
        The client with which to fetch the channel from the channel id.
    channel_id :class:`int`:
        The id of the channel to look up (and if not found, to add to the invalid_arguments dictionary)

    Returns
    --------
    The channel matching the given channel_id, or None if not found.

    Regards
    --------
    Since invalid_arguments is a dictionary, it will be passed as reference. It is updated inside the function, but
    it will also update the original dictionary object.
    """
    channel = None
    if channel_id is not None:
        channel = client.get_channel(channel_id)
        if channel is None:
            invalid_arguments[invalid_argument_name] = str(channel_id)
    return channel


def get_role_argument(
        invalid_arguments: dict[str, str | list[str]],
        invalid_argument_name: str,
        server: discord.Guild | None,
        role_id: int,
) -> discord.Role:
    """
    Try to get the role corresponding to a role id. If the channel is not found, add the argument name to
    invalid_arguments.

    Parameters
    -----------
    invalid_arguments :class:`dict[str, str | list[str]]`:
        A dictionary of previous invalid arguments with which to add the argument name if the requested role is
        not found.
    invalid_argument_name :class:`str`:
        The argument name to add to the invalid_arguments dictionary, if the requested role is not found.
    server :class:`discord.Guild | None`:
        The guild with which to fetch the role from the role id. If this is None, the role won't be added to the
        invalid_arguments dictionary, but will still return None.
    role_id :class:`int`:
        The id of the role to look up (and if not found, to add to the invalid_arguments dictionary)

    Returns
    --------
    The role matching the given role_id, or None if not found or if `server` is None.

    Regards
    --------
    Since invalid_arguments is a dictionary, it will be passed as reference. It is updated inside the function, but
    it will also update the original dictionary object.
    """
    role = None
    if role_id is not None and server is not None:
        role = server.get_role(role_id)
        if role is None:
            invalid_arguments[invalid_argument_name] = str(role_id)
    return role


def get_user_argument(
        invalid_arguments: dict[str, str | list[str]],
        invalid_argument_name: str,
        client: Bot,
        user_id: int,
) -> discord.User:
    user = None
    if user_id is not None:
        user = client.get_user(user_id)
        if user is None:
            invalid_arguments[invalid_argument_name] = str(user_id)
    return user


def get_roles_in_list(
        invalid_arguments: dict[str, str | list[str]],
        invalid_argument_name: str,
        server: discord.Guild,
        role_ids: [int],
) -> list[discord.Role]:
    roles = []
    invalid_role_ids: list[str] = []
    for role_id in role_ids and server is not None:
        role = server.get_role(role_id)
        if role is None:
            invalid_role_ids.append(str(role_id))
        else:
            roles.append(role)
    invalid_arguments.append(invalid_argument_name + f": [{','.join(invalid_role_ids)}]")
    return roles


class ServerSettings:
    @staticmethod
    async def migrate(async_rina_db: motor.code.AgnosticDatabase):
        query = {"guild_id": itx.guild_id}
        old_collection: motor.MotorCollection = await async_rina_db["guildInfo"]

        await old_collection.find_one(query)

    @staticmethod
    async def load_all(async_rina_db: motor.core.AgnosticDatabase) -> list[ServerSettings]:
        query = {}
        collection: motor.MotorCollection = await async_rina_db["server_settings"]
        all_settings = await collection.find()
        # todo: implement. lol
        if all_settings is None:
            return []
        return []

    @staticmethod
    def from_ids(
            itx: discord.Interaction,
            parent_server: ServerSettings | None,
            child_servers: dict[GuildId, ServerSettings] | None,
            server_id: int,

            qotw_suggestions_channel_id: int | None,
            developer_request_channel_id: int | None,
            watchlist_channel_id: int | None,
            badeline_bot_id: int | None,
            staff_logs_category_id: int | None,
            staff_reports_channel_id: int | None,
            ban_appeal_reaction_role_id: int | None,
            watchlist_reaction_role_id: int | None,
            developer_request_reaction_role_id: int | None,
            ticket_create_channel_id: int | None,

            staff_role_ids: list[int],
            admin_role_ids: list[int],
            owner_role_ids: list[int],

            ban_appeal_webhook_id: int | None,
            vctable_prefix: str | None,
            aegis_ping_role_id: int | None,
    ) -> ServerSettings:
        invalid_arguments: dict[str, str | list[str]] = {}

        if child_servers is None:
            child_servers = {}
        server = itx.client.get_guild(server_id)
        if server is None:
            invalid_arguments.append(f"server_id: {server_id}")

        qotw_suggestions_channel = get_channel_argument(
            invalid_arguments, "qotw_suggestions_channel_id",
            itx.client, qotw_suggestions_channel_id)
        developer_request_channel = get_channel_argument(
            invalid_arguments, "developer_request_channel_id",
            itx.client, developer_request_channel_id)
        staff_reports_channel = get_channel_argument(
            invalid_arguments, "staff_reports_channel_id",
            itx.client, staff_reports_channel_id)
        staff_logs_category = get_channel_argument(
            invalid_arguments, "staff_logs_category_id",
            itx.client, staff_logs_category_id)
        watchlist_channel = get_channel_argument(
            invalid_arguments, "watchlist_channel_id",
            itx.client, watchlist_channel_id)
        ticket_create_channel = get_channel_argument(
            invalid_arguments, "ticket_create_channel_id",
            itx.client, ticket_create_channel_id)

        watchlist_reaction_role = get_role_argument(
            invalid_arguments, "watchlist_reaction_role_id",
            itx.client, watchlist_reaction_role_id)
        ban_appeal_reaction_role = get_role_argument(
            invalid_arguments, "ban_appeal_reaction_role_id",
            itx.client, ban_appeal_reaction_role_id)
        developer_request_reaction_role = get_role_argument(
            invalid_arguments, "developer_request_reaction_role_id",
            itx.client, developer_request_reaction_role_id)

        badeline_bot = get_user_argument(
            invalid_arguments, "badeline_bot_id",
            itx.client, badeline_bot_id)

        staff_roles = get_roles_in_list(
            invalid_arguments, "staff_role_ids",
            server, staff_role_ids)
        admin_roles = get_roles_in_list(
            invalid_arguments, "admin_role_ids",
            server, admin_role_ids)
        owner_roles = get_roles_in_list(
            invalid_arguments, "owner_role_ids",
            server, owner_role_ids)

        if len(invalid_arguments) > 0:
            raise ValueError("Some server settings for {} are unset!\n" + ','.join(invalid_arguments))

        return ServerSettings(
            parent_server=parent_server,
            child_servers=child_servers,
            server=server,

            qotw_suggestions_channel=qotw_suggestions_channel,
            developer_request_channel=developer_request_channel,
            watchlist_channel=watchlist_channel,
            badeline_bot=badeline_bot,
            staff_logs_category=staff_logs_category,
            staff_reports_channel=staff_reports_channel,
            ban_appeal_reaction_role=ban_appeal_reaction_role,
            watchlist_reaction_role=watchlist_reaction_role,
            developer_request_reaction_role=developer_request_reaction_role,
            ticket_create_channel=ticket_create_channel,

            staff_roles=staff_roles,
            admin_roles=admin_roles,
            owner_roles=owner_roles,

            ban_appeal_webhook_id=ban_appeal_webhook_id,
            vctable_prefix=vctable_prefix,
            aegis_ping_role_id=aegis_ping_role_id,
        )

    def __init__(
            self, *,
            parent_server: ServerSettings | None,
            child_servers: dict[GuildId, ServerSettings] | None,
            server: discord.Guild,  # transplace_server_id,

            qotw_suggestions_channel: MessageChannel | None,
            developer_request_channel: MessageChannel | None,
            watchlist_channel: MessageChannel | None,
            badeline_bot: discord.User | None,
            staff_logs_category: discord.CategoryChannel | None,
            staff_reports_channel: MessageChannel | None,
            ban_appeal_reaction_role: discord.Role | None,
            watchlist_reaction_role: discord.Role | None,
            developer_request_reaction_role: discord.Role | None,
            ticket_create_channel: MessageChannel | None,

            staff_roles: list[discord.Role],
            admin_roles: list[discord.Role],
            owner_roles: list[discord.Role],

            ban_appeal_webhook_id: int | None,
            vctable_prefix: str | None,
            aegis_ping_role_id: int | None
    ):
        self.parent_server = parent_server
        self.child_servers = child_servers
        self.server = server

        self.qotw_suggestions_channel = qotw_suggestions_channel
        self.developer_request_channel = developer_request_channel
        self.watchlist_channel = watchlist_channel
        self.badeline_bot = badeline_bot
        self.staff_logs_category = staff_logs_category
        self.staff_reports_channel = staff_reports_channel
        self.ban_appeal_reaction_role = ban_appeal_reaction_role
        self.watchlist_reaction_role = watchlist_reaction_role
        self.developer_request_reaction_role = developer_request_reaction_role
        self.ticket_create_channel = ticket_create_channel

        self.staff_roles = staff_roles
        self.admin_roles = admin_roles
        self.owner_roles = owner_roles

        self.ban_appeal_webhook_id = ban_appeal_webhook_id
        self.vctable_prefix = vctable_prefix
        self.aegis_ping_role_id = aegis_ping_role_id

    def add_child_server(self, settings: ServerSettings):
        self.child_servers[settings.server.id] = settings

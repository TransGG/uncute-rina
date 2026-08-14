from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from resources.customs import Bot


def is_staff(
        itx: discord.Interaction[Bot] | tuple[Bot, discord.Guild],
        member: discord.Member | discord.User
) -> bool:
    """
    Check if someone is staff.

    :param itx: The interaction with ``itx.client.server_settings``
     and ``itx.guild``. Or a tuple of the client and the guild.
    :param member: A discord user with or without roles attribute.

    :return: Whether the user has a staff role.
    """
    if isinstance(member, discord.User):
        # No roles, no server, so no staff
        return False

    if isinstance(itx, discord.Interaction):
        client = itx.client
        guild = itx.guild
    else:
        client, guild = itx

    if guild is None:
        # No server, so no staff
        return False

    # The passed keys will only correspond to roles, so this cast is fine
    staff_roles: list[discord.Role] = client.get_guild_attributes(
        guild).staff_roles
    roles_set: set[discord.Role] = set(staff_roles)
    return (
        len(roles_set.intersection(member.roles)) > 0
        or is_admin(itx, member)
    )


def is_admin(
        itx: discord.Interaction[Bot] | tuple[Bot, discord.Guild],
        member: discord.Member | discord.User
) -> bool:
    """
    Check if someone is an admin.

    :param itx: The interaction with ``itx.client.server_settings``
     and ``itx.guild``. Or a tuple of the client and the guild.
    :param member: A discord user with or without roles attribute.

    :return: Whether the user has an admin role.
    """
    if isinstance(itx, discord.Interaction):
        client = itx.client
        guild = itx.guild
    else:
        client, guild = itx

    if isinstance(member, discord.User) or guild is None:
        # No roles, no server, so no staff
        return False

    # The passed keys will only correspond to roles, so this cast is fine
    admin_roles = client.get_guild_attributes(
        guild).admin_roles
    roles_set: set[discord.Role] = set(admin_roles)
    return (
        len(roles_set.intersection(member.roles)) > 0
        or member.id == guild.owner_id
        or member.id == client.bot_owner.id
    )

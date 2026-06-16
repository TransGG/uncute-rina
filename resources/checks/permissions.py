from __future__ import annotations
import discord

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from resources.customs import Bot


def is_staff(
        itx: discord.Interaction[Bot],
        member: discord.Member | discord.User
) -> bool:
    """
    Check if someone is staff.

    :param itx: The interaction with ``itx.client.server_settings``
     and ``itx.guild``.
    :param member: A discord user with or without roles attribute.

    :return: Whether the user has a staff role.
    """
    if isinstance(member, discord.User):
        # No roles, no server, so no staff
        return False

    if itx.guild is None:
        # No server, so no staff
        return False

    # The passed keys will only correspond to roles, so this cast is fine
    staff_roles: list[discord.Role] = itx.client.get_guild_attributes(
        itx.guild).staff_roles
    roles_set: set[discord.Role] = set(staff_roles)
    return (
        len(roles_set.intersection(member.roles)) > 0
        or is_admin(itx, member)
    )


def is_admin(
        itx: discord.Interaction[Bot],
        member: discord.Member | discord.User
) -> bool:
    """
    Check if someone is an admin.

    :param itx: The interaction with ``itx.client.server_settings``
     and ``itx.guild``.
    :param member: A discord user with or without roles attribute.

    :return: Whether the user has an admin role.
    """
    if isinstance(member, discord.User) or itx.guild is None:
        # No roles, no server, so no staff
        return False

    # The passed keys will only correspond to roles, so this cast is fine
    admin_roles = itx.client.get_guild_attributes(
        itx.guild).admin_roles
    roles_set: set[discord.Role] = set(admin_roles)
    return (
        len(roles_set.intersection(member.roles)) > 0
        or member.id == itx.guild.owner_id
        or member.id == itx.client.bot_owner.id
    )

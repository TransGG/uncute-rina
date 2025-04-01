from __future__ import annotations
import discord

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from resources.customs.bot import Bot


def is_verified(itx: discord.Interaction[Bot], member: discord.Member | discord.User) -> bool:
    """
    Check if someone is verified.

    :param itx: The interaction with ``itx.client.server_settings`` and ``itx.guild``.
    :param member: A discord user with or without roles attribute.

    :return: Whether the user is verified.
    """
    return is_staff(itx, member)


def is_staff(itx: discord.Interaction[Bot], member: discord.Member | discord.User) -> bool:
    """
    Check if someone is staff.

    :param itx: The interaction with ``itx.client.server_settings`` and ``itx.guild``.
    :param member: A discord user with or without roles attribute.

    :return: Whether the user has a staff role.
    """
    staff_roles: list[discord.Role | None] | None = itx.client.get_guild_attribute(itx.guild, "staff_roles")
    if staff_roles is None:
        staff_roles = []
    roles_set: set[discord.Role] = set(staff_roles) - { None }
    return (
        is_admin(itx, member) or
        len(roles_set.intersection(member.roles)) > 0
    )


def is_admin(itx: discord.Interaction[Bot], member: discord.Member | discord.User) -> bool:
    """
    Check if someone is an admin.

    :param itx: The interaction with ``itx.client.server_settings`` and ``itx.guild``.
    :param member: A discord user with or without roles attribute.

    :return: Whether the user has an admin role.
    """
    admin_roles: list[discord.Role | None] | None = itx.client.get_guild_attribute(itx.guild, "admin_roles")
    if admin_roles is None:
        admin_roles = []
    roles_set: set[discord.Role] = set(admin_roles) - { None }
    return (
            member.id == itx.guild.owner_id or
            member.id == itx.client.bot_owner.id or
            len(roles_set.intersection(member.roles)) > 0
    )

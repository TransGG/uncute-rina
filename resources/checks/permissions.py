from __future__ import annotations
import discord

from typing import TYPE_CHECKING

from extensions.settings.objects import AttributeKeys

if TYPE_CHECKING:
    from resources.customs import Bot


def is_staff(itx: discord.Interaction[Bot], member: discord.Member | discord.User) -> bool:
    """
    Check if someone is staff.

    :param itx: The interaction with ``itx.client.server_settings`` and ``itx.guild``.
    :param member: A discord user with or without roles attribute.

    :return: Whether the user has a staff role.
    """
    staff_roles: list[discord.Role] = itx.client.get_guild_attribute(
        itx.guild, AttributeKeys.staff_roles, default=[])
    roles_set: set[discord.Role] = set(staff_roles)
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
    admin_roles: list[discord.Role] = itx.client.get_guild_attribute(
        itx.guild, AttributeKeys.admin_roles, default=[])
    roles_set: set[discord.Role] = set(admin_roles)
    return (
            member.id == itx.guild.owner_id or
            member.id == itx.client.bot_owner.id or
            len(roles_set.intersection(member.roles)) > 0
    )

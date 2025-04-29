import discord

from resources.checks.permissions import is_staff, is_admin
from .errors import CommandDoesNotSupportDMsCheckFailure, InsufficientPermissionsCheckFailure
from .command_checks import is_in_dms


def is_staff_check(itx: discord.Interaction):
    """
    A check to check if the command executor has a staff role.
    :param itx: The interaction to check.
    :return: ``True`` if the executor has a staff role, else an exception.
    :raise InsufficientPermissionsCheckFailure: If the user does not have a staff role.
    """
    if is_in_dms(itx.guild):
        return CommandDoesNotSupportDMsCheckFailure()
    if is_staff(itx, itx.user):
        return True
    raise InsufficientPermissionsCheckFailure("User is not staff")


def is_admin_check(itx: discord.Interaction):
    """
    A check to check if the command executor has an admin role.
    :param itx: The interaction to check.
    :return: ``True`` if the executor has an admin role, else an exception.
    :raise InsufficientPermissionsCheckFailure: If the user does not have an admin role.
    """
    if is_in_dms(itx.guild):
        return CommandDoesNotSupportDMsCheckFailure()
    if is_admin(itx, itx.user):
        return True
    raise InsufficientPermissionsCheckFailure("User is not admin")

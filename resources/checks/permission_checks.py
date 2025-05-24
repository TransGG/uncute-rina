from __future__ import annotations
from typing import TYPE_CHECKING

import discord

from .permissions import is_staff, is_admin
from .errors import (
    CommandDoesNotSupportDMsCheckFailure,
    InsufficientPermissionsCheckFailure
)
from .command_checks import is_in_dms

if TYPE_CHECKING:
    from resources.customs import Bot


def is_staff_check(itx: discord.Interaction[Bot]):
    """
    A check to check if the command executor has a staff role.

    :param itx: The interaction to check.
    :return: ``True`` if the executor has a staff role, else
     an exception.
    :raise InsufficientPermissionsCheckFailure: If the user does not
     have a staff role.
    :raise CommandDoesNotSupportDMsCheckFailure: If the command was
     executed in DMs
    """
    if is_in_dms(itx.guild):
        raise CommandDoesNotSupportDMsCheckFailure()
    if is_staff(itx, itx.user):
        return True
    raise InsufficientPermissionsCheckFailure("User is not staff")


def is_admin_check(itx: discord.Interaction[Bot]):
    """
    A check to check if the command executor has an admin role.

    :param itx: The interaction to check.
    :return: ``True`` if the executor has an admin role, else an
     exception.
    :raise InsufficientPermissionsCheckFailure: If the user does not
     have an admin role.
    :raise CommandDoesNotSupportDMsCheckFailure: If the command was
     executed in DMs
    """
    if is_admin(itx, itx.user):  # can raise DMsCheckFailure
        return True
    raise InsufficientPermissionsCheckFailure("User is not admin")

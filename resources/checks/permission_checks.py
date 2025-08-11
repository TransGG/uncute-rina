from __future__ import annotations

import discord
from discord import app_commands
from typing import TYPE_CHECKING, Any

from .permissions import is_staff, is_admin
from .errors import (
    CommandDoesNotSupportDMsCheckFailure,
    InsufficientPermissionsCheckFailure
)
from .command_checks import is_in_dms

if TYPE_CHECKING:
    from resources.customs import Bot

    from discord.app_commands.commands import (
        CommandCallback, GroupT, P, T,
    )


def is_staff_check(
        func: CommandCallback[Any, ..., Any]
) -> CommandCallback[GroupT, P, T]:
    def decor_check(itx: discord.Interaction[Bot]) -> bool:
        """
        A check to check if the command/interaction was run by a staff member
        of this server.

        :param itx: The interaction to check.
        :return: ``True`` if the interaction was run by a staff member, else
         an exception.
        :raise CommandDoesNotSupportDMsCheckFailure: If the command was run
         outside a server.
        :raise InsufficientPermissionsCheckFailure: If the command was not run
         by a staff member.
        """
        if is_in_dms(itx.guild):
            raise CommandDoesNotSupportDMsCheckFailure()
        if is_staff(itx, itx.user):
            return True
        raise InsufficientPermissionsCheckFailure("User is not staff")

    app_commands.check(decor_check)(func)
    return func


def is_admin_check(
        func: CommandCallback[Any, ..., Any]
) -> CommandCallback[GroupT, P, T]:
    def decor_check(itx: discord.Interaction[Bot]) -> bool:
        """
        A check to check if the command/interaction was run by an admin staff
        member of this server.

        :param itx: The interaction to check.
        :return: ``True`` if the interaction was run by an admin, else
         an exception.
        :raise CommandDoesNotSupportDMsCheckFailure: If the command was run
         outside a server.
        :raise InsufficientPermissionsCheckFailure: If the command was not run
         by an admin.
        """
        if is_in_dms(itx.guild):
            raise CommandDoesNotSupportDMsCheckFailure()
        if is_admin(itx, itx.user):
            return True
        raise InsufficientPermissionsCheckFailure("User is not admin")

    app_commands.check(decor_check)(func)
    return func

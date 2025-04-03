from __future__ import annotations
from typing import TYPE_CHECKING

import discord
import discord.app_commands as app_commands

from resources.checks.errors import ModuleNotEnabledCheckFailure, CommandDoesNotSupportDMsCheckFailure

if TYPE_CHECKING:
    from resources.customs import Bot


def module_enabled_check(module_key):
    """
    A check to check if a module is enabled.

    :param module_key: The key of the module to check.
    :return: A decorator that checks if the given module is enabled in the interaction's guild.
    """
    async def decor_check(itx: discord.Interaction[Bot]):
        """
        A decorator that checks if the interaction's guild has a module enabled.
        :param itx: The interaction with the guild to check (and the itx.client to check it with).
        :return: ``True`` if the module is enabled, else an exception.
        :raise ModuleNotEnabledCheckFailure: If the module is not enabled.
        :raise CommandDoesNotSupportDMsCheckFailure: If the command was run outside a server
         (-> no modules = no attributes).
        """
        if itx.guild is None:
            raise CommandDoesNotSupportDMsCheckFailure()
        if itx.client.is_module_enabled(itx.guild, module_key):
            return True
        raise ModuleNotEnabledCheckFailure(module_key)
    return app_commands.check(decor_check)


def not_in_dms_check(itx: discord.Interaction[Bot]) -> bool:
    """
    A check to check if the command/interaction was run in DMs.
    :param itx: The interaction to check.
    :return: ``True`` if the interaction was not in a DM, else an exception.
    :raise CommandDoesNotSupportDMsCheckFailure: If the command was run outside a server.
    """
    if is_in_dms(itx.guild):
        raise CommandDoesNotSupportDMsCheckFailure()
    return True


def is_in_dms(guild: discord.Guild | int | None) -> bool:
    """
    A simple function to check if a command was run in a DM.
    :param guild: The guild or guild id to check...... This function is just a one-liner...
    :return: Whether the command was run in DMs.
    """
    return guild is None


def module_not_disabled_check(module_key: str):
    """
    A check to check if a module is not disabled.

    :param module_key: The key of the module to check.
    :return: A decorator that checks if the given module is disabled in the interaction's guild.
    """
    async def decor_check(itx: discord.Interaction[Bot]) -> bool:
        """
        A check to check if a command is allowed to be used in the current channel. This will be allowed in DMs, but
        not in servers that don't explicitly enabled the module.

        :param itx: The interaction with the guild and :py:func:`Bot.is_module_enabled` function.
        :return: ``True`` if the check passed.
        :raise ModuleNotEnabledCheckFailure: If the command was run in a server, and the server did not have the
         module enabled.
        """
        """
        A decorator that checks if the interaction's guild has a module enabled.
        :param itx: The interaction with the guild to check (and the itx.client to check it with).
        :return: ``True`` if the module is enabled, else an exception.
        :raise ModuleNotEnabledCheckFailure: If the module is not enabled.
        :raise CommandDoesNotSupportDMsCheckFailure: If the command was run outside a server
         (-> no modules = no attributes).
        """
        if is_in_dms(itx.guild):
            return True
        if itx.client.is_module_enabled(itx.guild, module_key):
            return True
        raise ModuleNotEnabledCheckFailure(module_key)
    return app_commands.check(decor_check)

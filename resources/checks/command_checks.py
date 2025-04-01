from __future__ import annotations
from typing import TYPE_CHECKING

import discord.app_commands as app_commands

from resources.checks.errors import ModuleNotEnabledCheckFailure, CommandDoesNotSupportDMsCheckFailure

if TYPE_CHECKING:
    import discord
    from resources.customs.bot import Bot


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


def not_in_dms_check(itx: discord.Interaction[Bot]):
    """
    A check to check if the command/interaction was run in DMs.
    :param itx: The interaction to check.
    :return: ``True`` if the interaction was not in a DM, else an exception.
    :raise CommandDoesNotSupportDMsCheckFailure: If the command was run outside a server.
    """
    if itx.guild is not None:
        return True
    raise CommandDoesNotSupportDMsCheckFailure()

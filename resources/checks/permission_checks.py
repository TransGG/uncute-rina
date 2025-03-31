import discord
import discord.app_commands as app_commands

from resources.utils.permissions import is_staff, is_admin

from .errors import InsufficientPermissionsCheckFailure


def is_staff_check(itx: discord.Interaction):
    if is_staff(itx.guild, itx.user):
        return True
    raise InsufficientPermissionsCheckFailure("User is not staff")


def is_admin_check(itx: discord.Interaction):
    if is_admin(itx.guild, itx.user):
        return True
    raise InsufficientPermissionsCheckFailure("User is not admin")

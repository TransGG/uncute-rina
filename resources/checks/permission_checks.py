import discord

from resources.utils.permissions import is_staff, is_admin

from .errors import InsufficientPermissionsCheckFailure


def is_staff_check(itx: discord.Interaction):
    if is_staff(itx, itx.user):
        return True
    raise InsufficientPermissionsCheckFailure("User is not staff")


def is_admin_check(itx: discord.Interaction):
    if is_admin(itx, itx.user):
        return True
    raise InsufficientPermissionsCheckFailure("User is not admin")

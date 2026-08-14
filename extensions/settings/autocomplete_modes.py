from enum import Enum

import discord
from discord import app_commands

from resources.customs import Bot


class TypeAutocomplete(Enum):
    help = "Help"
    attribute = "Attribute"
    module = "Module"


class TypeAutocompleteTransformer(app_commands.Transformer[Bot]):
    async def transform(self, itx: discord.Interaction[Bot], value: str, /) -> TypeAutocomplete:
        return TypeAutocomplete(value)


class ModeAutocomplete(Enum):
    set = "Set"
    delete = "Delete"
    add = "Add"
    remove = "Remove"
    enable = "Enable"
    disable = "Disable"
    view = "View"
    invalid = "-"


class ModeAutocompleteTransformer(app_commands.Transformer[Bot]):
    async def transform(self, itx: discord.Interaction[Bot], value: str, /) -> ModeAutocomplete:
        if value in ModeAutocomplete:
            return ModeAutocomplete(value)
        return ModeAutocomplete.invalid

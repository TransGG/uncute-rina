from enum import Enum

import discord
from discord import app_commands


class TypeAutocomplete(Enum):
    help = "Help"
    attribute = "Attribute"
    module = "Module"


class TypeAutocompleteTransformer(app_commands.Transformer):
    async def transform(self, itx: discord.Interaction, value: str, /) -> TypeAutocomplete:
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


class ModeAutocompleteTransformer(app_commands.Transformer):
    async def transform(self, itx: discord.Interaction, value: str, /) -> ModeAutocomplete:
        if value in ModeAutocomplete:
            return ModeAutocomplete(value)
        return ModeAutocomplete.invalid

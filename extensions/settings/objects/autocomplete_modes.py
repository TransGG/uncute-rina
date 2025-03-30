from enum import Enum

class TypeAutocomplete(Enum):
    attribute = "Attribute"
    module = "Module"

class ModeAutocomplete(Enum):
    set = "Set"
    delete = "Delete"
    add = "Add"
    remove = "Remove"
    enable = "Enable"
    disable = "Disable"
    view = "View"
    invalid = "-"

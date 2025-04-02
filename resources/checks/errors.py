from discord.app_commands import CheckFailure


class InsufficientPermissionsCheckFailure(CheckFailure):
    pass


class ModuleNotEnabledCheckFailure(CheckFailure):
    def __init__(self, module_key):
        self.module_key = module_key


class CommandDoesNotSupportDMsCheckFailure(CheckFailure):
    pass


class MissingAttributesCheckFailure(CheckFailure):
    def __init__(self, *attributes: str):
        self.attributes: list[str] = list(attributes)

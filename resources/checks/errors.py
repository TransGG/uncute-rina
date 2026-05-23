from discord.app_commands import CheckFailure


class InsufficientPermissionsCheckFailure(CheckFailure):
    pass


class ModuleNotEnabledCheckFailure(CheckFailure):
    def __init__(self, module_key: str) -> None:
        self.module_key = module_key


class CommandDoesNotSupportDMsCheckFailure(CheckFailure):
    pass


class MissingAttributesCheckFailure(CheckFailure):
    def __init__(self, module: str | None, attributes: list[str]) -> None:
        self.module: str | None = module
        self.attributes: list[str] = list(attributes)

    def __str__(self) -> str:
        return f"{self.module}; " + ', '.join(self.attributes)

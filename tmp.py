from typing import TypeAliasType
import typing
from extensions.settings.objects.server_settings import get_attribute_type

attribute_type, _ = get_attribute_type("attribute_key")

def is_attribute_type(val: type):
    f = any(
        val in typing.get_args(i.__value__)
        if type(i) is TypeAliasType
        else val is i
        for i in attribute_type
    )
    return f

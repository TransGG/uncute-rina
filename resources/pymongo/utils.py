def encode_field(field_name: str):
    """Replace disallowed MongoDB characters with allowed ones."""
    field_name = (field_name
                  .replace("%", "%0")
                  .replace(".", "%1")
                  .replace("$", "%2"))
    return field_name


def decode_field(field_name: str):
    """Revert replacement of disallowed MongoDB characters."""
    field_name = (field_name
                  .replace("%1", ".")
                  .replace("%2", "$")
                  .replace("%0", "%"))
    return field_name

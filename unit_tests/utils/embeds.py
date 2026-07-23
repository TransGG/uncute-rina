import discord
import typing

from discord.types import embed as d_embed


def get_embed_issues(embed: discord.Embed) -> tuple[list[str], int]:
    """
    Validate an embed object and return a list of potential issues.

    :param embed: The embed you want to validate

    :return: A tuple with a list of issue descriptions for embed content
     size length limits; and the sum of characters in the embed fields.

    .. note::

        This function is not perfect. Emojis like :newspaper: get converted
         to 📰, which would have a shorter character length.
    """
    issues = []
    total_characters = 0

    embed_dict: d_embed.Embed = embed.to_dict()
    for key, value in embed_dict.items():
        value_str: str  # mypy moment
        match key:
            case "title":
                value_str = typing.cast(str, value)  # mypy moment
                total_characters += len(value_str)
                if len(value_str) > 256:
                    issues.append(
                        f"Title length exceeds 256 characters (is '{len(value_str)}')."
                    )

            case "description":
                value_str = typing.cast(str, value)  # mypy moment
                total_characters += len(value_str)
                if len(value_str) > 4096:
                    issues.append(
                        f"Description length exceeds 4096 characters "
                        f"(is '{len(value_str)}')."
                    )

            case "fields":
                value_fields: list[d_embed.EmbedField] = typing.cast(list[d_embed.EmbedField], value)  # mypy moment
                if len(value_fields) > 25:
                    issues.append(
                        f"Embed contains more than 25 fields (is '{len(value_fields)}')."
                    )
                for field in value_fields:
                    for field_key, field_value in field.items():
                        char_count, issue_text = _validate_embed_field(
                            field, field_key, field_value)  # type: ignore[arg-type]
                        total_characters += char_count
                        if issue_text is not None:
                            issues.append(issue_text)

            case "footer":
                value_footer: d_embed.EmbedFooter = typing.cast(d_embed.EmbedFooter, value)  # mypy moment
                text = value_footer["text"]
                total_characters += len(text)
                if len(text) > 2048:
                    issues.append(
                        f"Footer length exceeds 2048 characters "
                        f"(is '{len(text)}')."
                    )

            case "author":
                value_author: d_embed.EmbedAuthor = typing.cast(d_embed.EmbedAuthor, value)
                for author_key, author_value_a in value_author.items():
                    author_value: str = typing.cast(str, author_value_a)  # mypy moment
                    if author_key == "name":
                        total_characters += len(author_value)
                        if len(author_value) > 256:
                            issues.append(
                                f"Author name '{author_value}' exceeds 256 "
                                f"characters (is '{len(author_value)}')."
                            )

    if total_characters > 6000:
        issues.append(f"Total character count of embed exceeds 6000 "
                      f"characters (is '{total_characters}').")

    return issues, total_characters


def _validate_embed_field(
        field: d_embed.EmbedField,
        field_key: str,
        field_value: str,
) -> tuple[int, str | None]:
    if field_key == "type":
        if field_value != "rich":
            return 0, (
                f"Field type '{field_value}' (for field with "
                f"name '{field['name']}') is not supported."
            )
    if field_key == "name":
        if len(field_value) > 256:
            return len(field_value), (
                f"Field name '{field_value}' exceeds 256 "
                f"characters (is '{len(field_value)}')."
            )
    if field_key == "value":
        if len(field_value) > 1024:
            return len(field_value), (
                f"Field value for field with name "
                f"'{field['name']}' exceeds 1024 characters "
                f"(is '{len(field_value)}')."
            )
    return 0, None

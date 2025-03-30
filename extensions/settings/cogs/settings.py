import typing

import discord
import discord.ext.commands as commands
import discord.app_commands as app_commands

from resources.customs.bot import Bot
from resources.utils.permissions import is_admin, is_admin_check

from extensions.help.cogs import send_help_menu
from extensions.settings.objects import (
    ServerSettings, ServerAttributes, ServerAttributeIds, EnabledModules, TypeAutocomplete, ModeAutocomplete, parse_attribute
)


# todo: make function for parsing channel / role / user
#  Maybe make it match a specific type (eg. discord.CategoryChannel/vc/member/user).
#  Maybe autocomplete with the right type? like autocompleting channel names

# todo: make function to parse a list of ^ one of the above
#  or maybe a mix of multiple
# todo: allow individual adding and removing from lists
# todo: make options an enum or flag (not strings/dictionary! ):


# todo: make settings that are changeable also an enum

# todo: maybe a function to re-fetch settings for a specific server
#  Like if a channel is deleted, or an emoji is removed. That you don't
#  have to completely restart Rina to re-fetch every setting.

# todo: ensure SystemAttributeIds.parent_server is not in a parent server's parent server
#  The same for checking if one of the child_servers contains self, to prevent cyclic dependencies.

@app_commands.check(is_admin_check)
async def _setting_autocomplete(itx: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    itx.namespace.type = typing.cast(str | None, itx.namespace.type)

    if itx.namespace.type == TypeAutocomplete.module.value:
        module_keys = list(EnabledModules.__required_keys__.union(EnabledModules.__optional_keys__))
        return [
            app_commands.Choice(name=key, value=key) for key in module_keys
            if current.lower() in key.lower()
        ][:10]
    elif itx.namespace.type == TypeAutocomplete.attribute.value:
        attribute_id_keys = list(ServerAttributeIds.__required_keys__.union(ServerAttributeIds.__optional_keys__))
        return [
            app_commands.Choice(name=key, value=key) for key in attribute_id_keys
            if current.lower() in key.lower()
        ][:10]
    else:
        return []

attribute_type_single_value = [ModeAutocomplete.set, ModeAutocomplete.delete]
attribute_type_list = [ModeAutocomplete.add, ModeAutocomplete.remove]

def get_attribute_autocomplete_type(attribute_key: str) -> list[ModeAutocomplete] | None:
    """
    Retrieve the autocomplete-type of a ServerAttributeId key. This is usually either a list or a single value.

    Returns
    -------
    The autocomplete type, or None if the attribute is not a valid key.
    """
    attribute_keys = list(ServerAttributeIds.__required_keys__.union(ServerAttributeIds.__optional_keys__))
    attribute_types = typing.get_type_hints(ServerAttributeIds)
    if attribute_key in attribute_keys:
        attribute_type = attribute_types[attribute_key]
        if typing.get_origin(attribute_type) is list:
            return attribute_type_list
        else:
            return attribute_type_single_value
    return None

def get_attribute_type(attribute_key: str) -> type | None:
    attribute_keys = list(ServerAttributes.__required_keys__.union(ServerAttributes.__optional_keys__))
    attribute_types = typing.get_type_hints(ServerAttributes)
    attribute_type = None
    if attribute_key in attribute_keys:
        attribute_type = attribute_types[attribute_key]
        if typing.get_origin(attribute_type) is typing.types.UnionType:  # typing.Union != typing.types.UnionType :/
            # original was: `list[T] | None` (`Union[list[T], None]`).
            #   get_origin returns `<class 'types.UnionType'>`
            #   get_args   returns `(list[T], <class 'NoneType'>)`.
            attribute_type = typing.get_args(attribute_type)[0]
        if typing.get_origin(attribute_type) is list:
            # original was `list[T]`. get_args returns `T`
            attribute_type = typing.get_args(attribute_type)[0]
    return attribute_type


@app_commands.check(is_admin_check)
async def _mode_autocomplete(itx: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    itx.namespace.type = typing.cast(str | None, itx.namespace.type)
    itx.namespace.setting = typing.cast(str | None, itx.namespace.setting)

    types = [ModeAutocomplete.view]

    if itx.namespace.type == TypeAutocomplete.module.value:
        module_keys = list(EnabledModules.__required_keys__.union(EnabledModules.__optional_keys__))
        if itx.namespace.setting in module_keys:
            types += [ModeAutocomplete.enable, ModeAutocomplete.disable]
            return [
                app_commands.Choice(name=key.value, value=key.value)
                for key in types if current.lower() in key.value.lower()
            ]
        return [app_commands.Choice(name="Invalid setting given.", value=ModeAutocomplete.invalid.value)]
    elif itx.namespace.type == TypeAutocomplete.attribute.value:
        autocomplete_type = get_attribute_autocomplete_type(itx.namespace.setting)
        if autocomplete_type is None:
            return [app_commands.Choice(name="Invalid setting given.", value=ModeAutocomplete.invalid.value)]
        types += autocomplete_type
        return [
            app_commands.Choice(name=key.value, value=key.value)
            for key in types if current.lower() in key.value.lower()
        ]
    else:
        return []

async def _value_autocomplete(itx: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    itx.namespace.type = typing.cast(str | None, itx.namespace.type)
    itx.namespace.mode = typing.cast(str | None, itx.namespace.mode)
    itx.namespace.setting = typing.cast(str | None, itx.namespace.setting)
    itx.namespace.value = typing.cast(str | None, itx.namespace.value)

    if itx.namespace.type == TypeAutocomplete.attribute.value:
        if itx.namespace.mode == ModeAutocomplete.view.value:
            return [app_commands.Choice(name="This parameter is unnecessary when viewing a state", value="-")]

        attribute_type = get_attribute_type(itx.namespace.setting)
        if attribute_type is None:
            return [app_commands.Choice(name="Invalid setting given.", value="-")]

        results = []
        if issubclass(attribute_type, discord.Guild):
            for guild in itx.client.guilds:
                if current in guild.name or str(guild.id).startswith(current):
                    results.append(app_commands.Choice(name=guild.name, value=str(guild.id)))
        elif issubclass(attribute_type, discord.abc.GuildChannel):
            for channel in itx.guild.channels:
                if (isinstance(channel, attribute_type) and
                    (current in channel.name or str(channel.id).startswith(current))
                ):
                    results.append(app_commands.Choice(name=channel.name, value=str(channel.id)))
        elif issubclass(attribute_type, discord.User):
            # Note: discord.User is a subclass of discord.abc.Messageable, so should be tested before that too.
            for member in itx.guild.members:
                if current in member.name or str(member.id).startswith(current):
                    results.append(app_commands.Choice(name=member.name, value=str(member.id)))
                if len(results) > 20:
                    break
            if current.isdecimal():
                potential_user = itx.client.get_user(int(current))
                if potential_user is not None:
                    results.append(app_commands.Choice(name=potential_user.name, value=str(potential_user.id)))
        elif issubclass(attribute_type, discord.abc.Messageable):
            if current.isdecimal():
                potential_channel = itx.client.get_channel(int(current))
                if potential_channel is not None:
                    results.append(app_commands.Choice(
                        name=potential_channel.name, value=str(potential_channel.id)))
        elif issubclass(attribute_type, discord.Role):
            for role in itx.guild.roles:
                if current in role.name or str(role.id).startswith(current):
                    results.append(app_commands.Choice(name=role.name, value=str(role.id)))
        elif issubclass(attribute_type, discord.Emoji):
            for emoji in itx.guild.emojis:
                if current in emoji.name or str(emoji.id).startswith(current):
                    results.append(app_commands.Choice(name=emoji.name, value=str(emoji.id)))
        elif attribute_type == str:
            results.append(app_commands.Choice(name=current, value=current))
        elif attribute_type == int:
            if current.isdecimal():
                results.append(app_commands.Choice(name=current, value=current))
        else:
            results.append(
                app_commands.Choice(name=f"Autocomplete for type '{attribute_type.__name__}' not supported"[:100],
                                    value="-"))
        return results[:10]

    elif itx.namespace.type == TypeAutocomplete.module.value:
        return [
            app_commands.Choice(name="This parameter is unnecessary when toggling module state", value="-"),
        ]
    else:
        return []

class SettingsCog(commands.Cog):
    def __init__(self):
        pass

    @app_commands.command(name="migrate", description="Migrate bot settings to new database.")
    async def migrate(
            self,
            itx: discord.Interaction
    ):
        if not is_admin(itx.guild, itx.user):
            pass
        await ServerSettings.migrate(itx.client.async_rina_db)
        itx.response = typing.cast(discord.InteractionResponse, itx.response)
        await itx.response.send_message("Successfully migrated databases.", ephemeral=True)

    @app_commands.command(name="settings", description="Edit bot settings for this server.")
    @app_commands.describe(setting_type="What do you want to modify?",
                           setting="The setting you want to see/modify",
                           mode="How do you want to modify it?",
                           value="The thing you want to add/remove")
    @app_commands.rename(setting_type="type")
    @app_commands.choices(setting_type=[
        discord.app_commands.Choice(name='Help', value="Help"),
        discord.app_commands.Choice(name='Attribute', value="Attribute"),
        discord.app_commands.Choice(name='Module', value="Module"),
    ])
    @app_commands.autocomplete(setting=_setting_autocomplete)
    @app_commands.autocomplete(mode=_mode_autocomplete)
    @app_commands.autocomplete(value=_value_autocomplete)
    @app_commands.check(is_admin_check)
    async def settings(
            self,
            itx: discord.Interaction,
            setting_type: str,
            setting: str | None = None,
            mode: str | None = None,
            value: str | None = None
    ):
        help_cmd_mention = itx.client.get_command_mention("help")
        help_str = f"Use {help_cmd_mention} `page:900` for more info."
        if setting_type not in ["Help", "Attribute", "Module"]:
            await itx.response.send_message("That is not a valid type. Please use the options provided to you. " +
                                            help_str,
                                            ephemeral=True)
            return

        try:
            ModeAutocomplete(mode)
        except ValueError:
            await itx.response.send_message("This is not a valid mode. " + help_str, ephemeral=True)
            return

        if setting_type == "Help":
            # Todo: Make more functions call HelpPage functions.
            await send_help_menu(itx, requested_page=900)

        if setting_type == "Attribute":
            attribute_keys = list(ServerAttributes.__required_keys__.union(ServerAttributes.__optional_keys__))
            if mode is None:
                await itx.response.send_message("You must set a mode! " + help_str)

            if setting in attribute_keys:
                if mode == ModeAutocomplete.view:
                    # todo: Implement. Needs `itx.client.server_attributes[setting]`
                    pass

                # confirm if expected attribute type also matches the given attribute type
                expected_attribute_type = get_attribute_autocomplete_type(setting)
                parse_attribute(itx.client, setting, value)


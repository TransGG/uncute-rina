from __future__ import annotations
import typing  # for typing.cast and TYPE_CHECKING

import discord
import discord.ext.commands as commands
import discord.app_commands as app_commands

from extensions.settings.objects.server_settings import ParseError
from extensions.watchlist.local_watchlist import import_watchlist_threads
from resources.checks import is_admin_check, not_in_dms_check, module_enabled_check, MissingAttributesCheckFailure

from extensions.help.cogs import send_help_menu
from extensions.settings.objects import (
    ServerSettings, ServerAttributes, ServerAttributeIds, EnabledModules, TypeAutocomplete, ModeAutocomplete,
    parse_attribute, get_attribute_type, ModuleKeys, AttributeKeys
)

if typing.TYPE_CHECKING:
    from resources.customs import Bot


# todo: maybe a function to re-fetch settings for a specific server
#  Like if a channel is deleted, or an emoji is removed. That you don't
#  have to completely restart Rina to re-fetch every setting.

# todo: ensure SystemAttributeIds.parent_server is not in a parent server's parent server
#  The same for checking if one of the child_servers contains self, to prevent cyclic dependencies.


attribute_type_single_value = [ModeAutocomplete.set, ModeAutocomplete.delete]
attribute_type_list = [ModeAutocomplete.add, ModeAutocomplete.remove]


def get_attribute_autocomplete_mode(attribute_key: str) -> list[ModeAutocomplete] | None:
    """
    Retrieve the mode autocomplete-type of a ServerAttributeId key. This is usually either a list or a single value.

    Returns
    -------
    The mode autocomplete-type, or None if the attribute is not a valid key.
    """
    _, in_list = get_attribute_type(attribute_key)
    if in_list:
        return attribute_type_list
    return attribute_type_single_value


@app_commands.check(is_admin_check)
async def _setting_autocomplete(itx: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    itx.namespace.type = typing.cast(str | None, itx.namespace.type)

    if itx.namespace.type == TypeAutocomplete.help.value:
        return [
            app_commands.Choice(name="For a list of attributes/modules, leave `mode` empty.", value="-"),
        ]
    elif itx.namespace.type == TypeAutocomplete.module.value:
        module_keys = EnabledModules.__annotations__
        return [
            app_commands.Choice(name=key, value=key) for key in module_keys
            if current.lower() in key.lower()
        ][:10]
    elif itx.namespace.type == TypeAutocomplete.attribute.value:
        attribute_id_keys = ServerAttributeIds.__annotations__
        return [
            app_commands.Choice(name=key, value=key) for key in attribute_id_keys
            if current.lower() in key.lower()
        ][:10]
    else:
        return []


@app_commands.check(is_admin_check)
async def _mode_autocomplete(itx: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    itx.namespace.type = typing.cast(str | None, itx.namespace.type)
    itx.namespace.setting = typing.cast(str | None, itx.namespace.setting)

    types = [ModeAutocomplete.view]

    if itx.namespace.type == TypeAutocomplete.help.value:
        return [
            app_commands.Choice(name="For a list of attributes/modules, leave `mode` empty.", value="-"),
        ]
    elif itx.namespace.type == TypeAutocomplete.module.value:
        if itx.namespace.setting in EnabledModules.__annotations__:
            types += [ModeAutocomplete.enable, ModeAutocomplete.disable]
            return [
                app_commands.Choice(name=key.value, value=key.value)
                for key in types if current.lower() in key.value.lower()
            ]
        return [app_commands.Choice(name="Invalid setting given.", value=ModeAutocomplete.invalid.value)]
    elif itx.namespace.type == TypeAutocomplete.attribute.value:
        autocomplete_type = get_attribute_autocomplete_mode(itx.namespace.setting)
        if autocomplete_type is None:
            return [app_commands.Choice(name="Invalid setting given.", value=ModeAutocomplete.invalid.value)]
        types += autocomplete_type
        return [
            app_commands.Choice(name=key.value, value=key.value)
            for key in types if current.lower() in key.value.lower()
        ]
    else:
        return []


@app_commands.check(is_admin_check)
async def _value_autocomplete(itx: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    itx.namespace.type = typing.cast(str | None, itx.namespace.type)
    itx.namespace.mode = typing.cast(str | None, itx.namespace.mode)
    itx.namespace.setting = typing.cast(str | None, itx.namespace.setting)
    itx.namespace.value = typing.cast(str | None, itx.namespace.value)

    if itx.namespace.type == TypeAutocomplete.help.value:
        return [
            app_commands.Choice(name="For a list of attributes/modules, leave `mode` empty.", value="-"),
        ]

    elif itx.namespace.type == TypeAutocomplete.attribute.value:
        if itx.namespace.mode == ModeAutocomplete.view.value:
            return [app_commands.Choice(name="This parameter is unnecessary when viewing an attribute.", value="-")]
        elif itx.namespace.mode == ModeAutocomplete.delete.value:
            return [app_commands.Choice(name="This parameter is unnecessary when deleting an attribute.", value="-")]

        attribute_type, _ = get_attribute_type(itx.namespace.setting)
        if attribute_type is None:
            return [app_commands.Choice(name="Invalid setting given.", value="-")]

        results = []
        if issubclass(attribute_type, discord.Guild):
            # iterate all guilds
            for guild in itx.client.guilds:
                if current.lower() in guild.name.lower() or str(guild.id).startswith(current):
                    results.append(app_commands.Choice(name=guild.name, value=str(guild.id)))
        elif issubclass(attribute_type, discord.User):
            # Note: discord.User is a subclass of discord.abc.Messageable, so should be tested before that too.
            # iterate guild members
            for member in itx.guild.members:
                if current.lower() in member.name.lower() or str(member.id).startswith(current):
                    results.append(app_commands.Choice(name=member.name, value=str(member.id)))
                if len(results) > 20:
                    break
            # from user id
            if current.isdecimal():
                potential_user = itx.client.get_user(int(current))
                if potential_user is not None:
                    results.append(app_commands.Choice(name=potential_user.name, value=str(potential_user.id)))
        elif issubclass(attribute_type, discord.abc.GuildChannel):
            for channel in itx.guild.channels:
                if (
                        isinstance(channel, attribute_type) and
                        (current in channel.name or str(channel.id).startswith(current))
                ):
                    results.append(app_commands.Choice(name=channel.name, value=str(channel.id)))
        elif issubclass(attribute_type, discord.abc.Messageable):
            # from channel id
            if current.isdecimal():
                potential_channel = itx.client.get_channel(int(current))
                if potential_channel is not None:
                    results.append(app_commands.Choice(
                        name=potential_channel.name, value=str(potential_channel.id)))
            # iterate messageable guild channels
            for channel in itx.guild.channels:
                if isinstance(channel, attribute_type):
                    if current.lower() in channel.name.lower() or str(channel.id).startswith(current):
                        results.append(app_commands.Choice(name=channel.name, value=str(channel.id)))
        elif issubclass(attribute_type, discord.Role):
            # iterate guild roles
            for role in itx.guild.roles:
                if current.lower() in role.name.lower() or str(role.id).startswith(current):
                    results.append(app_commands.Choice(name=role.name, value=str(role.id)))
        elif issubclass(attribute_type, discord.Emoji):
            # iterate guild emojis
            for emoji in itx.guild.emojis:
                if current.lower() in emoji.name.lower() or str(emoji.id).startswith(current):
                    results.append(app_commands.Choice(name=emoji.name, value=str(emoji.id)))
        elif attribute_type == str:
            # leave as is
            results.append(app_commands.Choice(name=current, value=current))
        elif attribute_type == int:
            # leave as is, if it's a number (otherwise don't suggest anything)
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


async def _handle_settings_attribute(
        itx: discord.Interaction[Bot],
        help_str: str,
        setting: str | None,
        modify_mode: ModeAutocomplete | None,
        value: str | None,
):
    """
    A helper function to handle setting server attributes.
    :param itx: The interaction with which to respond to messages, and itx.client to execute database actions.
    :param help_str: A help string to append to error messages.
    :param setting: The key of the attribute to change.
    :param modify_mode: The mode to use when modifying the attribute.
    :param value: The value to give the attribute or remove from the attribute (depending on the *modify_mode*.
    """
    itx.response: discord.InteractionResponse[Bot]  # noqa
    itx.followup: discord.Webhook  # noqa
    attribute_keys = ServerAttributes.__annotations__

    if setting is None:
        await itx.response.send_message(("Here is a list of attributes you can set:\n" +
                                         ", ".join(attribute_keys) +
                                         "\n" +
                                         help_str)[:2000], ephemeral=True)
        return

    if modify_mode is None:
        await itx.response.send_message("You didn't set a mode!" + help_str, ephemeral=True)
        return

    if setting not in attribute_keys:
        await itx.response.send_message(
            "This is not a valid setting. Please choose one of the autocompleted settings after "
            "setting `type:Attribute`.\n"
            "If you filled in `type:Module` and loaded the earlier autocomplete for that instead "
            "(and the autocomplete cache doesn't let you reload the settings), you can clear your "
            "whole chatbox and re-type the command to reset the autocomplete cache (discord is "
            "silly) (on Desktop at least). Otherwise reopen the app, maybe that works.\n" +
            help_str,
            ephemeral=True
        )
        return

    await itx.response.defer(ephemeral=True)  # defer before any database calls

    if modify_mode == ModeAutocomplete.view:
        entry = await ServerSettings.get_entry(itx.client.async_rina_db, itx.guild.id)
        if entry is None:
            await itx.followup.send(f"This server has no data for '{setting}' yet.", ephemeral=True)
            return
        attribute_raw = entry["attribute_ids"].get(setting, "<no value yet>")  # type: ignore
        attribute_parsed = itx.client.get_guild_attribute(itx.guild, setting)
        await itx.followup.send((f"The current value for '{setting}' is:\n"
                                 f"Raw:\n"
                                 f"- {attribute_raw}\n"
                                 f"Parsed:\n"
                                 f"- {ServerSettings.get_original(attribute_parsed)}"
                                 )[:2000],
                                ephemeral=True)
        return
    elif modify_mode == ModeAutocomplete.delete:
        await ServerSettings.remove_attribute(
            itx.client.async_rina_db, itx.guild.id, setting
        )
    else:
        invalid_arguments = {}
        attribute = parse_attribute(
            itx.client, itx.guild, setting, value, invalid_arguments=invalid_arguments
        )  # todo: check if ParseError handled
        if invalid_arguments and modify_mode not in [ModeAutocomplete.remove, ModeAutocomplete.remove]:
            # allow removal of malformed data
            attribute_type, _ = get_attribute_type(setting)
            await itx.followup.send((f"Could not parse `{value}` as value for "
                                     f"'{setting}' (expected {attribute_type.__name__}.\n"
                                     f"(Notes: {[(k, v) for k, v in invalid_arguments.items()]}")[:1999] + ")",
                                    ephemeral=True)
            return

        if hasattr(attribute, "id"):
            # guild, channel, emoji, role, user
            database_value = attribute.id
        else:
            # int, str
            database_value = attribute

        if setting == AttributeKeys.parent_server:
            # Check if the given server or one of its parents has this server
            #  marked as a parent already.
            assert type(database_value) is int
            has_current_server, parent_server_id = await _has_guild_as_parent(
                itx.client, itx.guild, database_value)
            if has_current_server:
                # parent_server should not be None if has_current_server is True
                await itx.followup.send(
                    f"You can't set this server as parent, since it or "
                    f"one of its parents (guild id `{parent_server_id}`) "
                    f"already has this server as its parent!",
                    ephemeral=True
                )
                return

        if modify_mode == ModeAutocomplete.set:
            await ServerSettings.set_attribute(
                itx.client.async_rina_db, itx.guild.id, setting, database_value
            )
        elif modify_mode == ModeAutocomplete.add:
            result = await ServerSettings.get_entry(itx.client.async_rina_db, itx.guild.id)
            if result is not None:
                items = getattr(result["attribute_ids"], setting, [])  # type: ignore
            else:
                # if guild has no info yet
                items = []

            if database_value in items:
                await itx.followup.send(f"Couldn't add '{database_value}' to the list, because it was "
                                        f"already in it!", ephemeral=True)
                return

            items.append(database_value)
            await ServerSettings.set_attribute(itx.client.async_rina_db, itx.guild.id, setting, items)
        elif modify_mode == ModeAutocomplete.remove:
            result = await ServerSettings.get_entry(itx.client.async_rina_db, itx.guild.id)
            if result is not None:
                items = result["attribute_ids"].get(setting, [])  # type: ignore
            else:
                # if guild has no info yet
                items = []

            if not items:  # empty list
                await itx.followup.send("Couldn't remove any item from the list, because there "
                                        "was nothing in it!", ephemeral=True)
                return

            if database_value not in items:
                if not value.isdecimal() or int(value) not in items:
                    await itx.followup.send(f"Couldn't remove '{database_value}' from the list, because "
                                            f"it wasn't in the list before either!", ephemeral=True)
                    return
                else:
                    database_value = int(value)

            del items[items.index(database_value)]
            await ServerSettings.set_attribute(itx.client.async_rina_db, itx.guild.id, setting, items)
        else:
            # confirm if expected attribute type also matches the given attribute type
            expected_modify_mode = get_attribute_autocomplete_mode(setting)
            assert expected_modify_mode is not None
            # It shouldn't be None because `setting` is already in `attribute_keys` from ServerAttributes, and
            #  the function checks keys of ServerAttributeIds, which should be identical.

            await itx.followup.send(
                f"This attribute cannot be changed with this mode ('{modify_mode.value}')\n"
                f"It must be one of the following: " +
                ', '.join([f"'{m.value}'" for m in expected_modify_mode]),  # [a,b,c] -> "'a', 'b', 'c'"
                ephemeral=True
            )
            return

    try:
        await itx.client.server_settings[itx.guild.id].reload(itx.client)
    except ParseError as ex:
        await itx.followup.send("Successfully set the module state!\n"
                                "Just one tiny problem... Reloading the server settings failed...\n"
                                "You should message Mia about this, or Cleo, to look into the database "
                                "and get more information about the problem:" +
                                ex.message, ephemeral=True)
        return

    await itx.followup.send(f"Successfully modified the value for '{setting}'!", ephemeral=True)


async def _has_guild_as_parent(
        client: Bot, guild: discord.Guild, parent_server_id: int
) -> tuple[bool, int | None]:
    """
    Whether the given parent server has this guild as its parent (recursively).

    Check if any of the parent server id's parent servers is equal to the
    given guild.

    :param client: The client to fetch the parent
    :param guild: The guild to check for recursive parenting.
    :param parent_server_id: The parent guild to link to the given guild.
    :return: A tuple of whether any parent servers has this server as its
     parent already; and the parent server id in question
    """
    has_current_server = False
    while parent_server_id is not None:
        if parent_server_id == guild.id:
            has_current_server = True
            break
        parent_server_id = client.get_guild_attribute(
            parent_server_id, AttributeKeys.parent_server)
    return has_current_server, parent_server_id


async def _handle_settings_module(
        itx: discord.Interaction[Bot],
        help_str: str,
        setting: str | None,
        modify_mode: str | None
):
    """
    A helper function to handle setting server attributes.
    :param itx: The interaction with which to respond to messages, and itx.client to execute database actions.
    :param help_str: A help string to append to error messages.
    :param setting: The key of the attribute to change.
    :param modify_mode: The mode to use when modifying the attribute.
    """
    module_keys = EnabledModules.__annotations__

    if setting is None:
        disabled_modules = set([i for i in module_keys])
        enabled_modules = set()

        if itx.client.server_settings is None:
            await itx.response.send_message("No settings have been loaded yet! Please wait a little bit, or "
                                            "message @mysticmia about this error message.",
                                            ephemeral=True)
            return

        server_setting: ServerSettings | None = itx.client.server_settings.get(itx.guild.id, None)
        if server_setting:
            for module, val in server_setting.enabled_modules.items():
                if val:
                    enabled_modules.add(module)
        disabled_modules = disabled_modules - enabled_modules
        enabled_modules_string = f"### Enabled:\n> {', '.join(enabled_modules)}\n" if enabled_modules else ""
        disabled_modules_string = f"### Disabled:\n> {', '.join(disabled_modules)}\n" if disabled_modules else ""
        await itx.response.send_message(
            ("Here is a list of modules you can set, and their values.\n" +
             enabled_modules_string + disabled_modules_string + help_str)[:2000],
            ephemeral=True
        )
        return

    if modify_mode is None:
        await itx.response.send_message("You didn't set a mode!" + help_str, ephemeral=True)
        return

    if setting not in module_keys:
        await itx.response.send_message(
            "This is not a valid setting. Please choose one of the autocompleted settings after "
            "setting `type:Module`.\n"
            "If you filled in `type:Attribute` and loaded the earlier autocomplete for that instead "
            "(and the autocomplete cache doesn't let you reload the settings), you can clear your "
            "whole chatbox and re-type the command to reset the autocomplete cache (discord is "
            "silly) (on Desktop at least). Otherwise reopen the app, maybe that works.\n" +
            help_str,
            ephemeral=True
        )
        return

    if modify_mode == ModeAutocomplete.view:
        module_enabled = itx.client.is_module_enabled(itx.guild, setting)
        state_str = 'Enabled' if module_enabled else 'Disabled'
        await itx.response.send_message(f"The module '{setting}' is currently '{state_str}'.",
                                        ephemeral=True)
        return
    elif modify_mode == ModeAutocomplete.enable:
        enable = True
    elif modify_mode == ModeAutocomplete.disable:
        enable = False
    else:
        await itx.response.send_message("That is not a valid mode for this setting!"
                                        "When setting the mode for a Module, it must be either"
                                        "'Enable', 'Disable', or 'View'.", ephemeral=True)
        return

    modified, created_new_document = await ServerSettings.set_module_state(
        itx.client.async_rina_db, itx.guild.id, setting, enable)

    if not modified and not created_new_document:
        # If the server's enabled modules already have this value
        await itx.response.send_message("This module is already " +
                                        ("enabled" if enable else "disabled") +
                                        "!\n" + help_str, ephemeral=True)
        return

    await itx.response.defer(ephemeral=True)  # defer before any database calls

    try:
        await itx.client.server_settings[itx.guild.id].reload(itx.client)
    except ParseError as ex:
        await itx.followup.send("Successfully set the module state!\n"
                                "Just one tiny problem... Reloading the server settings failed...\n"
                                "You should message Mia about this, or Cleo, to look into the database "
                                "and get more information about the problem:" +
                                ex.message, ephemeral=True)
        return

    await itx.followup.send("Successfully set the module state!", ephemeral=True)


class SettingsCog(commands.Cog):
    def __init__(self):
        pass

    migrate_group = app_commands.Group(name="migrate",
                                       description="A grouping of migrate commands.")

    @app_commands.check(is_admin_check)
    @migrate_group.command(name="migrate", description="Migrate bot settings to new database.")
    async def migrate(
            self,
            itx: discord.Interaction
    ):
        itx.response: discord.InteractionResponse  # noqa
        await ServerSettings.migrate(itx.client.async_rina_db)
        await itx.response.send_message("Successfully migrated databases.", ephemeral=True)
        itx.client.server_settings = await ServerSettings.fetch_all(itx.client)
        await itx.edit_original_response(content="Migrated databases and re-fetched all server settings.")

    @app_commands.check(is_admin_check)
    @module_enabled_check(ModuleKeys.watchlist)
    @migrate_group.command(name="migrate-watchlist",
                           description="Fetch all watchlist threads for this server.")
    async def migrate_watchlist(self, itx: discord.Interaction[Bot]):
        watchlist_channel: discord.TextChannel | None = itx.client.get_guild_attribute(
            itx.guild, AttributeKeys.watchlist_channel)
        if watchlist_channel is None:
            raise MissingAttributesCheckFailure(AttributeKeys.watchlist_channel)

        await itx.response.defer(ephemeral=True)
        await import_watchlist_threads(itx.client.async_rina_db,
                                       watchlist_channel)
        await itx.followup.send("Successfully imported watchlist threads.",
                                ephemeral=True)

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
    @app_commands.check(not_in_dms_check)
    async def settings(
            self,
            itx: discord.Interaction,
            setting_type: str,
            setting: str | None = None,
            mode: str | None = None,
            value: str | None = None
    ):
        itx.response: discord.InteractionResponse  # noqa
        itx.followup: discord.Webhook  # noqa
        help_cmd_mention = itx.client.get_command_mention("help")
        help_str = f"Use {help_cmd_mention} `page:900` for more info."

        try:
            modify_mode: ModeAutocomplete | None = None
            if mode is not None:
                modify_mode = ModeAutocomplete(mode)
        except ValueError:
            await itx.response.send_message("This is not a valid mode. " + help_str, ephemeral=True)
            return

        if setting_type == TypeAutocomplete.help.value:
            # Todo: Make more functions call HelpPage functions.
            await send_help_menu(itx, requested_page=900)

        elif setting_type == TypeAutocomplete.attribute.value:
            await _handle_settings_attribute(itx, help_str, setting, modify_mode, value)

        elif setting_type == TypeAutocomplete.module.value:
            await _handle_settings_module(itx, help_str, setting, modify_mode)
        else:
            await itx.followup.send("That is not a valid type. Please use the options provided to you. " +
                                    help_str,
                                    ephemeral=True)
            return

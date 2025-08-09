from __future__ import annotations
import typing  # for typing.cast and TYPE_CHECKING

import discord
import discord.ext.commands as commands
import discord.app_commands as app_commands

from resources.checks import (
    is_admin_check,
    module_enabled_check,
    MissingAttributesCheckFailure,
    CommandDoesNotSupportDMsCheckFailure,
)

from extensions.help.cogs import send_help_menu
from extensions.settings.objects.server_settings import ParseError
from extensions.watchlist.local_watchlist import refetch_watchlist_threads
from extensions.settings.objects import (
    ServerSettings, ServerAttributes, ServerAttributeIds, EnabledModules,
    TypeAutocomplete, ModeAutocomplete,
    parse_attribute, get_attribute_type, AttributeKeys, ModuleKeys
)
from resources.customs import GuildInteraction


if typing.TYPE_CHECKING:
    from resources.customs import Bot


attribute_type_single_value = [ModeAutocomplete.set, ModeAutocomplete.delete]
attribute_type_list = [ModeAutocomplete.add, ModeAutocomplete.remove]


def get_attribute_autocomplete_mode(
        attribute_key: str
) -> list[ModeAutocomplete] | None:
    """
    Retrieve the mode autocomplete-type of a ServerAttributeId key.
    This is usually either a list or a single value.

    :return: The mode autocomplete-type, or ``None`` if the attribute
     is not a valid key.
    """
    _, in_list = get_attribute_type(attribute_key)
    if in_list:
        return attribute_type_list
    return attribute_type_single_value


@is_admin_check
async def _setting_autocomplete(
        itx: discord.Interaction[Bot], current: str
) -> list[app_commands.Choice[str]]:
    itx.namespace.type = typing.cast(str | None, itx.namespace.type)  # pyright: ignore [reportAttributeAccessIssue] # noqa

    if itx.namespace.type == TypeAutocomplete.help.value:
        return [
            app_commands.Choice(
                name="For a list of attributes/modules, leave `mode` empty.",
                value="-"
            ),
        ]
    elif itx.namespace.type == TypeAutocomplete.module.value:
        module_keys = EnabledModules.__annotations__
        return [
            app_commands.Choice(name=key, value=key)
            for key in module_keys
            if current.lower() in key.lower()
        ][:10]
    elif itx.namespace.type == TypeAutocomplete.attribute.value:
        attribute_id_keys = ServerAttributeIds.__annotations__
        return [
            app_commands.Choice(name=key, value=key)
            for key in attribute_id_keys
            if current.lower() in key.lower()
        ][:10]
    else:
        return []


@is_admin_check
async def _mode_autocomplete(
        itx: discord.Interaction[Bot], current: str
) -> list[app_commands.Choice[str]]:
    itx.namespace.type = typing.cast(str | None, itx.namespace.type)  # pyright: ignore [reportAttributeAccessIssue] # noqa
    itx.namespace.setting = typing.cast(str | None, itx.namespace.setting)  # pyright: ignore [reportAttributeAccessIssue] # noqa

    types = [ModeAutocomplete.view]

    if itx.namespace.type == TypeAutocomplete.help.value:
        return [
            app_commands.Choice(
                name="For a list of attributes/modules, leave `mode` empty.",
                value="-"
            ),
        ]
    elif itx.namespace.type == TypeAutocomplete.module.value:
        if itx.namespace.setting in EnabledModules.__annotations__:
            types += [ModeAutocomplete.enable, ModeAutocomplete.disable]
            return [
                app_commands.Choice(name=key.value, value=key.value)
                for key in types if current.lower() in key.value.lower()
            ]
        return [app_commands.Choice(name="Invalid setting given.",
                                    value=ModeAutocomplete.invalid.value)]
    elif itx.namespace.type == TypeAutocomplete.attribute.value:
        if itx.namespace.setting is None:
            return [app_commands.Choice(
                name="No setting given. Please give a value for the "
                     "'setting' parameter.",
                value="-")]
        autocomplete_type = get_attribute_autocomplete_mode(
            itx.namespace.setting)
        if autocomplete_type is None:
            return [app_commands.Choice(name="Invalid setting given.",
                                        value=ModeAutocomplete.invalid.value)]
        types += autocomplete_type
        return [
            app_commands.Choice(name=key.value, value=key.value)
            for key in types if current.lower() in key.value.lower()
        ]
    else:
        return []


@is_admin_check
async def _value_autocomplete(
        itx: discord.Interaction[Bot], current: str
) -> list[app_commands.Choice[str]]:
    if itx.guild is None:
        raise CommandDoesNotSupportDMsCheckFailure()
    itx.namespace.type = typing.cast(str | None, itx.namespace.type)  # pyright: ignore [reportAttributeAccessIssue] # noqa
    itx.namespace.mode = typing.cast(str | None, itx.namespace.mode)  # pyright: ignore [reportAttributeAccessIssue] # noqa
    itx.namespace.setting = typing.cast(str | None, itx.namespace.setting)  # pyright: ignore [reportAttributeAccessIssue] # noqa
    itx.namespace.value = typing.cast(str | None, itx.namespace.value)  # pyright: ignore [reportAttributeAccessIssue] # noqa
    if itx.namespace.type == TypeAutocomplete.help.value:
        return [
            app_commands.Choice(
                name="For a list of attributes/modules, leave `mode` empty.",
                value="-"
            ),
        ]

    elif itx.namespace.type == TypeAutocomplete.attribute.value:
        if itx.namespace.mode == ModeAutocomplete.view.value:
            return [app_commands.Choice(
                name="This parameter is unnecessary when viewing "
                     "an attribute.",
                value="-")]
        elif itx.namespace.mode == ModeAutocomplete.delete.value:
            return [app_commands.Choice(
                name="This parameter is unnecessary when deleting "
                     "an attribute.",
                value="-")]

        if itx.namespace.setting is None:
            return [app_commands.Choice(
                name="No setting given. Please give a value for the "
                     "'setting' parameter.",
                value="-")]
        attribute_type, _ = get_attribute_type(itx.namespace.setting)
        if attribute_type is None:
            return [app_commands.Choice(name="Invalid setting given.",
                                        value="-")]

        results: list[app_commands.Choice] = []
        if discord.Guild in attribute_type:
            # iterate all guilds
            for guild in itx.client.guilds:
                if (current.lower() in guild.name.lower()
                        or str(guild.id).startswith(current)):
                    results.append(app_commands.Choice(
                        name=guild.name, value=str(guild.id)))
        if discord.User in attribute_type:
            # Note: discord.User is a subclass of discord.abc.Messageable,
            #  so should be tested before that too.
            # iterate guild members
            for member in itx.guild.members:
                if (current.lower() in member.name.lower()
                        or str(member.id).startswith(current)):
                    results.append(app_commands.Choice(
                        name=member.name, value=str(member.id)))
                if len(results) > 20:
                    break
            # from user id
            if current.isdecimal():
                potential_user = itx.client.get_user(int(current))
                if potential_user is not None:
                    results.append(app_commands.Choice(
                        name=potential_user.name, value=str(potential_user.id))
                    )
        if any(issubclass(channel_type, discord.abc.GuildChannel)
               for channel_type in attribute_type):
            for channel in itx.guild.channels:
                if (type(channel) in attribute_type
                        and (current in channel.name
                             or str(channel.id).startswith(current))):
                    results.append(app_commands.Choice(
                        name=channel.name, value=str(channel.id)))
        if any(issubclass(channel_type, discord.abc.Messageable)
               for channel_type in attribute_type):
            # from channel id
            if current.isdecimal():
                potential_channel = itx.client.get_channel(int(current))
                if (
                        potential_channel is not None
                        and not isinstance(potential_channel,
                                           discord.abc.PrivateChannel)
                ):
                    results.append(app_commands.Choice(
                        name=potential_channel.name,
                        value=str(potential_channel.id))
                    )
            # iterate messageable guild channels
            for channel in itx.guild.channels:
                if type(channel) in attribute_type:
                    if (current.lower() in channel.name.lower()
                            or str(channel.id).startswith(current)):
                        results.append(app_commands.Choice(
                            name=channel.name, value=str(channel.id)))
        if discord.Role in attribute_type:
            # iterate guild roles
            for role in itx.guild.roles:
                if (current.lower() in role.name.lower()
                        or str(role.id).startswith(current)):
                    results.append(app_commands.Choice(
                        name=role.name, value=str(role.id)))
        if discord.Emoji in attribute_type:
            # iterate guild emojis
            for emoji in itx.guild.emojis:
                if (current.lower() in emoji.name.lower()
                        or str(emoji.id).startswith(current)):
                    results.append(app_commands.Choice(
                        name=emoji.name, value=str(emoji.id)))
        if str in attribute_type:
            # leave as is
            results.append(app_commands.Choice(name=current, value=current))
        if str in attribute_type:
            # leave as is, if it's a number (otherwise don't suggest anything)
            if current.isdecimal():
                results.append(app_commands.Choice(
                    name=current, value=current))
        if len(results) == 0:
            attribute_type_names = ','.join(
                i.__name__ for i in attribute_type)
            results.append(
                app_commands.Choice(
                    name=f"No autocompletes for: "
                         f"{attribute_type_names}"[:100],
                    value="-")
            )

        # deduplicate
        unique_results = set()
        for result in results:
            unique_results.add((result.name, result.value))
        results = [app_commands.Choice(name=name, value=val)
                   for name, val in unique_results]

        return results[:10]

    elif itx.namespace.type == TypeAutocomplete.module.value:
        return [
            app_commands.Choice(
                name="This parameter is unnecessary when toggling "
                     "module state",
                value="-"
            ),
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

    :param itx: The interaction with which to respond to messages, and
     itx.client to execute database actions.
    :param help_str: A help string to append to error messages.
    :param setting: The key of the attribute to change.
    :param modify_mode: The mode to use when modifying the attribute.
    :param value: The value to give the attribute or remove from the
     attribute (depending on the *modify_mode*).
    """
    itx.response: discord.InteractionResponse[Bot]  # type: ignore
    itx.followup: discord.Webhook  # type: ignore
    attribute_keys = ServerAttributes.__annotations__

    if setting is None:
        await itx.response.send_message(
            ("Here is a list of attributes you can set:\n"
             + ", ".join(attribute_keys)
             + "\n"
             + help_str)[:2000],
            ephemeral=True
        )
        return

    if modify_mode is None:
        await itx.response.send_message("You didn't set a mode!" + help_str,
                                        ephemeral=True)
        return

    if setting not in attribute_keys:
        await itx.response.send_message(
            "This is not a valid setting. Please choose one of the "
            "autocompleted settings after setting `type:Attribute`.\n"
            "If you filled in `type:Module` and loaded the earlier "
            "autocomplete for that instead (and the autocomplete cache "
            "doesn't let you reload the settings), you can clear your whole "
            "chatbox and re-type the command to reset the autocomplete cache "
            "(discord is silly) (on Desktop at least). Otherwise reopen the "
            "app, maybe that works.\n"
            + help_str,
            ephemeral=True
        )
        return

    await itx.response.defer(ephemeral=True)  # defer before any database calls

    assert itx.guild is not None  # is_admin_check in parent function

    if modify_mode == ModeAutocomplete.view:
        entry = await ServerSettings.get_entry(itx.client.async_rina_db,
                                               itx.guild.id)
        if entry is None:
            await itx.followup.send(
                f"This server has no data for '{setting}' yet.",
                ephemeral=True
            )
            return
        attribute_raw = entry["attribute_ids"].get(
            setting, None)  # type: ignore
        if attribute_raw:
            attribute_raw = repr(attribute_raw)
        else:
            attribute_raw = "<no value yet>"
        attribute_parsed = itx.client.get_guild_attribute(itx.guild, setting)
        await itx.followup.send(
            (f"The current value for '{setting}' is:\n"
             f"Raw:\n"
             f"- {attribute_raw}\n"
             f"Parsed:\n"
             f"- {ServerSettings.get_original(attribute_parsed)}"
             )[:2000],
            ephemeral=True
        )
        return
    elif modify_mode == ModeAutocomplete.delete:
        await ServerSettings.remove_attribute(
            itx.client.async_rina_db, itx.guild.id, setting
        )
    else:
        if value is None:
            await itx.followup.send(
                "No value was given.",
                ephemeral=True
            )
            return

        invalid_arguments = {}
        attribute = parse_attribute(
            itx.client, itx.guild, setting, value,
            invalid_arguments=invalid_arguments
        )
        if attribute is None:
            await itx.followup.send(
                f"Couldn't parse value '{value}' for attribute '{setting}'.",
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        # raises ParseError if the ServerAttribute has a type that
        #  has no parsing function yet.
        if (attribute is None
                or invalid_arguments and modify_mode not in [
                    ModeAutocomplete.remove, ModeAutocomplete.remove
                ]):
            # allow removal of malformed data
            attribute_type, _ = get_attribute_type(setting)
            assert attribute_type is not None
            attribute_type_names = ', '.join(
                i.__name__ for i in attribute_type)
            await itx.followup.send(
                (f"Could not parse `{value}` as value for "
                 f"'{setting}' (expected one of {attribute_type_names}.\n"
                 f"(Notes: {[(k, v) for k, v in invalid_arguments.items()]})"
                 )[:1999]
                + ")",
                ephemeral=True
            )
            return

        # [guild, channel, emoji, role, user] if it has an id
        # else [int, str], for example
        database_value = getattr(attribute, "id", attribute)

        if setting == AttributeKeys.parent_server:
            # Check if the given server or one of its parents has this server
            #  marked as a parent already.
            assert type(database_value) is int
            has_current_server, parent_server_id = await _has_guild_as_parent(
                itx.client, itx.guild, database_value)
            if has_current_server:
                # parent_server should not be None if has_current_server
                #  is True
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
            result = await ServerSettings.get_entry(
                itx.client.async_rina_db, itx.guild.id)
            if result is not None:
                items = result["attribute_ids"].get(setting, [])
            else:
                # if guild has no info yet
                items = []

            if database_value in items:
                await itx.followup.send(
                    f"Couldn't add '{database_value}' to the list, because "
                    f"it was already in it!",
                    ephemeral=True
                )
                return

            items.append(database_value)
            await ServerSettings.set_attribute(
                itx.client.async_rina_db, itx.guild.id, setting, items)
        elif modify_mode == ModeAutocomplete.remove:
            result = await ServerSettings.get_entry(
                itx.client.async_rina_db, itx.guild.id)
            if result is not None:
                items = result["attribute_ids"].get(
                    setting, [])  # type: ignore
            else:
                # if guild has no info yet
                items = []

            if not items:  # empty list
                await itx.followup.send(
                    "Couldn't remove any item from the list, because there "
                    "was nothing in it!",
                    ephemeral=True
                )
                return

            if database_value not in items:
                if not value.isdecimal() or int(value) not in items:
                    await itx.followup.send(
                        f"Couldn't remove '{database_value}' from the "
                        f"list, because it wasn't in the list before either!",
                        ephemeral=True
                    )
                    return
                else:
                    database_value = int(value)

            del items[items.index(database_value)]
            await ServerSettings.set_attribute(
                itx.client.async_rina_db, itx.guild.id, setting, items)
        else:
            # confirm if expected attribute type also matches the given
            #  attribute type
            expected_modify_mode = get_attribute_autocomplete_mode(setting)
            assert expected_modify_mode is not None
            # It shouldn't be None because `setting` is already in
            #  `attribute_keys` from ServerAttributes, and the function
            #  checks keys of ServerAttributeIds, which should be
            #  identical.

            await itx.followup.send(
                f"This attribute cannot be changed with this mode "
                f"('{modify_mode.value}')\n"
                f"It must be one of the following: "
                + ', '.join([f"'{m.value}'" for m in expected_modify_mode]),
                # [enum.a, enum.b, enum.c] -> "'a', 'b', 'c'"
                ephemeral=True,
            )
            return

    try:
        await _reload_or_store_server_settings(itx.client, itx.guild)
    except ParseError as ex:
        await itx.followup.send(
            ("Successfully set the module state!\n"
             "Just one tiny problem... Reloading the server settings "
             "failed...\n"
             "You should message Mia about this, or Cleo, to look into the "
             "database and get more information about the problem:"
             + ex.message
             )[:2000],
            ephemeral=True,
        )
        return

    await itx.followup.send(
        f"Successfully modified the value for '{setting}'!",
        ephemeral=True,
    )


async def _reload_or_store_server_settings(
        client: Bot, guild: discord.Guild
) -> None:
    """
    Reload a guild's server settings object, or create a new one if
    none exists yet.

    :param client: The client with the server settings.
    :param guild: The guild you want to refresh or add server
     settings to.
    """
    if client.server_settings is None:
        raise ParseError("No server settings have been loaded yet!")
    if guild.id in client.server_settings:
        await client.server_settings[guild.id].reload(client)
    else:
        client.server_settings[guild.id] = \
            await ServerSettings.fetch(client, guild.id)


async def _has_guild_as_parent(
        client: Bot, guild: discord.Guild, parent_server_id: int
) -> tuple[bool, int | None]:
    """
    Whether the given parent server has this guild as its
    parent (recursively).

    Check if any of the parent server id's parent servers is equal to the
    given guild.

    :param client: The client to fetch the parent
    :param guild: The guild to check for recursive parenting.
    :param parent_server_id: The parent guild to link to the
     given guild.
    :return: A tuple of whether any parent servers has this server as
     its parent already; and the parent server id in question.
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
        itx: GuildInteraction[Bot],
        help_str: str,
        setting: str | None,
        modify_mode: ModeAutocomplete | None
):
    """
    A helper function to handle setting server attributes.
    :param itx: The interaction with which to respond to messages, and
     itx.client to execute database actions.
    :param help_str: A help string to append to error messages.
    :param setting: The key of the attribute to change.
    :param modify_mode: The mode to use when modifying the attribute.
    """
    module_keys = EnabledModules.__annotations__

    if setting is None:
        disabled_modules = set([i for i in module_keys])
        enabled_modules = set()

        if itx.client.server_settings is None:
            await itx.response.send_message(
                "No settings have been loaded yet! Please wait a little bit, "
                "or message @mysticmia about this error message.",
                ephemeral=True,
            )
            return

        server_setting: ServerSettings | None = \
            itx.client.server_settings.get(itx.guild.id, None)
        if server_setting:
            for module, val in server_setting.enabled_modules.items():
                if val:
                    enabled_modules.add(module)
        disabled_modules -= enabled_modules
        enabled_modules_string = ((f"### Enabled:\n> "
                                   f"{', '.join(enabled_modules)}\n")
                                  if enabled_modules else "")
        disabled_modules_string = (f"### Disabled:\n> "
                                   f"{', '.join(disabled_modules)}\n"
                                   if disabled_modules else "")
        await itx.response.send_message(
            ("Here is a list of modules you can set, and their values.\n"
             + enabled_modules_string + disabled_modules_string + help_str
             )[:2000],
            ephemeral=True,
        )
        return

    if modify_mode is None:
        await itx.response.send_message("You didn't set a mode!" + help_str,
                                        ephemeral=True)
        return

    if setting not in module_keys:
        await itx.response.send_message(
            "This is not a valid setting. Please choose one of the "
            "autocompleted settings after setting `type:Module`.\n"
            "If you filled in `type:Attribute` and loaded the earlier "
            "autocomplete for that instead (and the autocomplete cache "
            "doesn't let you reload the settings), you can clear your "
            "whole chatbox and re-type the command to reset the "
            "autocomplete cache (discord is silly) (on Desktop at least). "
            "Otherwise reopen the app, maybe that works.\n"
            + help_str,
            ephemeral=True,
        )
        return

    if modify_mode == ModeAutocomplete.view:
        module_enabled = itx.client.is_module_enabled(itx.guild, setting)
        state_str = 'Enabled' if module_enabled else 'Disabled'
        await itx.response.send_message(
            f"The module '{setting}' is currently '{state_str}'.",
            ephemeral=True,
        )
        return
    elif modify_mode == ModeAutocomplete.enable:
        enable = True
    elif modify_mode == ModeAutocomplete.disable:
        enable = False
    else:
        await itx.response.send_message(
            "That is not a valid mode for this setting!"
            "When setting the mode for a Module, it must be either"
            "'Enable', 'Disable', or 'View'.",
            ephemeral=True,
        )
        return

    modified, created_new_document = await ServerSettings.set_module_state(
        itx.client.async_rina_db, itx.guild.id, setting, enable)

    if not modified and not created_new_document:
        # If the server's enabled modules already have this value
        await itx.response.send_message(
            "This module is already "
            + ("enabled" if enable else "disabled")
            + "!\n" + help_str,
            ephemeral=True,
        )
        return

    await itx.response.defer(ephemeral=True)  # defer before any database calls

    try:
        await _reload_or_store_server_settings(itx.client, itx.guild)
    except ParseError as ex:
        await itx.followup.send(
            ("Successfully set the module state!\n"
             "Just one tiny problem... Reloading the server settings "
             "failed...\n"
             "You should message Mia about this, or Cleo, to look into "
             "the database and get more information about the problem:"
             + ex.message
             )[:2000],
            ephemeral=True,
        )
        return

    await itx.followup.send("Successfully set the module state!",
                            ephemeral=True)


class SettingsCog(commands.Cog):
    def __init__(self):
        pass

    migrate_group = app_commands.Group(
        name="migrate",
        description="A grouping of migrate commands.",
    )
    #
    # @app_commands.check(is_admin_check)
    # @migrate_group.command(
    #     name="database",
    #     description="Migrate bot settings to new database."
    # )
    # async def database(
    #         self,
    #         itx: discord.Interaction[Bot]
    # ):
    #     itx.response: discord.InteractionResponse[Bot]  # type: ignore
    #     await ServerSettings.migrate(itx.client.async_rina_db)
    #     await itx.response.send_message(
    #         "Successfully migrated databases.", ephemeral=True)
    #     itx.client.server_settings = await ServerSettings.fetch_all(
    #         itx.client)
    #     await itx.edit_original_response(
    #         content="Migrated databases and re-fetched all server settings.")
    #

    @migrate_group.command(
        name="migrate-watchlist",
        description="Fetch all watchlist threads for this server."
    )
    @is_admin_check
    @module_enabled_check(ModuleKeys.watchlist)
    async def migrate_watchlist(self, itx: GuildInteraction[Bot]):
        watchlist_channel: discord.TextChannel | None = \
            itx.client.get_guild_attribute(
                itx.guild, AttributeKeys.watchlist_channel)
        if watchlist_channel is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.watchlist,
                [AttributeKeys.watchlist_channel]
            )

        await itx.response.defer(ephemeral=True)
        await refetch_watchlist_threads(itx.client.async_rina_db,
                                        itx.guild,
                                        watchlist_channel)
        await itx.followup.send("Successfully imported watchlist threads.",
                                ephemeral=True)
    #
    # @app_commands.check(is_admin_check)
    # @module_enabled_check(ModuleKeys.starboard)
    # @migrate_group.command(
    #     name="migrate-starboard",
    #     description="Fetch all starboard messages for this server."
    # )
    # async def migrate_starboard(self, itx: discord.Interaction[Bot]):
    #     starboard_channel: discord.abc.Messageable | None = \
    #         itx.client.get_guild_attribute(
    #             itx.guild, AttributeKeys.starboard_channel)
    #     if starboard_channel is None:
    #         raise MissingAttributesCheckFailure(
    #             AttributeKeys.starboard_channel)
    #
    #     await itx.response.defer(ephemeral=True)
    #     await import_starboard_messages(itx.client, itx.client.async_rina_db,
    #                                     starboard_channel)
    #     await itx.followup.send("Successfully imported starboard messages.",
    #                             ephemeral=True)

    @app_commands.command(name="settings",
                          description="Edit bot settings for this server.")
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
    @is_admin_check
    async def settings(
            self,
            itx: GuildInteraction[Bot],
            setting_type: str,
            setting: str | None = None,
            mode: str | None = None,
            value: str | None = None
    ):
        itx.response: discord.InteractionResponse[Bot]  # type: ignore
        itx.followup: discord.Webhook  # type: ignore
        cmd_help = itx.client.get_command_mention_with_args(
            "help", page="900")
        help_str = f"Use {cmd_help} for more info."

        try:
            modify_mode: ModeAutocomplete | None = None
            if mode is not None:
                modify_mode = ModeAutocomplete(mode)
        except ValueError:
            await itx.response.send_message("This is not a valid mode. "
                                            + help_str, ephemeral=True)
            return

        if setting_type == TypeAutocomplete.help.value:
            await send_help_menu(itx, requested_page=900)

        elif setting_type == TypeAutocomplete.attribute.value:
            await _handle_settings_attribute(
                itx, help_str, setting, modify_mode, value)

        elif setting_type == TypeAutocomplete.module.value:
            await _handle_settings_module(itx, help_str, setting, modify_mode)
        else:
            await itx.followup.send(
                "That is not a valid type. Please use the options "
                "provided to you. "
                + help_str,
                ephemeral=True
            )
            return

from datetime import datetime, timedelta, timezone
import traceback  # for crash logging
import sys  # to stop the program (and automatically restart, thanks to pterodactyl)

import discord
from discord.ext import commands

from extensions.settings.objects import AttributeKeys
from resources.customs import Bot
from resources.checks import (
    InsufficientPermissionsCheckFailure,
    CommandDoesNotSupportDMsCheckFailure,
    ModuleNotEnabledCheckFailure, MissingAttributesCheckFailure
)
from resources.utils import is_admin, log_to_guild, debug


appcommanderror_cooldown: datetime = datetime.fromtimestamp(0, timezone.utc)
commanderror_cooldown: datetime = datetime.fromtimestamp(0, timezone.utc)


async def _send_crash_message(
        client: Bot,
        error_type: str,
        traceback_text: str,
        error_source: str,
        color: discord.Colour,
        itx: discord.Interaction | None = None
) -> None:
    """
    Sends crash message to Rina's main logging channel

    :param client: The client to fetch logging channel and send the crash message with.
    :param error_type: Whether the error an 'Error' or an 'AppCommand Error'
    :param traceback_text: The traceback to send.
    :param error_source: Name of the error source, displayed at the top of the message. Think of event or command.
    :param color: Color of the discord embed.
    :param itx: Interaction with a potential guild. This might allow Rina to send the crash log to that guild instead.
    """
    log_channel = None
    if hasattr(itx, "guild"):
        log_channel = client.get_guild_attribute(
            itx.guild, AttributeKeys.log_channel)

    if client.server_settings is None and log_channel is None:
        debug(f"Error during startup\n\n\n[{error_type}]: {error_source}\n\n"
              f"{traceback_text}\n\n")
        return

    if log_channel is None:
        # no guild settings, or itx -> 'NoneType' has no attribute '.guild'
        backup_guild_ids = [959551566388547676, 985931648094834798,
                            981615050664075404]
        possible_log_channels = [
            client.get_guild_attribute(guild_id, AttributeKeys.log_channel)
            for guild_id in backup_guild_ids
        ]
        # grab the first non-None logging channel
        for channel in possible_log_channels:
            if channel is None:
                continue
            log_channel = channel
            break

    if log_channel is None:
        # prevent infinite logging loops
        return

    error_caps = error_type.upper()
    debug_message = (f"\n\n\n\n[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')}]"
                     f"[{error_caps}]: {error_source}"
                     f"\n\n{traceback_text}\n")
    debug(f"{debug_message}", add_time=False)

    # prevent the code block from being escaped by other inner tick marks
    msg = debug_message.replace("``",
                                "`` ")
    embeds = []
    while len(msg) > 0 and len(embeds) < 10:
        # 4090 = 4096 (max description length of embeds) - len(2 * "```")
        embed = discord.Embed(
            title=error_type + ' Log',
            description="```" + msg[:4090] + "```",
            color=color,
        )
        embeds.append(embed)
        msg = msg[4090:]

    await log_channel.send(
        f"{client.bot_owner.mention}", embeds=embeds,
        allowed_mentions=discord.AllowedMentions(users=[client.bot_owner])
    )


async def _reply(itx: discord.Interaction, message: str) -> None:
    """
    A helper function to handle replying to an interaction by either using :py:func:`~discord.Webhook.send` or
    :py:func:`~discord.InteractionResponse.send_message`, depending on if a response has been responded to already.

    :param itx: The interaction to respond to.
    :param message: The message to respond with.

    .. note::

        The function will always try to respond to the interaction ephemerally.
    """
    itx.response: discord.InteractionResponse  # noqa
    itx.followup: discord.Webhook  # noqa
    try:
        if itx.response.is_done():
            await itx.followup.send(message, ephemeral=True)
        else:
            try:
                await itx.response.send_message(message, ephemeral=True)
            except discord.errors.NotFound:  # interaction not found, e.g. took too long
                await itx.followup.send(message, ephemeral=True)
    except discord.errors.NotFound:
        pass  # prevent other code from not running


class CrashHandling(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        client.on_error = self.on_error
        client.tree.on_error = self.on_app_command_error

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        # kill switch, see cmd_addons for other on_message events. (and a few other extensions)
        if message.author.id == self.client.bot_owner.id:
            cool_keys = [
                ":restart",
                ":sudo restart",
                ":sudo reboot",
                ":sudo shutdown",
            ]
            if message.content == ":kill now please stop" or any(
                    [message.content.startswith(item) for item in cool_keys]):
                await message.add_reaction("🔄")
                sys.exit(0)
                # quitting the program also
        # this will only run if it hasn't already quit, of course
        if message.content.startswith(":sudo "):
            await message.reply(
                "Cleo.CommandManager.InsufficientPermissionError: Could not run command: No permission\n"
                "Tryin to be part of the cool kids? Try reading this:\n"
                "1 4M 4 V3RY C001 K16!")
            await message.add_reaction("⚠")
        elif message.content.lower().startswith("i am a very cool kid"):
            await message.channel.send("Yes. Yes you are.")

    async def on_error(self, event: str, *_args, **_kwargs):
        global commanderror_cooldown
        if datetime.now().astimezone() - commanderror_cooldown < timedelta(seconds=10):
            # prevent extra log (prevent excessive spam and saving myself some large mentioning chain) if
            # within 10 seconds
            return

        potential_guild: discord.Guild | int | None = None
        for arg in [*_args, *(_kwargs.values())]:
            if hasattr(arg, "guild") and arg.guild is not None:
                # on_message has `Message` with `guild.id` (but no guild_id)
                potential_guild = arg.guild
                break
            if hasattr(arg, "guild_id") and arg.guild_id is not None:
                # RawReaction events have guild_id (but no guild.id)
                potential_guild = arg.guild_id
                break

        exception_and_message = traceback.format_exc(limit=0)
        exception_name = exception_and_message.split(":", 2)[0]
        exception_name = exception_name.split(".")[-1]  # a.b.Error -> Error
        if exception_name == MissingAttributesCheckFailure.__name__:
            if self.client.server_settings is None:
                # Don't send crash message. It's obvious attributes are missing
                #  because no attributes have been loaded yet.
                return

            commanderror_cooldown = datetime.now().astimezone()
            exception_message = exception_and_message.split(": ", 2)[1]
            # format_exc ends with a newline.
            exception_message = exception_message.strip()
            # exception is formatted using Exception.str(), which I overwrote:
            #  ExceptionName: module_name; attribute1, attribute2, attribute3
            module_source, missing_attributes = exception_message.split("; ", 2)
            missing_attributes = missing_attributes.split(", ")
            cmd_mention = self.client.get_command_mention("settings")
            await log_to_guild(
                self.client,
                potential_guild,
                f"Module `{module_source}` ran into an error! This is likely "
                f"because the module was enabled, but did not have the "
                f"required attributes configured to execute its features.\n"
                f"Use {cmd_mention} `type:Attribute` `setting: ` to set "
                f"these missing attributes:\n"
                f"> " + ", ".join(missing_attributes)
            )
            return

        msg = traceback.format_exc()
        commanderror_cooldown = datetime.now().astimezone()
        if potential_guild is None:
            event = "unknown guild: " + event
        else:
            event = f"guild: {potential_guild.id}, " + event

        await _send_crash_message(self.client, "Error", msg, event, discord.Colour.from_rgb(r=255, g=77, b=77))

    @staticmethod
    async def on_app_command_error(itx: discord.Interaction[Bot], error: discord.app_commands.AppCommandError):
        global appcommanderror_cooldown

        error_type = type(error)
        if error_type is InsufficientPermissionsCheckFailure:
            await itx.response.send_message("You do not have the permissions to run this command!",
                                            ephemeral=True)
            return
        elif error_type is CommandDoesNotSupportDMsCheckFailure:
            await itx.response.send_message("This command does not work in DMs. Please run this in a server instead.",
                                            ephemeral=True)
            return
        elif error_type is ModuleNotEnabledCheckFailure:
            error: ModuleNotEnabledCheckFailure
            if is_admin(itx, itx.user):
                cmd_mention = itx.client.get_command_mention("settings")
                cmd_mention_help = itx.client.get_command_mention("help")
                await itx.response.send_message(
                    f"This module is not enabled! Enable it using the following command:\n"
                    f"- {cmd_mention} `type:Module` `setting:{error.module_key}` `mode:Enable`\n"
                    f"Make sure you also set the required attributes for this module. The required "
                    f"attributes for modules and commands are explained in {cmd_mention_help}.",
                    ephemeral=True)
            await itx.response.send_message("This module is not enabled! Ask an admin to enable this module, "
                                            "or have them hide this command from users in the server settings.",
                                            ephemeral=True)
            return
        elif error_type is MissingAttributesCheckFailure:
            error: MissingAttributesCheckFailure
            cmd_mention = itx.client.get_command_mention("settings")
            await _reply(itx, f"Your command failed to completely execute because it relied on certain "
                              f"server attributes that were not defined! An admin will have to run "
                              f"{cmd_mention} `type:Attribute` `setting: ` for the following attribute(s):\n"
                              f"> " + ', '.join(error.attributes))
            return

        if datetime.now().astimezone() - appcommanderror_cooldown < timedelta(seconds=60):
            # prevent extra log (prevent excessive spam and saving myself some large mentioning chain) if
            # within 1 minute
            await _reply(
                itx,
                ("Your command ran into an error, but another crash "
                 "was caused within 60 seconds ago, so the error has not been "
                 "forwarded to the bot developer. If you didn't trigger a "
                 "crash in the past 60 seconds, you may want to re-run the "
                 "command in a little bit and see if you get a different "
                 "error message. Feel free to message @mysticmia with more "
                 "details.\n"
                 "Error: " + repr(error))[:2000]
            )
            return

        cmd_mention = itx.client.get_command_mention("update")
        if isinstance(error, discord.app_commands.errors.CommandNotFound):
            await _reply(itx, f"This command doesn't exist! Perhaps the commands are unsynced. Ask "
                              f"{itx.client.bot_owner} ({itx.client.bot_owner.mention}) if she typed {cmd_mention}!")
        elif isinstance(error, discord.app_commands.errors.CommandSignatureMismatch):
            await _reply(itx, f"Error: CommandSignatureMismatch. Either Mia used GroupCog instead of Cog, "
                              f"or this command is out of date (try {cmd_mention})")
        else:
            if hasattr(error, 'original'):
                error_reply = "Error"
                if hasattr(error.original, 'status'):
                    error_reply += " " + str(error.original.status)
                    # if error.original.status == "403":
                    #     await _reply(itx, "Error 403: It seems like I didn't have permissions for this action! "
                    #                       f"If you believe this is an error, please message or "
                    #                       f"ping {client.bot_owner}} :)")
                if hasattr(error.original, 'code'):
                    error_reply += " (" + str(error.original.code) + ")"
                await _reply(
                    itx,
                    error_reply
                    + f". Please report the error and details to "
                      f"{itx.client.bot_owner} ({itx.client.bot_owner.mention}) "
                      f"by pinging her or sending her a DM. (Though she "
                      f"should have received a message with error details "
                      f"herself as well."
                )
            else:
                await _reply(itx, "Something went wrong executing your command!\n    " + repr(error)[:1700])

        try:
            msg = f"    Executor details: {itx.user} ({itx.user.id})\n"
        except Exception as ex:
            msg = f"    Executor details: couldn't get interaction details: {repr(ex)}\n"
            #   f"    command: {error.command}\n" + \
            #   f"    arguments: {error.args}\n"
        if hasattr(error, 'original'):
            if hasattr(error.original, 'code'):
                msg += f"    code: {error.original.code}\n"
            if hasattr(error.original, 'status'):
                msg += f"    original error: {error.original.status}: {error.original.text}\n\n"
                #    f"   error response:     {error.original.response}\n\n"
        msg += traceback.format_exc()
        # details: /help `page:1` `param2:hey`
        command_details = f"</{itx.command.name}:{itx.data.get('id')}> " + ' '.join(
            [f"`{k}:{v}`" for k, v in itx.namespace.__dict__.items()])
        await _send_crash_message(itx.client, "AppCommand Error", msg, command_details,
                                  discord.Colour.from_rgb(r=255, g=121, b=77), itx=itx)
        appcommanderror_cooldown = datetime.now().astimezone()

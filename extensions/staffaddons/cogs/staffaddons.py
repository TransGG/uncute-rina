from datetime import datetime, timedelta
# ^ for /delete_week_selfies (within 7 days), and /version startup time parsing to discord unix <t:1234:F>
import requests  # to fetch from GitHub and see Rina is running the latest version

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.settings.objects import ModuleKeys, AttributeKeys
from resources.customs import Bot
from resources.checks.permissions import is_staff  # to check if messages in the selfies channel were sent by staff
from resources.checks import is_staff_check, module_enabled_check, MissingAttributesCheckFailure
from resources.utils.utils import log_to_guild  # logging when a staff command is used


class StaffAddons(commands.Cog):
    def __init__(self):
        pass

    @app_commands.check(is_staff_check)
    @app_commands.command(name="say", description="Force Rina to repeat your wise words")
    @app_commands.describe(text="What will you make Rina repeat?",
                           reply_to_interaction="Show who sent the message?")
    async def say(self, itx: discord.Interaction, text: str, reply_to_interaction: bool = False):
        if reply_to_interaction:
            await itx.response.send_message(text, ephemeral=False, allowed_mentions=discord.AllowedMentions.none())
            return

        await log_to_guild(
            itx.client,
            itx.guild,
            f"{itx.user.nick or itx.user.name} ({itx.user.id}) said a message using Rina: {text}",
            crash_if_not_found=True,
            ignore_dms=True
        )
        try:
            text = text.replace("[[\\n]]", "\n").replace("[[del]]", "")
            await itx.channel.send(f"{text}",
                                   allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=True,
                                                                            replied_user=True))
        except discord.Forbidden:
            await itx.response.send_message(
                "Forbidden: I'm not allowed to send a message in this channel.",
                ephemeral=True)
            return
        # No longer necessary: this gets caught by the on_app_command_error() event in the main file.
        await itx.response.send_message("Successfully sent!", ephemeral=True)

    @app_commands.check(is_staff_check)
    @module_enabled_check(ModuleKeys.selfies_channel_deletion)
    @app_commands.command(name="delete_week_selfies", description="Remove selfies and messages older than 7 days")
    async def delete_week_selfies(self, itx: discord.Interaction[Bot]):
        # This function largely copies the built-in channel.purge() function with a check, but is more fancy by
        # offering a sort of progress update every 50-100 messages :D
        # todo attribute: add selfies channel(s)
        selfies_channel = itx.client.get_guild_attribute(
            itx.guild, AttributeKeys.selfies_channel)
        if selfies_channel is None:
            raise MissingAttributesCheckFailure(AttributeKeys.selfies_channel)

        time_now = int(datetime.now().timestamp())  # get time in unix

        output = "Attempting deletion...\n"

        await itx.response.send_message(output + "...", ephemeral=True)

        await log_to_guild(itx.client, itx.guild,
                           f"{itx.user} ({itx.user.id}) deleted messages older than 7 days, in "
                           f"{itx.channel.mention} ({itx.channel.id}).")
        message_delete_count: int = 0
        queued_message_deletions: list[discord.Message] = []
        # current ephemeral message's count content (status of deleting messages)
        feedback_output_count_status: int = 0
        async for message in itx.channel.history(limit=None,
                                                 before=(datetime.now().astimezone() -
                                                         timedelta(days=6, hours=23, minutes=30)),
                                                 oldest_first=True):
            message_date = int(message.created_at.timestamp())
            if "[info]" in message.content.lower() and is_staff(itx, message.author):
                continue
            if time_now - message_date > 14 * 86400:
                # 14 days, too old to remove by bulk
                message_delete_count += 1
                await message.delete()
            elif time_now - message_date > 7 * 86400:
                # 7 days ; technically redundant due to loop's "before" kwarg, but better safe than sorry
                queued_message_deletions.append(message)
                if message_delete_count - feedback_output_count_status >= 50:
                    feedback_output_count_status = message_delete_count - message_delete_count % 10  # round to 10s
                    try:
                        await itx.edit_original_response(
                            content=output + f"\nRemoved {message_delete_count} messages older than 7 days "
                                             f"in {itx.channel.mention} so far...")
                    except discord.errors.HTTPException:
                        pass  # ephemeral message timed out or something..

            if len(queued_message_deletions) >= 100:
                # can only bulk delete up to 100 msgs
                message_delete_count += len(queued_message_deletions[:100])
                await itx.channel.delete_messages(queued_message_deletions[:100],
                                                  reason="Delete selfies older than 7 days")
                queued_message_deletions = queued_message_deletions[100:]

        if queued_message_deletions:
            message_delete_count += len(queued_message_deletions)  # count remaining messages
            await itx.channel.delete_messages(queued_message_deletions,
                                              reason="Delete selfies older than 7 days")  # delete last few messages

        try:
            await itx.channel.send(f"Removed {message_delete_count} messages older than 7 days!")
        except discord.Forbidden:
            await itx.followup.send(f"Removed {message_delete_count} messages older than 7 days!", ephemeral=False)

    @app_commands.command(name="version", description="Get bot version")
    async def get_bot_version(self, itx: discord.Interaction):
        # get most recently pushed bot version
        latest_rina = requests.get("https://raw.githubusercontent.com/TransPlace-Devs/uncute-rina/main/main.py").text
        latest_version = latest_rina.split("BOT_VERSION = \"", 1)[1].split("\"", 1)[0]
        unix = int(itx.client.startup_time.timetuple())
        for i in range(len(latest_version.split("."))):
            if int(latest_version.split(".")[i]) > int(itx.client.version.split(".")[i]):
                await itx.response.send_message(
                    f"Bot is currently running on v{itx.client.version} (latest: v{latest_version})\n"
                    f"(started <t:{unix}:D> at <t:{unix}:T>)",
                    ephemeral=False)
                return
        else:
            await itx.response.send_message(
                f"Bot is currently running on v{itx.client.version} (latest)\n(started <t:{unix}:D> at <t:{unix}:T>)",
                ephemeral=False)

    @app_commands.check(is_staff_check)
    @app_commands.command(name="update", description="Update slash-commands")
    async def update_command_tree(self, itx: discord.Interaction):
        await itx.client.tree.sync()
        itx.client.commandList = await itx.client.tree.fetch_commands()
        await itx.response.send_message("Updated commands")

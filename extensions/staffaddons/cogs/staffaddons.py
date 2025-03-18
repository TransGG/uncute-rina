from datetime import datetime, timedelta
# ^ for /delete_week_selfies (within 7 days), and /version startup time parsing to discord unix <t:1234:F>
import requests  # to fetch from GitHub and see Rina is running the latest version

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from resources.customs.bot import Bot
from resources.utils.permissions import is_staff  # for checking staff roles
from resources.utils.utils import log_to_guild  # logging when a staff command is used


class StaffAddons(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @app_commands.command(name="say", description="Force Rina to repeat your wise words")
    @app_commands.describe(text="What will you make Rina repeat?",
                           reply_to_interaction="Show who sent the message?")
    async def say(self, itx: discord.Interaction, text: str, reply_to_interaction: bool = False):
        if not is_staff(itx.guild, itx.user):
            await itx.response.send_message(
                "Hi. sorry.. It would be too powerful to let you very cool person use this command.",
                ephemeral=True
            )
            return
        if reply_to_interaction:
            await itx.response.send_message(text, ephemeral=False, allowed_mentions=discord.AllowedMentions.none())
            return
        cmd_mention = self.client.get_command_mention("editguildinfo")
        await self.client.get_guild_info(itx.guild, "vcLog", log=[
            itx,
            "Couldn't send your message. You can't send messages in this server because "
            "the bot setup seems incomplete\n"
            f"Use {cmd_mention} `mode:11` to fix this!"])
        try:
            # vcLog      = guild["vcLog"]
            await log_to_guild(self.client, itx.guild,
                               f"{itx.user.nick or itx.user.name} ({itx.user.id}) said a message using Rina: {text}")
            text = text.replace("[[\\n]]", "\n").replace("[[del]]", "")
            await itx.channel.send(f"{text}",
                                   allowed_mentions=discord.AllowedMentions(everyone=False, users=True, roles=True,
                                                                            replied_user=True))
        except discord.Forbidden:
            await itx.response.send_message(
                "Forbidden! I can't send a message in this channel/thread because I "
                "can't see it or because I'm not added to it yet!\n"
                "(Add me to the thread by mentioning me, or let Rina see this channel)",
                ephemeral=True)
            return
        except:
            await itx.response.send_message("Oops. Something went wrong!", ephemeral=True)
            raise
        # No longer necessary: this gets caught by the on_app_command_error() event in the main file.
        await itx.response.send_message("Successfully sent!", ephemeral=True)

    @app_commands.command(name="delete_week_selfies", description="Remove selfies and messages older than 7 days")
    async def delete_week_selfies(self, itx: discord.Interaction):
        # This function largely copies the built-in channel.purge() function with a check, but is more fancy by
        # offering a sort of progress update every 50-100 messages :D
        if not is_staff(itx.guild, itx.user):
            await itx.response.send_message("You don't have permissions to use this command. (for ratelimit reasons)",
                                            ephemeral=True)
            return
        time_now = int(datetime.now().timestamp())  # get time in unix
        if 'selfies' != itx.channel.name or not isinstance(itx.channel, discord.channel.TextChannel):
            await itx.response.send_message("You need to send this in a text channel named \"selfies\"", ephemeral=True)
            return

        output = "Attempting deletion...\n"

        await itx.response.send_message(output + "...", ephemeral=True)
        try:
            await log_to_guild(self.client, itx.guild,
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
                if "[info]" in message.content.lower() and is_staff(message.guild, message.author):
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
        except:
            await itx.followup.send("Something went wrong!", ephemeral=True)
            raise

    @app_commands.command(name="version", description="Get bot version")
    async def get_bot_version(self, itx: discord.Interaction):
        public = is_staff(itx.guild, itx.user)
        # get most recently pushed bot version
        latest_rina = requests.get("https://raw.githubusercontent.com/TransPlace-Devs/uncute-rina/main/main.py").text
        latest_version = latest_rina.split("BOT_VERSION = \"", 1)[1].split("\"", 1)[0]
        unix = int(self.client.startup_time.timetuple())
        for i in range(len(latest_version.split("."))):
            if int(latest_version.split(".")[i]) > int(self.client.version.split(".")[i]):
                await itx.response.send_message(
                    f"Bot is currently running on v{self.client.version} (latest: v{latest_version})\n"
                    f"(started <t:{unix}:D> at <t:{unix}:T>)",
                    ephemeral=not public)
                return
        else:
            await itx.response.send_message(
                f"Bot is currently running on v{self.client.version} (latest)\n(started <t:{unix}:D> at <t:{unix}:T>)",
                ephemeral=not public)

    @app_commands.command(name="update", description="Update slash-commands")
    async def update_command_tree(self, itx: discord.Interaction):
        if not is_staff(itx.guild, itx.user):
            await itx.response.send_message("Only Staff can update the slash commands (to prevent ratelimiting)",
                                            ephemeral=True)
            return
        await self.client.tree.sync()
        self.client.commandList = await self.client.tree.fetch_commands()
        await itx.response.send_message("Updated commands")

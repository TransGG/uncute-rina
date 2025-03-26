from datetime import datetime

import discord
import discord.ext.commands as commands
import discord.app_commands as app_commands

from resources.customs.bot import Bot
from resources.utils.permissions import is_staff  # for dev request thread ping


emoji_color_options = {
    "🔴": discord.Colour.from_rgb(r=255, g=100, b=100),
    "🟡": discord.Colour.from_rgb(r=255, g=255, b=172),
    "🟢": discord.Colour.from_rgb(r=100, g=255, b=100),
    "🔵": discord.Colour.from_rgb(r=172, g=172, b=255)
}


class DevRequest(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @app_commands.command(name="developer_request", description="Suggest a bot idea to the TransPlace developers!")
    @app_commands.describe(suggestion="What idea would you like to share?")
    async def developer_request(self, itx: discord.Interaction, suggestion: app_commands.Range[str, 25, 1500]):
        if len(suggestion) > 1500:
            await itx.response.send_message("Your suggestion won't fit! Please make your suggestion shorter. "
                                            "If you have a special request, you could make a ticket too "
                                            "(in #contact-staff)",
                                            ephemeral=True)
            return
        await itx.response.defer(ephemeral=True)
        try:
            # get channel of where this message has to be sent
            watchlist_channel = itx.client.get_channel(itx.client.custom_ids["staff_dev_request"])
            # make uncool embed for the loading period while it sends the copyable version
            embed = discord.Embed(
                color=discord.Colour.from_rgb(r=33, g=33, b=33),
                description=f"Loading request...",
            )
            # send the uncool embed
            msg = await watchlist_channel.send(
                "",
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            # make and join a thread under the question
            thread = await msg.create_thread(name=f"BotRQ-{suggestion[:48]}", auto_archive_duration=10080)
            await thread.join()
            suggestion = suggestion.replace("\\n", "\n")
            # send a plaintext version of the question, and copy a link to it
            copyable_version = await thread.send(f"{suggestion}", allowed_mentions=discord.AllowedMentions.none())

            # mention developers in a message edit, adding them all to the thread without mentioning them
            # and do the same for the requester, though this will only work if they're in the staff server..
            joiner_msg = await thread.send("role mention placeholder")
            await joiner_msg.edit(content=f"<@&{itx.client.custom_ids['staff_developer_role']}> <@{itx.user.id}>")
            await joiner_msg.delete()

            # edit the uncool embed to make it cool: Show question, link to plaintext, and upvotes/downvotes
            embed = discord.Embed(
                color=discord.Colour.from_rgb(r=255, g=255, b=172),
                title=f'',
                description=f"{suggestion}\n[Jump to plain version]({copyable_version.jump_url})",
                timestamp=datetime.now()
            )
            embed.set_author(
                name=f"{itx.user.nick or itx.user.name}",
                url=f"https://original.poster/{itx.user.id}/",
                icon_url=itx.user.display_avatar.url
            )
            embed.set_footer(text=f"")

            await msg.edit(embed=embed)
            await msg.add_reaction("⬆️")
            await msg.add_reaction("⬇️")
            await itx.followup.send("Successfully added your suggestion! The developers will review your idea, "
                                    "and perhaps inform you when it gets added :D", ephemeral=True)
        except:  # something went wrong before so i wanna see if it happens again
            await itx.followup.send("Something went wrong!", ephemeral=True)
            raise

    @app_commands.command(name="ping_open_dev_requests",
                          description="Send a message in closed green dev request threads")
    async def ping_open_developer_requests(self, itx: discord.Interaction):
        if not is_staff(itx.guild, itx.user):
            await itx.response.send_message(
                "You need to be staff to do this! It just sends \"boop\" to every dev request thread lol.",
                ephemeral=True)
            return

        await itx.response.send_message("`[   ]`: Fetching cached threads.", ephemeral=True)
        try:
            watchlist_channel = itx.client.get_channel(itx.client.custom_ids["staff_dev_request"])
            threads: list[discord.Thread] = []
            pinged_thread_count = 0
            async for thread in watchlist_channel.archived_threads(limit=None):
                threads.append(thread)

            await itx.edit_original_response(content="`[#  ]`: Fetching archived threads...")
            archived_thread_ids = [t.id for t in threads]
            for thread in watchlist_channel.threads:
                if thread.archived and thread.id not in archived_thread_ids:
                    threads.append(thread)

            await itx.edit_original_response(content="`[## ]`: Sending messages in threads...")

            not_found_count = 0
            ignored_count = 0
            failed_threads = []

            for thread in threads:
                try:
                    starter_message = await watchlist_channel.fetch_message(thread.id)
                except discord.errors.NotFound:
                    not_found_count += 1
                    continue  # thread starter message was removed.

                if (starter_message is None or
                        not itx.client.is_me(starter_message.author) or
                        len(starter_message.embeds) == 0):
                    ignored_count += 1
                    continue
                if starter_message.embeds[0].color in [emoji_color_options["🟡"],
                                                       emoji_color_options["🔵"]]:
                    try:
                        cmd_mention = itx.client.get_command_mention("ping_open_dev_requests")
                        await thread.send(itx.user.mention + f" poked this thread with {cmd_mention}.\n"
                                                             "This channel got a message because it was archived and "
                                                             "the request wasn't marked as completed or rejected.",
                                          allowed_mentions=discord.AllowedMentions.none())
                        pinged_thread_count += 1
                    except discord.Forbidden:
                        failed_threads.append(thread.id)

            await itx.edit_original_response(
                content=(f"`[###]`: Pinged {pinged_thread_count} archived "
                         f"channel{'' if pinged_thread_count == 1 else 's'} successfully!\n"
                         f"\n"
                         f"Ignored `{ignored_count}` threads (not by bot or no embeds, etc.)\n"
                         f"Could not find `{not_found_count}` starter messages.\n"
                         f"Could not send a message in the following {len(failed_threads)} threads:\n"
                         f"- {', '.join(['<#' + str(t_id) + '>' for t_id in failed_threads])}")[:2000])
        except:
            await itx.followup.send("Something went wrong!", ephemeral=True)
            raise

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if (payload.guild_id != self.client.custom_ids["staff_server_id"] or
                payload.channel_id != self.client.custom_ids["staff_dev_request"]):
            return

        emoji_color_selection = {
            "🔴": discord.Colour.from_rgb(r=255, g=100, b=100),
            "🟡": discord.Colour.from_rgb(r=255, g=255, b=172),
            "🟢": discord.Colour.from_rgb(r=100, g=255, b=100),
            "🔵": discord.Colour.from_rgb(r=172, g=172, b=255)
        }
        if getattr(payload.emoji, "name", None) not in emoji_color_selection:
            return
        channel: discord.TextChannel = await self.client.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if not self.client.is_me(message.author):
            return
        if len(message.embeds) != 1:
            return
        embed = message.embeds[0]
        embed.colour = emoji_color_selection[payload.emoji.name]
        await message.edit(embed=embed)
        await message.remove_reaction(payload.emoji.name, payload.member)

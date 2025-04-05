from datetime import datetime

import discord
import discord.ext.commands as commands
import discord.app_commands as app_commands

from extensions.settings.objects import AttributeKeys, ModuleKeys
from resources.checks import is_staff_check, MissingAttributesCheckFailure, \
    module_enabled_check  # for dev request thread ping
from resources.customs import Bot


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
    @module_enabled_check(ModuleKeys.dev_requests)
    async def developer_request(self, itx: discord.Interaction[Bot], suggestion: app_commands.Range[str, 25, 1500]):
        developer_request_channel: discord.TextChannel | None
        developer_role: discord.Role | None
        developer_request_channel, developer_role = itx.client.get_guild_attribute(
            itx.guild, AttributeKeys.developer_request_channel,
            AttributeKeys.developer_request_reaction_role)
        if developer_request_channel is None or developer_role is None:
            missing = [key for key, value in {
                AttributeKeys.developer_request_channel: developer_request_channel,
                AttributeKeys.developer_request_reaction_role: developer_role}.items()
                if value is None]
            raise MissingAttributesCheckFailure(*missing)

        if len(suggestion) > 4000:
            await itx.response.send_message("Your suggestion won't fit! Please make your suggestion shorter. "
                                            "If you have a special request, you could make a ticket too "
                                            "(in #contact-staff)",
                                            ephemeral=True)
            return
        await itx.response.defer(ephemeral=True)

        # make uncool embed for the loading period while it sends the copyable version
        embed = discord.Embed(
            color=discord.Colour.from_rgb(r=33, g=33, b=33),
            description="Loading request...",
        )
        # send the uncool embed
        msg = await developer_request_channel.send(
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

        # Mention developers in a message edit, adding them all to the thread
        # without mentioning them and do the same for the requester, though
        # this will only work if they're in the staff server..
        joiner_msg = await thread.send("role mention placeholder")
        developer_role = itx.client.get_guild_attribute(
            itx.user.guild, AttributeKeys.developer_request_channel)
        if developer_role is None:
            cmd_mention_settings = itx.client.get_command_mention("settings")
            await joiner_msg.edit(
                content=f"No role has been set up to be pinged after a "
                        f"developer request is created. Use "
                        f"{cmd_mention_settings} to add one.")
        else:
            await joiner_msg.edit(content=f"<@&{developer_role.id}> <@{itx.user.id}>")
            await joiner_msg.delete()

        # edit the uncool embed to make it cool: Show question, link to plaintext, and upvotes/downvotes
        embed = discord.Embed(
            color=discord.Colour.from_rgb(r=255, g=255, b=172),
            title='',
            description=f"{suggestion}\n[Jump to plain version]({copyable_version.jump_url})",
            timestamp=datetime.now()
        )
        embed.set_author(
            name=f"{itx.user.nick or itx.user.name}",
            url=f"https://original.poster/{itx.user.id}/",
            icon_url=itx.user.display_avatar.url
        )
        embed.set_footer(text="")

        await msg.edit(embed=embed)
        await msg.add_reaction("⬆️")
        await msg.add_reaction("⬇️")
        await itx.followup.send("Successfully added your suggestion! The developers will review your idea, "
                                "and perhaps inform you when it gets added :D", ephemeral=True)

    @app_commands.command(name="ping_open_dev_requests",
                          description="Send a message in closed green dev request threads")
    @app_commands.check(is_staff_check)
    @module_enabled_check(ModuleKeys.dev_requests)
    async def ping_open_developer_requests(self, itx: discord.Interaction[Bot]):
        await itx.response.send_message("`[+  ]`: Fetching cached threads.", ephemeral=True)
        watchlist_channel: discord.TextChannel | None = itx.client.get_guild_attribute(
            itx.guild, AttributeKeys.developer_request_channel)
        if watchlist_channel is None:
            raise MissingAttributesCheckFailure(AttributeKeys.developer_request_channel)

        threads: list[discord.Thread] = []
        pinged_thread_count = 0
        async for thread in watchlist_channel.archived_threads(limit=None):
            threads.append(thread)

        await itx.edit_original_response(content="`[#+ ]`: Fetching archived threads...")
        archived_thread_ids = [t.id for t in threads]
        for thread in watchlist_channel.threads:
            if thread.archived and thread.id not in archived_thread_ids:
                threads.append(thread)

        await itx.edit_original_response(content="`[##+]`: Sending messages in threads...")

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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not self.client.is_module_enabled(payload.guild_id, ModuleKeys.dev_requests):
            return
        dev_request_channel: discord.TextChannel = self.client.get_guild_attribute(
            payload.guild_id, AttributeKeys.developer_request_channel)
        if dev_request_channel is None:
            raise MissingAttributesCheckFailure(AttributeKeys.developer_request_channel)

        if dev_request_channel.id != payload.channel_id:
            return

        if getattr(payload.emoji, "name", None) not in emoji_color_options:
            return

        message = await dev_request_channel.fetch_message(payload.message_id)
        if not self.client.is_me(message.author):
            return
        if len(message.embeds) != 1:
            return
        embed = message.embeds[0]
        embed.colour = emoji_color_options[payload.emoji.name]
        await message.edit(embed=embed)
        await message.remove_reaction(payload.emoji.name, payload.member)

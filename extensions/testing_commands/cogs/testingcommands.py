from datetime import datetime
import random

import discord
from discord.ext import commands
import discord.app_commands as app_commands

from extensions.settings.objects import AttributeKeys
from resources.checks import MissingAttributesCheckFailure, is_staff_check
from resources.customs import Bot
from resources.views.generics import PageView, create_simple_button


async def _make_vclog_embed(
        mode: str,
        from_channel: discord.VoiceChannel | discord.StageChannel,
        to_channel: discord.VoiceChannel | discord.StageChannel,
        user: discord.Member
):
    if mode == "Move":
        embed: discord.Embed = discord.Embed(
            description=f"**{user.name}#{user.discriminator}** moved from "
                        f"{from_channel.mention} ({from_channel.name}) to "
                        f"{to_channel.mention} ({to_channel.name}).",
        )
        embed.add_field(
            name="Current channel they are in",
            value=f"{to_channel.mention} ({to_channel.name})",
            inline=False
        )
        embed.add_field(
            name="Previously occupied channel",
            value=f"{from_channel.mention} ({from_channel.name})",
            inline=False
        )
        embed.add_field(
            name="ID",
            value=f"```ini\n"
                  f"User = {user.id}\n"
                  f"New = {to_channel.id}\n"
                  f"Old = {from_channel.id}```",
            inline=False
        )
    else:
        mode_str, channel = (("joined", to_channel) if mode == "Join"
                             else ("left", from_channel))
        channel_str = ("voice" if type(channel) is discord.VoiceChannel
                       else "stage")
        nick_maybe = f"({user.nick}) " if user.nick else ""
        embed: discord.Embed = discord.Embed(
            description=f"**{user.name}#{user.discriminator}** {nick_maybe}"
                        f"{mode_str} {channel_str} channel: {channel.name}.",
        )
        embed.add_field(
            name="Channel",
            value=f"{channel.mention} ({channel.name})",
            inline=False
        )
        embed.add_field(
            name="ID",
            value=f"```ini\n"
                  f"User = {user.id}\n"
                  f"Channel = {channel.id}```",
            inline=False
        )

    embed.colour = 3553599
    embed.timestamp = datetime.now().astimezone()
    embed.set_author(
        name=f"{user.name}#{user.discriminator}",
        icon_url=user.avatar.url,
    )
    embed.set_footer(
        text=f"{user.name}#{user.discriminator}",
        icon_url=user.avatar.url
    )

    return embed


class TestingCog(commands.GroupCog, name="testing"):
    def __init__(self):
        # todo: try to implement tests for commands instead of doing roundabout ways like these.
        pass

    @app_commands.command(name="send_fake_watchlist_modlog", description="make a fake user modlog report")
    @app_commands.describe(
        target="User to add",
        reason="Reason for adding",
        rule="rule to punish for",
        private_notes="private notes to include",
        role_changes="role changes ([[\\n]] converts to newline)"
    )
    @app_commands.check(is_staff_check)
    async def send_fake_watchlist_mod_log(
            self, itx: discord.Interaction, target: discord.User, reason: str = "",
            rule: str = None, private_notes: str = "", role_changes: str = ""
    ):
        staff_logs_category = itx.client.get_guild_attribute(
            itx.guild, AttributeKeys.staff_logs_category
        )
        if staff_logs_category is None:
            raise MissingAttributesCheckFailure(AttributeKeys.staff_logs_category)

        embed = discord.Embed(title="did a log thing for x", color=16705372)
        embed.add_field(name="User", value=f"{target.mention} (`{target.id}`)", inline=True)
        embed.add_field(name="Moderator", value=f"{itx.user.mention}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Rule", value=f">>> {rule}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Reason", value=f">>> {reason}")
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Private Notes", value=f">>> {private_notes}")
        embed.add_field(name="\u200b", value="\u200b", inline=False)
        embed.add_field(name="Role Changes", value=role_changes.replace("[[\\n]]", "\n"))
        # any channel in AttributeKeys.staff_logs_category should work.
        await staff_logs_category.send(embed=embed)

    @app_commands.command(name="send_pageview_test", description="Send a test embed with page buttons")
    @app_commands.describe(page_count="The amount of pages to send/test")
    @app_commands.check(is_staff_check)
    async def send_pageview_test_embed(
            self, itx: discord.Interaction, page_count: app_commands.Range[int, 1, 10000] = 40
    ):
        def get_chars(length: int):
            letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/   "
            return (''.join(random.choice(letters) for _ in range(length))).strip()

        async def update_test_page(itx1: discord.Interaction, view1: PageView):
            embed = view1.pages[view1.page]
            await itx1.response.edit_message(
                content="updated a" + str(view1.page),
                embed=embed,
                view=view1
            )

        pages = []
        for page_index in range(page_count):  # embeds
            e = discord.Embed(
                color=discord.Color.from_hsv(random.random(), 0.40, 0.100),
                title=get_chars(random.randint(15, 40)),
                description=get_chars(60)
            )
            for _ in range(0, 4):  # embed fields
                e.add_field(
                    name=get_chars(random.randint(10, 30)),
                    value=get_chars(random.randint(20, 60)),
                    inline=False
                )
            e.set_footer(text=f"{page_index + 1}/{page_count}")
            pages.append(e)

        async def go_to_page_button_callback(itx1: discord.Interaction):
            # view: PageView = view
            await itx1.response.send_message(f"This embed has {view.max_page_index + 1} pages!")

        go_to_page_button = create_simple_button("🔢", discord.ButtonStyle.blurple, go_to_page_button_callback,
                                                 label_is_emoji=True)
        view = PageView(0, len(pages), update_test_page, appended_buttons=[go_to_page_button])
        await itx.response.send_message("Sending this cool embed...", embed=pages[0], view=view)

    @app_commands.command(name="send_srmod_appeal_test", description="Send a test embed of a ban appeal")
    @app_commands.describe(username="The username you want to fill in")
    @app_commands.check(is_staff_check)
    async def send_srmod_appeal_test(self, itx: discord.Interaction, username: str):
        embed: discord.Embed = discord.Embed(title="New Ban Appeal")
        embed.add_field(name="Which of the following are you appealing?",
                        value="Discord Ban")
        embed.add_field(name="What is your discord username?",
                        value=username)
        embed.add_field(name="Why were you banned?",
                        value="I spammed this chanel D:")
        embed.add_field(name="Why do you wish to be unbanned?",
                        value="i was promisd cokies :cookie:")
        embed.add_field(name="Do you have anything else to add?",
                        value="me eepy")
        await itx.channel.send("Sending this cool embed...", embed=embed)

    @app_commands.command(name="send_vc_log_test",
                          description="Send a test embed of a vc log")
    @app_commands.describe(mode="Whether you joined, left, or moved channels",
                           from_channel="The channel you left from",
                           to_channel="The channel you joined")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Join", value="Join"),
        app_commands.Choice(name="Leave", value="Leave"),
        app_commands.Choice(name="Move", value="Move"),
    ])
    @app_commands.check(is_staff_check)
    async def send_vc_log_test(
            self,
            itx: discord.Interaction[Bot],
            mode: str,
            from_channel: discord.VoiceChannel | discord.StageChannel = None,
            to_channel: discord.VoiceChannel | discord.StageChannel = None,
    ):
        itx.response: discord.InteractionResponse  # noqa
        # jeez the log is inconsistent lol
        user = itx.user

        if mode == "Join" and to_channel is None:
            await itx.response.send_message(
                "Mode \"Join\" needs to_channel!",
                ephemeral=True
            )
            return
        elif mode == "Leave" and from_channel is None:
            await itx.response.send_message(
                "Mode \"Leave\" needs from_channel!",
                ephemeral=True
            )
            return
        elif to_channel is None and from_channel is None:
            await itx.response.send_message(
                "Mode \"Move\" needs from_channel and to_channel!",
                ephemeral=True
            )
            return

        embed = await _make_vclog_embed(mode, from_channel, to_channel, user)
        await itx.channel.send(embed=embed)

        await itx.response.send_message("Sent.", ephemeral=True)

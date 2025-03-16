import random

import discord
from discord.ext import commands
from discord import app_commands

from resources.customs.bot import Bot
from resources.views.generics import PageView, create_simple_button


class TestingCog(commands.GroupCog, name="testing"):
    def __init__(self, client: Bot):
        self.client = client

    @app_commands.command(name="send_fake_watchlist_modlog", description="make a fake user modlog report")
    @app_commands.describe(
        target="User to add",
        reason="Reason for adding",
        rule="rule to punish for",
        private_notes="private notes to include",
        role_changes="role changes ([[\\n]] converts to newline)"
    )
    async def send_fake_watchlist_mod_log(
            self, itx: discord.Interaction, target: discord.User, reason: str = "",
            rule: str = None, private_notes: str = "", role_changes: str = ""
    ):
        embed = discord.Embed(title="did a log thing for x", color=16705372)
        embed.add_field(name="User", value=f"{target.mention} (`{target.id}`)", inline=True)
        embed.add_field(name="Moderator", value=f"{itx.user.mention}", inline=True)
        embed.add_field(name="\u200b", value=f"\u200b", inline=False)
        embed.add_field(name="Rule", value=f">>> {rule}", inline=True)
        embed.add_field(name="\u200b", value=f"\u200b", inline=False)
        embed.add_field(name="Reason", value=f">>> {reason}")
        embed.add_field(name="\u200b", value=f"\u200b", inline=False)
        embed.add_field(name="Private Notes", value=f">>> {private_notes}")
        embed.add_field(name="\u200b", value=f"\u200b", inline=False)
        embed.add_field(name="Role Changes", value=role_changes.replace("[[\\n]]", "\n"))
        # any channel in self.client.custom_ids["staff_logs_category"] should work.
        await self.client.get_channel(1143642283577725009).send(embed=embed)

    @app_commands.command(name="send_pageview_test", description="Send a test embed with page buttons")
    @app_commands.describe(page_count="The amount of pages to send/test")
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
    async def send_pageview_test_embed(self, itx: discord.Interaction, username: str):
        embed: discord.Embed = discord.Embed(title="New Ban Appeal")
        embed.add_field(name="Which of the following are you appealing?", value="Discord Ban")
        embed.add_field(name="What is your discord username?", value=username)
        embed.add_field(name="Why were you banned?", value="I spammed this chanel D:")
        embed.add_field(name="Why do you wish to be unbanned?", value="i was promisd cokies :cookie:")
        embed.add_field(name="Do you have anything else to add?", value="me eepy")
        await itx.channel.send("Sending this cool embed...", embed=embed)


async def setup(client: Bot):
    await client.add_cog(TestingCog(client))

import discord
from discord.ext import commands
from discord import app_commands
from resources.customs.bot import Bot
from resources.modals.help import JumpToPageModal_HelpCommands_Help
from resources.views.generics import PageView, create_simple_button

import random


class TestingCog(commands.GroupCog,name="testing"):
    def __init__(self, client: Bot):
        self.client = client

    @app_commands.command(name="send_fake_watchlist_modlog", description="make a fake user modlog report")
    @app_commands.describe(target="User to add", reason="Reason for adding", rule="rule to punish for", private_notes="private notes to include")
    async def send_fake_watchlist_mod_log(self, itx: discord.Interaction, target: discord.User, reason: str = "", rule: str = None, private_notes: str = ""):
        embed = discord.Embed(title="did a log thing for x", color=16705372)
        embed.add_field(name="User",value = f"{target.mention} (`{target.id}`)", inline=True)
        embed.add_field(name="Moderator",value = f"{itx.user.mention}", inline=True)
        embed.add_field(name="\u200b",value = f"\u200b", inline=False)
        embed.add_field(name="Rule",value = f">>> {rule}", inline=True)
        embed.add_field(name="\u200b",value = f"\u200b", inline=False)
        embed.add_field(name="Reason",value = f">>> {reason}")
        embed.add_field(name="\u200b",value = f"\u200b", inline=False)
        embed.add_field(name="Private Notes",value = f">>> {private_notes}")
        # any channel in self.client.custom_ids["staff_logs_category"] should work.
        await self.client.get_channel(1143642283577725009).send(embed=embed)

    @app_commands.command(name="send_pageview_test", description="Send a test embed with page buttons")
    @app_commands.describe(page_count="The amount of pages to send/test")
    async def send_pageview_test_embed(self, itx: discord.Interaction, page_count: int = 40):
        def getChars(len: int):
            letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/   "
            return (''.join(random.choice(letters) for i in range(len))).strip()
        
        pages = []
        for page_index in range(page_count): # embeds
            e = discord.Embed(
                color=discord.Color.from_hsv(random.random(), 0.40, 0.100),
                title=getChars(random.randint(15, 40)),
                description=getChars(60)
            )
            for _ in range(0, 4): # embed fields
                e.add_field(
                    name = getChars(random.randint(10, 30)),
                    value = getChars(random.randint(20, 60)),
                    inline=False
                )
            e.set_footer(text=f"{page_index+1}/{page_count}")
            pages.append(e)
        
        async def update_test_page(itx: discord.Interaction, view: PageView):
            e = view.pages[view.page]
            await itx.response.edit_message(
                content="updated a" + str(view.page),
                embed=e,
                view=view
            )
        

        async def go_to_page_button_callback(itx: discord.Interaction):
            # view: PageView = view
            await itx.response.send_message(f"This embed has {view.max_page_index+1} pages!")
        
        go_to_page_button = create_simple_button("🔢", discord.ButtonStyle.blurple, go_to_page_button_callback, label_is_emoji=True)
        view = PageView(0, pages, update_test_page, appended_buttons=[go_to_page_button])
        await itx.response.send_message("Sending this cool embed...", embed=pages[0], view=view)
        


async def setup(client):
    await client.add_cog(TestingCog(client))
import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from resources.customs.bot import Bot
from resources.utils.stringhelper import replace_string_command_mentions

from extensions.help.helppage import HelpPage
from extensions.help.helppages import help_pages
from extensions.help.utils import generate_help_page_embed, get_nearest_help_pages_from_page
from extensions.help.views.helppage import HelpPageView


FIRST_PAGE: int = sorted(list(help_pages))[0]
#    all pages only have one of these attributes
assert all([type(i) is int for i in help_pages]), "All help pages should have an integer key."
assert sorted(list(help_pages)) == list(help_pages), "All help pages should be sorted by default."
assert all([all([j in ["title", "description", "fields", "staff_only"] for j in help_pages[i]]) for i in help_pages]), \
    "All pages should only have fields that are one of these attributes: title, description, fields, staff_only"


class HelpCommand(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    async def send_help_menu(self, itx: discord.Interaction, requested_page: int = FIRST_PAGE):
        if requested_page not in help_pages:
            min_index, max_index = get_nearest_help_pages_from_page(requested_page, list(help_pages))
            relative_page_location_details = f"(nearest pages are `{min_index}` and `{max_index}`)."
            await itx.response.send_message(
                replace_string_command_mentions(
                    (
                        f"This page (`{requested_page}`) does not exist! " if requested_page != 404 else
                        "`404`: Page not found!") +  # easter egg
                    f" {relative_page_location_details} " +
                    "Try %%help%% `page:1` or use the page keys to get to the right page number!",
                    self.client
                ),
                ephemeral=True
            )
            return

        embed = generate_help_page_embed(help_pages[requested_page], requested_page, self.client)
        await itx.response.send_message(embed=embed,
                                        view=HelpPageView(self.client, requested_page, help_pages),
                                        ephemeral=True)

    @app_commands.command(name="help", description="A help command to learn more about me!")
    @app_commands.describe(page="What page do you want to jump to? (useful if sharing commands)")
    async def help(self, itx: discord.Interaction, page: int = FIRST_PAGE):
        await self.send_help_menu(itx, page)

    @app_commands.command(name="commands", description="A help command to learn more about me!")
    @app_commands.describe(page="What page do you want to jump to? (useful if sharing commands)")
    async def commands(self, itx: discord.Interaction, page: int = FIRST_PAGE):
        await self.send_help_menu(itx, page)

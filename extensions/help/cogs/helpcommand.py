import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from resources.customs.bot import Bot
from resources.utils.permissions import is_admin
from resources.utils.stringhelper import replace_string_command_mentions

from extensions.help.helppages import help_pages, aliases, FIRST_PAGE
from extensions.help.helppage import HelpPage
from extensions.help.utils import get_nearest_help_pages_from_page, generate_help_page_embed
from extensions.help.views.helppage import HelpPageView


async def send_help_menu(itx: discord.Interaction, requested_page: int = FIRST_PAGE):
    if requested_page not in help_pages:
        min_index, max_index = get_nearest_help_pages_from_page(requested_page, list(help_pages))
        relative_page_location_details = f"(nearest pages are `{min_index}` and `{max_index}`)."
        await itx.response.send_message(
            replace_string_command_mentions(
                (  # easter egg
                    f"This page (`{requested_page}`) does not exist! " if requested_page != 404 else
                    "`404`: Page not found!"
                ) +
                f" {relative_page_location_details} " +
                "Try %%help%% `page:1` or use the page keys to get to the right page number!",
                itx.client
            ),
            ephemeral=True
        )
        return

    user_is_staff = is_admin(itx.guild, itx.user)
    if not user_is_staff and help_pages[requested_page].get("staff_only", False):
        # user is not staff but the page is staff-only
        await itx.response.send_message("This page is only available to admins.", ephemeral=True)
        return

    embed = generate_help_page_embed(help_pages[requested_page], requested_page, itx.client)

    await itx.response.send_message(embed=embed,
                                    view=HelpPageView(requested_page, help_pages, user_is_staff),
                                    ephemeral=True)

async def _help_page_autocomplete(itx: discord.Interaction, current: str) -> list[app_commands.Choice[int]]:
    results = []
    added_pages = []

    user_is_staff = is_admin(itx.guild, itx.user)

    if current.isdecimal():
        current_page = None
        try:
            current_page = int(current)
        except ValueError:
            pass

        if current_page is not None and current_page in aliases:
            if user_is_staff or not help_pages[current_page].get("staff_only", False):
                results.append(app_commands.Choice(name=aliases[current_page][0], value=current_page))
                return results

    # search aliases
    for page in aliases:
        for alias in aliases[page]:
            if not user_is_staff and help_pages[page].get("staff_only", False):
                continue

            if current.lower() in alias.lower():
                results.append(app_commands.Choice(name=alias[:100], value=page))
                added_pages.append(page)
                break  # only add each page once
        if len(results) >= 10:
            return results

    if len(results) >= 2:
        return results

    # search page descriptions
    for page in help_pages:
        if not user_is_staff and help_pages[page].get("staff_only", False):
            continue

        if page in added_pages:
            continue
        if current.lower() in help_pages[page]["description"].lower():
            results.append(app_commands.Choice(name=help_pages[page]["title"][:100], value=page))
            # added_pages.append(page)  # unnecessary because it won't iterate pages after this.
        if len(results) >= 10:
            break

    return results


class HelpCommand(commands.Cog):
    def __init__(self):
        pass

    @app_commands.command(name="help", description="A help command to learn more about me!")
    @app_commands.describe(page="What page do you want to jump to? (useful if sharing commands)")
    @app_commands.autocomplete(page=_help_page_autocomplete)
    async def help(self, itx: discord.Interaction, page: int = FIRST_PAGE):
        await send_help_menu(itx, page)

    @app_commands.command(name="commands", description="A help command to learn more about me!")
    @app_commands.describe(page="What page do you want to jump to? (useful if sharing commands)")
    @app_commands.autocomplete(page=_help_page_autocomplete)
    async def commands(self, itx: discord.Interaction, page: int = FIRST_PAGE):
        await send_help_menu(itx, page)

import discord, discord.ext.commands as commands, discord.app_commands as app_commands
from resources.customs.bot import Bot
from resources.views.help import PageView_HelpCommands_Help
from resources.customs.help import HelpPage
from resources.utils.stringhelper import replace_string_command_mentions


help_pages: dict[int, HelpPage] = {
    0 : HelpPage( # fallback default page
        title="Rina's fallback help page",
        description="""Hi there! This bot has a whole bunch of commands. Let me introduce you to some:
%%add_poll_reactions%%: Add an up-/downvote emoji to a message (for voting)
%%commands%% or %%help%%: See this help page
%%compliment%%: Rina can compliment others (matching their pronoun role)
%%convert_unit%%: Convert a value from one to another! Distance, speed, currency, etc.
%%dictionary%%: Search for an lgbtq+-related or dictionary term!
%%equaldex%%: See LGBTQ safety and rights in a country (with API)
%%math%%: Ask Wolfram|Alpha for math or science help
%%nameusage gettop%%: See how many people are using the same name
%%pronouns%%: See someone's pronouns or edit your own
%%qotw%% and %%developer_request%%: Suggest a Question Of The Week or Bot Suggestion to staff
%%reminder reminders%%: Make or see your reminders
%%roll%%: Roll some dice with a random result
%%tag%%: Get information about some of the server's extra features
%%todo%%: Make, add, or remove items from your to-do list
%%toneindicator%%: Look up which tone tag/indicator matches your input (eg. /srs)

Make a custom voice channel by joining "Join to create VC" (use %%tag%% `tag:customvc` for more info)
%%editvc%%: edit the name or user limit of your custom voice channel
%%vctable about%%: Learn about making your voice chat more on-topic!
"""
    ),
    #region Default pages (home / index)
    1 : HelpPage(
        title = "Rina's commands",
        description = "Hey there. This is Rina. I'm a bot that does silly things for TransPlace and some linked servers. I'm being maintained by <@262913789375021056>.\n"
                      "I can do many things like looking up tone indicators or words, or sharing server info and questions of the week. To share my commands, I've made this cool interactive menu.\n"
                      "\n"
                      "Use the buttons below to cycle through different categories of commands!\n"
                      "\n"
                      "📋 Index (page 2)\n"
                      "◀️ Previous page:\n"
                      "▶️ Next page: Index\n"
                      "🔢 Jump to page\n"
                      "\n"
                      "Do you have a cool bot idea? use %%developer_request%% to suggest them to staff!"
    ),
    2 : HelpPage(
        title = "Index",
        description = "Here's a list of all the categories. You can use the :1234: button to quickly hop "
                      "between these pages. Press :clipboard: to quickly go back to this index page.\n"
                      "\n"
                      ". . **1:** Welcome page\n"
                      ". . **2:** Index\n"
                      ". . **3:** Utility\n"
    ),
    #endregion
    #region Expanded index pages (commands)
    3 : HelpPage( # index: Utility
        title = "Utility",
        description = "Some commands help in your daily life, like the following commands:\n"
                      "\n"
                      ". . **101:** roll\n"
                      ". . **103:** reminder\n"
                      ". . **104:** convert_unit\n"
                      ". . **105:** todo\n",
    ),
    4 : HelpPage(
        title = "null",
        description = "null"
    ),
    5 : HelpPage(
        title = "null",
        description = "null"
    ),
    #endregion
    #region Utility commands
    101 : HelpPage( # dice rolls
        title = "Rolling dice", # /roll
        description = "Have you ever wanted to roll virtual dice? Now you can!\n"
                      "Rina lets you roll dice with many kinds of faces. Rolling a 2-faced die (aka, a coin)? sure!\n"
                      "\n"
                      "Because this command also allows an __advanced input__, go to the next page for more info: __**102**__\n",
        fields = [
            (
                "Parameters",
                "`dice`: How many dice do you want to roll?\n"
                "- Any number between 1 and 999999\n"
                "`faces`: How many sides does every die have?\n"
                "- Any number between 1 and 999999\n"
                "`mod`: Do you want to add a modifier? (eg. add 2 after rolling the dice)\n"
                "- (optional) Any (negative) (decimal) number\n"
                "`advanced`: Roll more advanced! example: 1d20+3*2d4\n"
                "- (optional) String of your advanced dice roll. See page __**102**__ for more info."
            ),
            (
                "Examples",
                "- %%roll%% `dice:3` `faces:6`\n"
                "  - rolls 3 dice with 6 faces (3d6), aka rolling 3 normal dice\n"
                "- %%roll%% `dice:6` `faces:2`\n"
                "  - rolls 6 dice with 2 faces (6d2), aka flipping 6 coins\n"
                "- %%roll%% `dice:3` `faces:2` `mod:4`\n"
                "  - flip 3 coins, then add '4' to the final outcome.\n"
                "  - eg. 1 + 2 + 2 = 5 (3 dice with 2 faces), then add 4 to the final result = 5 + 4 = 9\n"
                "- %%roll%% `dice:1` `faces:1` `advanced:help`\n"
                "  - See next page (__**102**__) for more information about advanced dice rolls."
            )
        ]
    ),
    102 : HelpPage( # dice rolls advanced
        title = "Advanced dice rolls", # /roll advanced: ...
        description = "In the case that the simple dice roll command is not enough, you can roll complexer combinations of dice rolls using the advanced option.\n"
                      "The advanced mode lets you use addition, subtraction, multiplication, and custom dice.\n"
                      "To use the advanced function, you must give a value to the required parameters first ('dice' and 'faces') (the inserted value is ignored).\n"
                      "Supported characters are: `0123456789d+*-`. Spaces are ignored. Multiplication goes before addition/subtraction.",
        fields = [
            (
                "Examples",
                "- %%roll%% `dice:1` `faces:1` `advanced:3d2 + 1`\n"
                "  - Flip 3 coins (dice with 2 faces), then add 1 to the total.\n"
                "- %%roll%% `dice:9999` `faces:9999` `advanced:2d20*2`\n"
                "  - Roll two 20-sided dice, add their eyes, and then multiply the total by 2.\n"
                "- %%roll%% `dice:1` `faces:1` `advanced:2*1d20+2*1d20`\n"
                "  - Same as the above.\n"
                "- %%roll%% `dice:1` `faces:1` `advanced:5d6*2d6-3d6`\n"
                "  - Multiply the outcome of 5 dice with the outcome of 2 dice, and subtract the outcome of 3 dice."
             )
        ]
    ),
    103 : HelpPage( # reminders
        title = "Reminders", # /reminder
        description = "With this feature, you'll never forget your tasks anymore! (so long as Rina is online...).\n"
                      "This command lets you create, remove, and view your reminders.",
        fields = [
            (
                "reminder remindme",
                "> %%reminder remindme%% `time:` `reminder:`\n"
                "`time`: When do you want to be reminded?\n"
                "- Use a format like 10d9h8m7s for days/hours/min/sec.\n" #TODO: clarify; copy paste ValueError help message?
                "`reminder`: What would you like to be reminded of?"
            ),
            (
                "reminder reminders",
                "%%reminder reminders%% [`item:`]\n"
                "- Show a list of active reminders. They each have a number. Use `item:number` to view more information about this reminder."
            ),
            (
                "reminder remove",
                "%%reminder remove%% item:\n"
                "- Remove a reminder. Use %%reminder reminders%% to see a list of reminders. Each has a number. Use that number to remove the reminder like so: `item:number`."
            )
        ]
    ),
    104 : HelpPage( # convert unit
        title = "Converting units",
        description = "Since international communities often share stories about temperature and speed, it's not uncommon to have to look up how many feet go in a centimeter. "
                      "This module lets you easily converty a large amount of units in multiple categories! Currencies are fetched live using an online website (api)!\n"
                      "The units (`from` and `to_unit`) will autocomplete depending on the selected category.",
        fields = [
            (
                "Parameters",
                "`mode`: What type of unit do you want to compare? length/time/currency/...\n"
                "`from`: What unit are you trying to convert? (eg. Celsius / Fahrenheit)\n"
                "`value`: How much of this unit are you converting? (think __20__ degrees Celsius)\n"
                "`to_unit`: What unit to convert to? *C -> *F : fill in Fahrenheit.\n"
                "`public`: (optional) Do you want to show this to everyone in chat?\n"
                "- Default: False"
            ),
            (
                "Examples",
                "%%convert_unit%% `mode:Length (miles,km,inch)` `from:meter` `value:80` `to_unit:yard`\n"
                "- Convert 80 meters to yards = about 87.5 yd\n"
                ""
            )
        ]
    ),
    105 : HelpPage( # to-do list
        title = "Todo lists",
        description = "For the forgetful, or if you just want a nice grocery list, this command is for you! You can easily add and remove to-do notes, and they're saved throughout all servers with me (TransPlace, EnbyPlace, Transonance, etc.)",
        fields = [
            (
                "Parameters",
                "`mode`: Do you want to add, remove, or check (view) your to-do list?\n"
                "- if you want to add to / remove from your to-do list, you must also give the `todo` value below.\n"
                "`todo`:\n"
                "- Add: What to-do would you like to add?\n"
                "- Remove: What to-do item would you like to remove from your list? Give the number of the to-do list as it's shown with %%todo%% `mode:Check`"
            ),
            (
                "Examples",
                "%%todo%% `mode:Add something to your to-do list` `todo:Create a nice help command`\n"
                "- Add \"Create a nice help command\"\n"
                "%%todo%% `mode:Check`\n"
                "- Your to-do list would look like this. Note how each item starts with a number. Use this number to remove them.\n"
                "  - Found 4 to-do items:\n"
                "  - `0`: Create a nice help command\n"
                "%%todo%% `mode:Remove to-do` `todo:0`\n"
                "- Remove to-do item number 0 from your list. Use %%todo%% `mode:Check` to see what number to use to remove the right item.\n"
                "- Keep in mind that the order will shift after you've removed an item, so redo the `check` command to make sure you're removing the right command when removing multiple to-do items at once!"
            )
        ]
    )
    #endregion
}
FIRST_PAGE: int = sorted(list(help_pages))[0]

assert all([type(i) is int for i in help_pages]) # all help pages have an integer key
assert sorted(list(help_pages)) == list(help_pages) # all help pages are sorted by default
assert all([all([j in ["title", "description", "fields"] for j in help_pages[i]]) for i in help_pages]) # all pages only have one of these attributes


# TODO: move to own file
def generate_help_page_embed(page: HelpPage, page_number: int, client: Bot) -> discord.Embed:
    """
    Helper command to generate an embed for a specific help page. This command is mainly to prevent inconsistencies between the /help calling and updating functions.
    Page fields are appended after the description, in the order they are given in the list.

    Parameters:
    -----------
    page: :class:`help_page`:
        The help page to reference. This is a TypedDict{"title":str, "description":str, "fields":list[tuple[str,str]]}.
    page_number: :class:`int`:
        The page number of the help page. This number is added as footer, but is also used for the hue (HSV) value of the embed color.
    client: :class:`Bot`:
        The bot instance for get_command_mention().

    Returns:
    :class:`discord.Embed`: An embed of the given help page.
    """
    embed = discord.Embed(color = discord.Color.from_hsv((180 + page_number*10)/360, 0.4, 1),
                          title = page["title"],
                          description = replace_string_command_mentions(page["description"], client))
    if "fields" in page:
        for field in page["fields"]:
            embed.add_field(name  = replace_string_command_mentions(field[0], client), 
                            value = replace_string_command_mentions(field[1], client), 
                            inline = False)
    embed.set_footer(text="page: "+str(page_number))
    return embed


class HelpCommand(commands.Cog):
    def __init__(self, client: Bot):
        global RinaDB
        self.client = client
        RinaDB = client.RinaDB

    async def send_help_menu(self, itx: discord.Interaction, requested_page: int):
        embed = discord.Embed(color = discord.Color.from_hsv(180/360, 0.4, 1),
                              title = help_pages[requested_page]["title"],
                              description = replace_string_command_mentions(help_pages[requested_page]["description"], self.client))
        if "fields" in help_pages[requested_page]:
            for field in help_pages[requested_page]["fields"]:
                embed.add_field(name  = replace_string_command_mentions(field[0], self.client),
                                value = replace_string_command_mentions(field[1], self.client),
                                inline = False)

        embed.set_footer(text = f"page: {requested_page}")

        await itx.response.send_message(embed = embed,
                                        view = PageView_HelpCommands_Help(help_pages, requested_page, self.client),
                                        ephemeral = True)


        #region old help command
#         out = f"""\
# Hi there! This bot has a whole bunch of commands. Let me introduce you to some:
# {self.client.get_command_mention('add_poll_reactions')}: Add an up-/downvote emoji to a message (for voting)
# {self.client.get_command_mention('commands')} or {self.client.get_command_mention('help')}: See this help page
# {self.client.get_command_mention('compliment')}: Rina can compliment others (matching their pronoun role)
# {self.client.get_command_mention('convert_unit')}: Convert a value from one to another! Distance, speed, currency, etc.
# {self.client.get_command_mention('dictionary')}: Search for an lgbtq+-related or dictionary term!
# {self.client.get_command_mention('equaldex')}: See LGBTQ safety and rights in a country (with API)
# {self.client.get_command_mention('math')}: Ask Wolfram|Alpha for math or science help
# {self.client.get_command_mention('nameusage gettop')}: See how many people are using the same name
# {self.client.get_command_mention('pronouns')}: See someone's pronouns or edit your own
# {self.client.get_command_mention('qotw')} and {self.client.get_command_mention('developer_request')}: Suggest a Question Of The Week or Bot Suggestion to staff
# {self.client.get_command_mention('reminder reminders')}: Make or see your reminders
# {self.client.get_command_mention('roll')}: Roll some dice with a random result
# {self.client.get_command_mention('tag')}: Get information about some of the server's extra features
# {self.client.get_command_mention('todo')}: Make, add, or remove items from your to-do list
# {self.client.get_command_mention('toneindicator')}: Look up which tone tag/indicator matches your input (eg. /srs)

# Make a custom voice channel by joining "Join to create VC" (use {self.client.get_command_mention('tag')} `tag:customvc` for more info)
# {self.client.get_command_mention('editvc')}: edit the name or user limit of your custom voice channel
# {self.client.get_command_mention('vctable about')}: Learn about making your voice chat more on-topic!
# """
# # Check out the #join-a-table channel: In this channel, you can claim a channel for roleplaying or tabletop games for you and your group!
# # The first person that joins/creates a table gets a Table Owner role, and can lock, unlock, or close their table.
# # {self.client.get_command_mention('table lock')}, {self.client.get_command_mention('table unlock')}, {self.client.get_command_mention('table close')}
# # You can also transfer your table ownership to another table member, after they joined your table: {self.client.get_command_mention('table newowner')}\
# # """
#         await itx.response.send_message(out, ephemeral=True)
        #endregion

    @app_commands.command(name="help", description="A help command to learn more about me!")
    @app_commands.describe(page="What page do you want to jump to? (useful if sharing commands)")
    async def help(self, itx: discord.Interaction, page: int = FIRST_PAGE):
        await self.send_help_menu(itx, page)

    @app_commands.command(name="commands", description="A help command to learn more about me!")
    @app_commands.describe(page="What page do you want to jump to? (useful if sharing commands)")
    async def commands(self, itx: discord.Interaction, page: int = FIRST_PAGE):
        await self.send_help_menu(itx, page)


async def setup(client):
    await client.add_cog(HelpCommand(client))

from import_modules import *

class help_page(typing.TypedDict):
    title: str
    description: str
    fields: list[tuple[str,str]]

help_pages: dict[int, help_page] = {
    #region Default pages (home / index)
    1:{
        "title":"Rina's commands",
        "description": "Hey there. This is Rina. I'm a bot that does silly things for TransPlace and some linked servers. I'm being maintained by <@262913789375021056>.\n"
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
    },
    2:{
        "title":"Index",
        "description": "Here's a list of all the categories. You can use the :1234: button to quickly hop between these pages. Press :clipboard: to quickly go back to this index page.\n"
                       "\n"
                       ". . **1:** Welcome page\n"
                       ". . **2:** Index\n"
                       ". . **3:** Utility\n"
    },
    #endregion
    #region Expanded index pages (commands)
    3:{
        "title":"Utility",
        "description":"Some commands help in your daily life, like the following commands:\n"
                      "\n"
                      ". . **101:** roll\n"
                      ". . **103:** reminder\n"
                      ". . **104:** convert_unit\n"
                      ". . **105:** todo\n",
    },
    4:{
        "title":"null",
        "description":"null"
    },
    5:{
        "title":"null",
        "description":"null"
    },
    #endregion
    #region Utility commands
    101:{
        "title":"Rolling dice",
        "description":"Have you ever wanted to roll virtual dice? Now you can!\n"
                      "Rina lets you roll dice with many kinds of faces. Rolling a 2-faced die (aka, a coin)? sure!\n"
                      "\n"
                      "Because this command also allows an __advanced input__, go to the next page for more info: __**102**__\n",
        "fields":[
            (
                "Parameters",
                "`dice`: How many dice do you want to roll?\n"
                "- Any number between 1 and 999999\n"
                "`faces`: How many sides does every die have?\n"
                "- Any number between 1 and 999999\n"
                "`mod`: Do you want to add a modifier? (eg. add 2 after rolling the dice)\n"
                "- (optional) Any (negative) (decimal) number\n"
                "`advanced`: Roll more advanced! example: 1d20+3*2d4\n"
                "- (optional) String of your advanced dice roll."
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
    }
}
FIRST_PAGE = sorted(list(help_pages))[0]

assert sorted(list(help_pages)) == list(help_pages)

def replace_string_command_mentions(text: str, client: Bot) -> str:
    """
    Converts strings with "%%command%%" into a command mention (</command:12345678912345678>).

    Parameters:
    -----------
    text: :class:`str`
        The text in which to look for command mentions
    client: :class:`main.Bot`
        The client with which to convert the command into a command mention

    Returns:
    --------
    :class:`str`: The input text, with every command instance replaced with its matching command mention. Note: If the command does not exist, it will fill the mention with "/command" instead of "</command:1>"
    """
    while "%%" in text:
        command_start_index = text.index("%%")
        command_end_index = text.index("%%", command_start_index + 2)
        text = (text[:command_start_index] +
                client.get_command_mention(text[command_start_index + 2 : command_end_index]) +
                text[command_end_index + 2:])
    return text

def generate_help_page_embed(page: help_page, page_number: int, client: Bot) -> discord.Embed:
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

class JumpToPageModal_HelpCommands_Help(discord.ui.Modal, title="Go to help page"):
    def __init__(self, page_count, timeout=None):
        super().__init__()
        self.value = None # itx if valid input is given, else None
        self.timeout = timeout
        self.page = None # numeric input, or None if non-numeric input (can be out of range)
        self.page_count = page_count

        self.question_text = discord.ui.TextInput(label='What help page do you want to jump to?',
                                                  placeholder=f"2",
                                                  # style=discord.TextStyle.short, required=True
                                                  )
        self.add_item(self.question_text)

    async def on_submit(self, itx: discord.Interaction):
        if not self.question_text.value.isnumeric():
            await itx.response.send_message("Error: Invalid number.\n"
                                            "\n"
                                            "This button lets you jump to a help page (number). To see what kinds of help pages there are, go to the index page (page 2, or click the :clipboard: button).\n"
                                            "An example of a help page is page 3: `Utility`. To go to this page, you can either use the previous/next buttons (◀️ and ▶️) to navigate there, or click the 🔢 button: This button opens a modal.\n"
                                            "In this modal, you can put in the page number you want to jump to. Following from our example, if you type in '3', it will bring you to page 3; `Utility`.\n"
                                            "Happy browsing!", ephemeral=True)
            return
        else:
            self.page = int(self.question_text.value)

            if self.page not in self.page_indexes:
                if self.page > self.page_indexes[-1]:
                    relative_page_location_details = f" (nearest pages to `{self.page}` are `{self.page_indexes[-1]}` and `{self.page_indexes[0]}`)"
                elif self.page < self.page_indexes[0]:
                    relative_page_location_details = f" (nearest pages to `{self.page}` are `{self.page_indexes[0]}` and `{self.page_indexes[-1]}`)"
                else:
                    min_index = self.page
                    max_index = self.page
                    while min_index not in self.page_indexes:
                        min_index -= 1
                    while max_index not in self.page_indexes:
                        max_index += 1
                    relative_page_location_details = f" (nearest pages to `{self.page}` are `{min_index}` and `{max_index}`)"
                await itx.response.send_message(f"Error: Number invalid. Please go to a valid help page" + relative_page_location_details + ".", ephemeral=True)
                return

            #self.page = self.page-1 # turn page number into index number
        self.value = itx
        self.stop()

class PageView_HelpCommands_Help(discord.ui.View):
    def __init__(self, pages: dict[int, help_page], client: Bot, timeout: float=None):
        super().__init__()
        self.timeout = timeout
        self.page    = 1
        self.pages   = pages
        self.client = client

    async def update_page(self, itx: discord.Interaction):
        page_details = self.pages[self.page]

        embed = discord.Embed(color= discord.Color.from_hsv((180 + self.page*10)/360, 0.4, 1),
                              title=page_details["title"],
                              description=replace_string_command_mentions(page_details["description"], self.client))
        if "fields" in page_details:
            for field in page_details["fields"]:
                embed.add_field(name  = replace_string_command_mentions(field[0], self.client), 
                                value = replace_string_command_mentions(field[1], self.client), 
                                inline = False)
        embed.set_footer(text="page: "+str(self.page))

        await itx.response.edit_message(embed=embed)

    #region Buttons

    @discord.ui.button(emoji='📋', style=discord.ButtonStyle.gray) # index
    async def go_to_index(self, itx: discord.Interaction, _button: discord.ui.Button):
        self.page = 1 # page 2, but index 1
        await self.update_page(itx)

    @discord.ui.button(emoji='◀️', style=discord.ButtonStyle.blurple) # previous
    async def previous(self, itx: discord.Interaction, _button: discord.ui.Button):
        # get current page, find the index of it, subtract 1 from that index, and find the related page to match
        page_indexes = sorted(list(self.pages)) # sorting may be unnecessary, since it should already be sorted.
        current_page_index = page_indexes.index(self.page)
        if current_page_index - 1 < page_indexes[0]: # below lowest index
            self.page = page_indexes[-1] # set to highest index
        else:
            self.page = page_indexes[current_page_index - 1]

        await self.update_page(itx)

    @discord.ui.button(emoji='▶️', style=discord.ButtonStyle.blurple) # next
    async def next(self, itx: discord.Interaction, _button: discord.ui.Button):
        # get current page, find the index of it, add 1 to that index, and find the related page to match
        page_indexes = sorted(list(self.pages)) # sorting may be unnecessary, since it should already be sorted.
        current_page_index = page_indexes.index(self.page)
        if current_page_index + 1 > page_indexes[-1]: # above highest index
            self.page = page_indexes[0] # set to lowest index
        else:
            self.page = page_indexes[current_page_index + 1]

        await self.update_page(itx)

    @discord.ui.button(emoji='🔢', style=discord.ButtonStyle.gray) # go to page
    async def go_to_page(self, itx: discord.Interaction, _button: discord.ui.Button):
        jump_page_modal = JumpToPageModal_HelpCommands_Help(len(self.pages))
        await itx.response.send_modal(jump_page_modal)

        await jump_page_modal.wait()
        if jump_page_modal.value == None:
            pass
        else:
            self.page = jump_page_modal.page
            await self.update_page(jump_page_modal.value)

    #endregion Buttons


class HelpCommand(commands.Cog):
    def __init__(self, client: Bot):
        global RinaDB
        self.client = client
        RinaDB = client.RinaDB

    async def send_help_menu(self, itx: discord.Interaction, requested_page = FIRST_PAGE):
        embed = discord.Embed(color = discord.Color.from_hsv(180/360, 0.4, 1),
                              title = help_pages[requested_page]["title"],
                              description = replace_string_command_mentions(help_pages[1]["description"], self.client))
        if "fields" in help_pages[requested_page]:
            for field in help_pages[requested_page]["fields"]:
                embed.add_field(name  = replace_string_command_mentions(field[0], self.client),
                                value = replace_string_command_mentions(field[1], self.client),
                                inline = False)

        embed.set_footer(text = f"page: {requested_page}")

        await itx.response.send_message(embed = embed,
                                        view = PageView_HelpCommands_Help(help_pages, self.client),
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
    async def help(self, itx: discord.Interaction, page: int = 1):
        await self.send_help_menu(itx)

    @app_commands.command(name="commands", description="A help command to learn more about me!")
    async def commands(self, itx: discord.Interaction):
        await self.send_help_menu(itx)

async def setup(client):
    await client.add_cog(HelpCommand(client))
from extensions.help.helppage import HelpPage


# noinspection SqlNoDataSourceInspection
help_pages: dict[int, HelpPage] = {
    0: HelpPage(  # fallback default page
        title="Rina's fallback help page",
        description="""Hi there! This bot has a whole bunch of commands. Let me introduce you to some:
%%add_poll_reactions%%: Add an up-/down-vote emoji to a message (for voting)
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
""",
        fields=[],
        staff_only=False,
    ),
    # region Default pages (home / index)
    1: HelpPage(
        title="Rina's commands",
        description="Hey there. This is Rina. I'm a bot that does silly things for TransPlace and some linked servers. "
                    "I'm mostly being maintained by <@262913789375021056>.\n"
                    "I can do many things like looking up tone indicators or words, or sharing server info and "
                    "questions of the week. To share my commands, I've made this cool interactive menu.\n"
                    "\n"
                    "Use the buttons below to cycle through different categories of commands!\n"
                    "\n"
                    "📋 Index (page 2)\n"
                    "◀️ Previous page:\n"
                    "▶️ Next page: Index\n"
                    "🔢 Jump to page\n"
                    "\n"
                    "Do you have a cool bot idea? Use %%developer_request%% to suggest them to staff!",
        fields=[],
        staff_only=False,
    ),
    2: HelpPage(
        title="Index",
        description="Here's a list of all the categories. You can use the :1234: button to quickly hop "
                    "between these pages. Press :clipboard: to quickly go back to this index page.\n"
                    "\n"
                    ". . **1:** Welcome page\n"
                    ". . **2:** Index\n"
                    ". . **3:** Bot functions\n"  # 100
                    ". . **4:** Utility\n"  # 110
                    ". . **5:** Suggestion commands\n"  # 120
                    ". . **6:** Internet search commands\n"  # 130
                    ". . **7:** Server search commands\n"  # 140
                    ". . **8:** Chat actions\n"  # 150
                    ". . **9:** Server functions\n"  # 160
                    ". . **10:** Voice channels",  # 170
        fields=[],
        staff_only=False,
    ),
    # endregion

    # ### Bot functions:
    # #      add_poll_reactions, version, help, commands, get_rina_command_mention
    # ### Utility:
    # #      roll, convert_unit, reminders, todo
    # ### Suggestion commands:
    # #      qotw, developer_request
    # ### Internet search commands:
    # #      equaldex, math, dictionary, toneindicator (kinda not really API / internet but oh well)
    # ### Server search commands:
    # #      getemojidata, getunusedemojis, getemojitop10,
    # #      getstickerdata, getunusedstickers, getstickertop10,
    # #      getmemberdata, nameusage name/gettop
    # ### Chat actions:
    # #      abababa/awawawa, headpats, not cute, compliment, complimentblacklist
    # ### Server functions:
    # #      tags, remove_role
    # ### Voice channels:
    # #      editvc and vctable

    # region Expanded index pages (commands)
    3: HelpPage(  # index: Bot functions
        title="Bot functions",
        description="This section will list some simple rina-related commands that may help you:\n"
                    "\n"
                    ". . **101:** /help and /commands\n"
                    ". . **102:** version\n"
                    ". . **103:** get_rina_command_mention\n"
                    ". . **105:** add_poll_reactions\n",
        fields=[],
        staff_only=False,
    ),
    4: HelpPage(  # index: Utility
        title="Utility",
        description="Some commands help in your daily life, like the following commands:\n"
                    "\n"
                    ". . **111:** roll\n"
                    ". . **113:** reminder\n"
                    ". . **114:** convert_unit\n"
                    ". . **115:** todo\n",
        fields=[],
        staff_only=False,
    ),
    5: HelpPage(  # index: Suggestion commands
        title="Suggestion commands",
        description="Sometimes you just want to share your ideas with other people, you know?\b"
                    "\n"
                    ". . **121:** developer_request\n"
                    ". . **122:** qotw (question of the week)\n",
        fields=[],
        staff_only=False,
    ),
    6: HelpPage(  # index: Internet search commands
        title="Internet search commands",
        description="Googling is hard. That's why I made some searching commands!\b"
                    "\n"
                    ". . **131:** equaldex (LGBTQ laws in countries)\n"
                    ". . **132:** qotw (question of the week)\n",
        fields=[],
        staff_only=False,
    ),
    7: HelpPage(
        title="Work in progress...",
        description="This section is still being worked on! (help, so much text to write D: )\n"
                    "Scroll a few pages ahead to see what the rest of the help pages look like!",
        fields=[],
        staff_only=False,
    ),
    8: HelpPage(
        title="placeholder (skip ahead)",
        description="placeholder (skip ahead)",
        fields=[],
        staff_only=False,
    ),
    # endregion
    # region Bot Functions
    101: HelpPage(  # /help and /commands
        title="The help command and command list.",
        description="Obviously the most important command on the bot, this command attempts to explain "
                    "every command and function in the bot. This page will also be the first page "
                    "to show the layout of these commands.\n"
                    "\n"
                    "After running the command, Rina replies with an embed showing information about "
                    "the bot or command. There are interactable buttons to go back to start, jump to the "
                    "previous or next page, or jump to a specific page number. You can also provide a "
                    "`page ` argument to jump to a page immediately. Useful for sharing help command "
                    "pages.\n"
                    ""
                    "Running /help and /commands both bring up this embed.",
        fields=[
            (
                "Parameters",
                "`page`: The page to immediately jump to. Useful for sharing commands with other users.\n"
                "- (optional) Any number."
            ),
            (
                "Examples",
                "- %%help%%\n"
                "  - The simplest way to learn Rina's commands. Brings you to the first page.\n"
                "- %%help%% `page:1`\n"
                "  - brings up the help page for this /help command.\n"
                "- %%commands%% `page:3`\n"
                "  - An alias for this command. Brings you to the Bot Functions index page."
            )
        ],
        staff_only=False,
    ),
    102: HelpPage(  # /version
        title="Bot version",
        description="You can run %%version%% at any time. It will show you the bot's current "
                    "version and when it was started up. The message will only be visible for "
                    "you, unless you are a staff member.\n"
                    "This might someties also show that there is a new version available. Rina "
                    "will automatically update to it when she restarts.",
        fields=[
            (
                "Examples",
                "- %%version%%\n"
                "  - Gives Rina's current version, and if there is a newer version."
            )
        ],
        staff_only=False,
    ),
    103: HelpPage(  # get_rina_command_mention
        title="Sharing Rina's commands the cooler way :sunglasses:",
        description="Rina has a lot of commands, all in a big list. Other bots may also have "
                    "commands that are put in this same list.. Finding the right command "
                    "between all those /help commands with the same name can be quite "
                    "difficult.\n"
                    "\n"
                    "For that reason, this cool command lets you do things like -> %%help%% <- this "
                    "for Rina!\n"
                    "\n"
                    "On a technical level, all commands have a name and unique ID, like "
                    "so: `%%help%%`. Other bot commands with the same name have a different "
                    "ID. Mismatched IDs will autofill incorrect on Android, and try to run "
                    "a nonexisting command: </id_is_1234:1234> (`</id_is_1234:1234>`).",
        fields=[
            (
                "Parameters",
                "`command`: The command you want to convert into a cool mention.\n"
                "- The name of one of Rina's commands.\n"
                "- If it's an invalid command, rina will still give a response but it won't be in a mention format.\n"
            ),
            (
                "Examples",
                "- %%get_rina_command_mention%% `command:/version`\n"
                "  - Gives you the input, a mention preview, and a copyable mention.\n"
                "- %%get_rina_command_mention%% `command:add_poll_reactions`\n"
                "  - Gives you the command mention information for /add_poll_reactions.\n"
            )
        ],
        staff_only=False,
    ),
    104: HelpPage(  # /add_poll_reactions
        title="Adding voting emojis / Creating tiny polls",
        description="Sometimes you just want to see everyone's opinion on something, so you "
                    "add a thumbs up and thumbs down emoji to your message. But what if you "
                    "want to cast a vote yourself too? Rina's got you covered.\n"
                    "\n"
                    "This command lets you add between 2 and 3 emojis, allowing you to get "
                    "positive, negative, and neutral reactions. You can also run the command "
                    "again for even more emojis! Reuse a previous emoji if you only want to "
                    "add 1 new one.",
        fields=[
            (
                "Parameters",
                # /add_poll_reactions message_id: upvote_emoji: downvote_emoji: neutral_emoji:
                "`message_id`: The message to add emojis to.\n"
                "- A message ID. Right click a message and click \"Copy Message ID\". The command must be run in the "
                "same channel as this message.\n"
                "`upvote_emoji`: The first emoji to add to the message.\n"
                "- An emoji or emoji ID.\n"
                "`downvote_emoji`: The last emoji to add to the message.\n"
                "- An emoji or emoji ID.\n"
                "`neutral_emoji`: A middle emoji to add to the message. Will be added after the upvote but before "
                "the downvote emoji.\n"
                "- (optional) An emoji or emoji ID.\n"
            ),
            (
                "Examples",  # discord emojis don't work in code blocks :(, so gotta use unicode.
                "- %%add_poll_reactions%% `message_id:1963131994116722778` `upvote_emoji:🐟` `downvote_emoji:🐢`\n"
                "  - Adds a fish and then a turtle to a message with the id.\n"
                "- %%add_poll_reactions%% `message_id:1134140122115838003` "
                "`upvote_emoji:👍` `downvote_emoji:👎` `neutral_emoji:🤷`\n"
                "  - Adds a thumbs up, then a person shrugging, then a thumbs down emoji."
            )
        ],
        staff_only=False,
    ),
    # endregion
    # region Utility commands
    111: HelpPage(  # dice rolls
        title="Rolling dice",  # /roll
        description="Have you ever wanted to roll virtual dice? Now you can!\n"
                    "Rina lets you roll dice with many kinds of faces. Rolling a 2-faced die (aka, a coin)? sure!\n"
                    "\n"
                    "Because this command also allows an __advanced input__, go to the next page for "
                    "more info: __**102**__\n",
        fields=[
            (
                "Parameters",
                "`dice`: How many dice do you want to roll?\n"
                "- Any number between 1 and 999999.\n"
                "`faces`: How many sides does every die have?\n"
                "- Any number between 1 and 999999.\n"
                "`mod`: Do you want to add a modifier? (eg. add 2 after rolling the dice)\n"
                "- (optional) Any (negative) (decimal) number.\n"
                "`advanced`: Roll more advanced! example: 1d20+3*2d4\n"
                "- (optional) String of your advanced dice roll. See page __**102**__ for more info."
            ),
            (
                "Examples",
                "- %%roll%% `dice:3` `faces:6`\n"
                "  - Rolls 3 dice with 6 faces (3d6), aka rolling 3 normal dice.\n"
                "- %%roll%% `dice:6` `faces:2`\n"
                "  - Rolls 6 dice with 2 faces (6d2), aka flipping 6 coins.\n"
                "- %%roll%% `dice:3` `faces:2` `mod:4`\n"
                "  - Flip 3 coins, then add '4' to the final outcome.\n"
                "  - eg. 1 + 2 + 2 = 5 (3 dice with 2 faces), then add 4 to the final result = 5 + 4 = 9.\n"
                "- %%roll%% `dice:1` `faces:1` `advanced:help`\n"
                "  - See next page (__**102**__) for more information about advanced dice rolls."
            )
        ],
        staff_only=False,
    ),
    112: HelpPage(  # dice rolls advanced
        title="Advanced dice rolls",  # /roll advanced: ...
        description="In the case that the simple dice roll command is not enough, you can roll complexer combinations "
                    "of dice rolls using the advanced option.\n"
                    "The advanced mode lets you use addition, subtraction, multiplication, and custom dice.\n"
                    "To use the advanced function, you must give a value to the required parameters first ('dice' and "
                    "'faces') (the inserted value is ignored).\n"
                    "Supported characters are: `0123456789d+*-`. Spaces are ignored. Multiplication goes before "
                    "addition/subtraction.",
        fields=[
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
        ],
        staff_only=False,
    ),
    113: HelpPage(  # reminders
        title="Reminders",  # /reminder
        description="With this feature, you'll never forget your tasks anymore! (so long as Rina is online...).\n"
                    "This command lets you create, remove, and view your reminders.",
        fields=[
            (
                "reminder remindme",
                "- %%reminder remindme%% `time: ` `reminder: `\n"
                "`time`: When do you want to be reminded?\n"
                "- Use a format like 1mo10d9h8m7s for years/months/weeks/days/hours/min/sec.\n"
                # TODO: clarify; copy paste ValueError help message?
                "- Use a format like 2026-12-01 or 2026-12-01T15:43:23 for a reminder in December 2026.\n"
                "- Use a format like <t\\:01234567> or just 01234567 to use a Unix timestamp.\n"
                "`reminder`: What would you like to be reminded of?"
            ),
            (
                "reminder reminders",
                "- %%reminder reminders%% [`item: `]\n"
                "  - Show a list of active reminders. They each have a number. Use `item:number` to view more "
                "information about a specific reminder."
            ),
            (
                "reminder remove",
                "- %%reminder remove%% `item: `\n"
                "  - Remove a reminder. Use %%reminder reminders%% to see a list of reminders. Each has a number. "
                "Use that number to remove the reminder like so: `item:number`."
            )
        ],
        staff_only=False,
    ),
    114: HelpPage(  # convert unit
        title="Converting units",
        description="Since international communities often share stories about temperature and speed, it's not "
                    "uncommon to have to look up how many feet go in a centimeter. This module lets you easily "
                    "converty a large amount of units in multiple categories! Currencies are fetched live using "
                    "an online website (api)!\n"
                    "The units (`from` and `to_unit`) will autocomplete depending on the selected category.",
        fields=[
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
                "- %%convert_unit%% `mode:Length (miles,km,inch)` `from:meter` `value:80` `to_unit:yard`\n"
                "  - Convert 80 meters to yards = about 87.5 yd\n"
                ""
            )
        ],
        staff_only=False,
    ),
    115: HelpPage(  # to-do list
        title="Todo lists",
        description="For the forgetful, or if you just want a nice grocery list, this command is for you! You can "
                    "easily add and remove to-do notes, and they're saved throughout all servers with me "
                    "(TransPlace, EnbyPlace, Transonance, etc.)",
        fields=[
            (
                "Parameters",
                "`mode`: Do you want to __Add__, __Remove__, or __Check__ (view) your to-do list?\n"
                "- if you want to add to / remove from your to-do list, you must also give the `todo` value below.\n"
                "`todo`:\n"
                "- __Add__: What to-do would you like to add?\n"
                "- __Remove__: What to-do item would you like to remove from your list? Give the number of the to-do "
                "list as it's shown with %%todo%% `mode:Check`"
            ),
            (
                "Examples",
                "- %%todo%% `mode:Add something to your to-do list` `todo:Create a nice help command`\n"
                "  - Add \"Create a nice help command\"\n"
                "- %%todo%% `mode:Check`\n"
                "  - Your to-do list would look like this. Note how each item starts with a number. Use this number "
                "to remove them.\n"
                "    - Found 4 to-do items:\n"
                "    - `0`: Create a nice help command\n"
                "    - `1`: Share cool command with everyone\n"
                "- %%todo%% `mode:Remove to-do` `todo:0`\n"
                "  - Remove to-do item number 0 from your list. Use %%todo%% `mode:Check` to see what number to use "
                "to remove the right item.\n"
                "  - Keep in mind that the order will shift after you've removed an item, so redo the `check` command "
                "to make sure you're removing the right command when removing multiple to-do items at once!"
            )
        ],
        staff_only=False,
    ),
    # endregion
    # region Suggestion commands
    121: HelpPage(  # developer_request
        title="Send suggestions for bot developers!",
        description="If you ever have any suggestions or ideas for any bots, feel free "
                    "to use this command. This can include:\n"
                    "- Bigger features like starboard,\n"
                    "- Smaller features like a %%add_poll_reactions%%,\n"
                    "- Silly features like %%compliment%%,\n"
                    "- A spelling mistake of 1 mistyped character.\n"
                    "It doesn't have to be much :) so long as you explain your ideas "
                    "(or you would have to DM a staff member to give extra explanation).",
        fields=[
            (
                "Parameters",
                "`suggestion`: The idea you would like to share.\n"
                "- A message between 20 and 1500 characters. Try to be detailed so we can figure "
                "out what you want without having to ask for more details :)\n"
            ),
            (
                "Examples (real)",
                "- %%developer_request%% `suggestion:idea for rina: make tags just post the message directly "
                "into the channel instead of as a command follow-up so it doesn't show the \"message could "
                "not be loaded\" error :3`\n"
                "  - Sends a message to a developer channel on the staff server.\n"
                "- %%developer_request%% `suggestion:For Amari, make voice channels not give xp if someone is "
                "alone in a voice channel, to prevent people camping in vc alone (or falling asleep in vc) for xp`\n"
                "  - yeah, it does the thingy"
            )
        ],
        staff_only=False,
    ),
    122: HelpPage(  # qotw
        title="Questions of the week",
        description="You might have seen a Question of the Week pop up roughly once a week, \n"
                    "If you have any cool questions you want to ask to the server, feel free to ask them!\n"
                    "\n"
                    "Questions will be sent in a channel on the staff server, where we can vote, discuss, "
                    "or give suggestions. To give your questions a better chance of being picked, make "
                    "sure they can be answered by everyone.",
        fields=[
            (
                "Parameters",
                "`question`: The question you want to suggest.\n"
                " - A question of max 400 characters to propose to the staff server.\n"
            ),
            (
                "Examples",
                "- %%qotw%% `question:do you have a favourite flower or plant?`\n"
                "  - Sends your question to the staff team to vote :D\n"
                "- %%qotw%% `question:Should cleo make more qotws?`\n"
                "  - yes"
            )
        ],
        staff_only=False,
    ),
    # endregion
    # region Internet search commands
    131: HelpPage(  # equaldex
        title="Get LGBTQ laws from countries!",
        description="There's many countries in the world, and each has different "
                    "laws, of course. One website put these laws together and made "
                    "a nice overview for it :D. This command retrieves and shows you "
                    "some of their data.",
        fields=[
            (
                "Parameters",
                "`country_id`: The ID of the country you want to look up.\n"
                "- The short ID form of a country. Some examples: America: US, Germany: DE, Canada: CA\n"
                "- For more information, see [Wikipedia/ISO_3166#Officially_assigned_code_elements]"
                "(https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements)\n"
                "- It appears lowercase country codes don't work :p. So use uppercase: \"de\" vs \"DE\"."
            ),
            (
                "Examples",
                "- %%equaldex%% `country_id:GB`"
                "  - Get LGBTQ laws from Great Britain (United Kingdom).\n"
                "- %%equaldex%% `country_id:DE`"
                "  - DE for Germany, "
            )
        ],
        staff_only=False,
    )
    # endregion
}

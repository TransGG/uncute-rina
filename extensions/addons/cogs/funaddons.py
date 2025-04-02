import random  # for dice rolls (/roll) and selecting a random staff interaction wait time
from typing import TypeVar

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from resources.customs.bot import Bot

from extensions.settings.objects import ModuleKeys

STAFF_CONTACT_CHECK_WAIT_MIN = 5000
STAFF_CONTACT_CHECK_WAIT_MAX = 7500


T = TypeVar('T', int, float)


def _product_of_list(mult_list: list[T]) -> T:
    """
    Multiply all elements in a list.

    :param mult_list: The list to multiply.
    :return: The multiplied total.
    """
    a = 1
    for x in mult_list:
        a *= x
    return a


def _generate_roll(query: str) -> list[int]:
    """
    A helper command to generate a dice roll from a dice string representation "2d6"
    :param query: The string representing the dice roll.
    :return: A list of outcomes following from the dice roll. 2d6 will return a list with 2 integers, ranging from 1-6.
    """
    # print(query)
    temp: list[str | int] = query.split("d")
    # 2d4 = ["2","4"]
    # 2d3d4 = ["2","3","4"] (huh?)
    # 4 = 4
    # [] (huh?)
    if len(temp) > 2:
        raise ValueError("Can't have more than 1 'd' in the query of your die!")
    if len(temp) == 1:
        try:
            temp[0] = int(temp[0])
        except ValueError:
            raise TypeError(f"You can't do operations with '{temp[0]}'")
        return [temp[0]]
    if len(temp) < 1:
        raise ValueError(f"I couldn't understand what you meant with {query} ({str(temp)})")
    dice = temp[0]
    negative = dice.startswith("-")
    if negative:
        dice = dice.replace("-", "", 1)
    faces = ""
    for x in temp[1]:
        if x in "0123456789":
            faces += x
        else:
            break

    remainder = temp[1][len(faces):]  # (take the length of the now-still-string faces variable)
    if len(remainder) > 0:
        raise TypeError(f"Idk what happened, but you probably filled something in incorrectly:\n"
                        f"I parsed dice roll '{query}' into a roll of '{dice}' dice with '{faces}' faces, "
                        f"but got left with '{remainder}'. ({dice}d{faces} and {remainder})")

    try:
        dice = int(dice)
    except ValueError:
        raise ValueError(f"You have to roll a numerical number of dice! (You tried to roll '{dice}' dice)")
    try:
        faces = int(faces)
    except ValueError:
        raise TypeError(
            f"You have to roll a die with a numerical number of faces! (You tried to roll {dice} dice with "
            f"'{faces}' faces)")
    if dice >= 1000000:
        raise OverflowError(
            f"Sorry, if I let you roll `{dice:,}` dice, then the universe will implode, and Rina will stop "
            f"responding to commands. Please stay below 1 million dice...")
    if faces >= 1000000:
        raise OverflowError(
            f"Uh.. At that point, you're basically rolling a sphere. Even earth has fewer faces than `{faces:,}`. "
            f"Please bowl with a sphere of fewer than 1 million faces...")

    negativity: int = (negative * -2 + 1)  # turn a boolean 0 or 1 into a 1 or -1
    return [negativity * random.randint(1, faces) for _ in range(dice)]


async def _handle_awawa_reaction(client: Bot, message: discord.Message) -> bool:
    """
    Add headpats to a given message if its content is ababababa or awawawawawawawawa etc.
    :param client: The bot with server_settings.
    :param message: The message to check and add reactions to.
    :return: Whether the pat reaction is added.
    """
    # adding headpats on abababa or awawawawa
    msg_content = message.content.lower()
    emoji_str = "<:TPF_02_Pat:968285920421875744>"
    if len(msg_content) > 5 and (msg_content.startswith("aba") or msg_content.startswith("awa")):
        # check if the message content is /(ab|aw)+a/i
        replaced = msg_content.replace("ab", "").replace("aw", "")
        if replaced == "a":
            try:
                # todo attribute: Pat emoji ; also don't need the second message.add_reaction then.
                #  there is also an emoji lower.
                await message.add_reaction(emoji_str)
                return True
            except discord.errors.Forbidden:  # blocked rina :(, or just no perms
                pass

    if len(msg_content) > 9 and msg_content.startswith("a"):
        if any(char not in set("abw") for char in msg_content):
            return False

        try:
            await message.add_reaction(emoji_str)
            return True
        except discord.errors.Forbidden:  # blocked rina :(, or just no perms
            pass

    return False


class FunAddons(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        self.headpat_wait = 0
        self.rude_comments_opinion_cooldown = 0

    def handle_random_pat_reaction(self, message: discord.Message) -> bool:
        """
        A helper function to handle on_message events by users and randomly add a pat reaction to it.

        :param message: The message to (per chance) add a pat reaction to.

        :return: Whether a reaction was added to the message.
        """
        # adding headpats every x messages
        self.headpat_wait += 1
        if self.headpat_wait >= 1000:  # todo: do we want server-specific headpat times? if so, todo attribute: .
            # todo attribute: add headpat channel blacklist. Should also look if messages are in thread of this channel.
            #  Should also be able to be categories.
            if (
                    (type(message.channel) is discord.Thread and
                     message.channel.parent == 987358841245151262) or  # <#welcome-verify>
                    message.channel.name.startswith('ticket-') or
                    message.channel.name.startswith('closed-') or
                    message.channel.category.id in [959584962443632700, 959590295777968128,
                                                    959928799309484032, 1041487583475138692,
                                                    995330645901455380, 995330667665707108] or
                    # <#Bulletin Board>, <#Moderation Logs>,
                    # <#Verifier Archive>, <#Events>,
                    # <#Open Tickets>, <#Closed Tickets>
                    message.guild.id in [981730502987898960]  # don't send in Mod server
            ):
                pass
            else:
                self.headpat_wait = 0
                # TODO: re-enable code someday
                # people asked for no random headpats anymore; or make it opt-in. See GitHub #23
                # try:
                #     added_pat = True
                #     await message.add_reaction("<:TPF_02_Pat:968285920421875744>")  #headpatWait
                # except discord.errors.Forbidden:
                #     await log_to_guild(self.client, message.guild, f"**:warning: Warning: **Couldn\'t add pat "
                #                                                    f"reaction to {message.jump_url} (Forbidden): "
                #                                                    f"They might have blocked Rina...')
                # except discord.errors.HTTPException as ex:
                #     await log_to_guild(self.client, message.guild, f"**:warning: Warning: **Couldn\'t add pat "
                #                                                    f"reaction to {message.jump_url}. "
                #                                                    f"(HTTP/{ex.code}) "
                #                                                    f"They might have blocked Rina...')
                return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot:
            return

        added_pat = False
        if self.client.is_module_enabled(message.guild, ModuleKeys.headpat_reactions):
            added_pat = self.handle_random_pat_reaction(message)

        if not added_pat:
            await _handle_awawa_reaction(self.client, message)

    @app_commands.command(name="roll", description="Roll a die or dice with random chance!")
    @app_commands.describe(dice="How many dice do you want to roll?",
                           faces="How many sides does every die have?",
                           mod="Do you want to add a modifier? (add 2 after rolling the dice)",
                           advanced="Roll more advanced! example: 1d20+3*2d4. Overwrites dice/faces given; "
                                    "'help' for more")
    async def roll(
            self, itx: discord.Interaction,
            dice: app_commands.Range[int, 1, 999999],
            faces: app_commands.Range[int, 1, 999999],
            public: bool = False, mod: int | None = None, advanced: str | None = None
    ):
        hide = False
        if advanced is None:
            await itx.response.defer(ephemeral=not public)
            rolls = []
            for _ in range(dice):
                rolls.append(random.randint(1, faces))

            if mod is None:
                if dice == 1:
                    out = (f"I rolled {dice} die with {faces} face{'s' * (faces > 1)}: "
                           f"{str(sum(rolls))}")
                else:
                    out = (f"I rolled {dice} di{'c' * (dice > 1)}e with {faces} face{'s' * (faces > 1)}:\n"
                           f"{' + '.join([str(roll) for roll in rolls])}  =  {str(sum(rolls))}")
            else:
                out = (f"I rolled {dice} {'die' if dice == 0 else 'dice'} with {faces} face{'s' * (faces > 1)} "
                       f"and a modifier of {mod}:\n"
                       f"({' + '.join([str(roll) for roll in rolls])}) + {mod}  =  {str(sum(rolls) + mod)}")
            if len(out) > 300:
                out = (f"I rolled {dice:,} {'die' if dice == 0 else 'dice'} with {faces:,} face{'s' * (faces > 1)} "
                       f"and a modifier of {(mod or 0):,}") * (mod is not None) + \
                      (f":\n"
                       f"With this many numbers, I've simplified it a little. You rolled "
                       f"`{sum(rolls) + (mod or 0):,}`.")
                roll_db = {}
                for roll in rolls:
                    try:
                        roll_db[roll] += 1
                    except KeyError:
                        roll_db[roll] = 1
                # order dict by the eyes rolled: {"eyes":"count",1:4,2:1,3:4,4:1}
                # x.items() gives a list of tuples [(1,4), (2,1), (3,4), (4,1)] that is then sorted b
                # the first item in the tuple.
                roll_db = dict(sorted([x for x in roll_db.items()]))
                details = "You rolled "
                for roll in roll_db:
                    details += f"'{roll}'x{roll_db[roll]}, "
                if len(details) > 1500:
                    details = ""
                elif len(details) > 300:
                    hide = True
                out = out + "\n" + details
            elif len(out) > 300:
                hide = True
            if hide:
                await itx.delete_original_response()
            await itx.followup.send(out, ephemeral=not public)
        else:
            await itx.response.defer(ephemeral=not public)
            advanced = advanced.replace(" ", "")
            if advanced == "help":
                cmd_mention = itx.client.get_command_mention("help")
                await itx.response.send(
                    f"I don't think I ever added a help command... Ping mysticmia for more information about "
                    f"this command, or run {cmd_mention} `page:112` for more information.")

            for char in advanced:
                if char not in "0123456789d+*-":  # kKxXrR": #!!pf≤≥
                    if public:
                        await itx.delete_original_response()
                    await itx.followup.send(f"Invalid input! This command doesn't have support for '{char}' yet!",
                                            ephemeral=True)
                    return
            _add = advanced.replace('-', '+-').split('+')
            add = [add_section for add_section in _add if len(add_section) > 0]
            # print("add:       ",add)
            multiply = []
            for add_section in add:
                multiply.append(add_section.split('*'))
            # print("multiply:  ",multiply)
            try:
                result = [[sum(_generate_roll(query)) for query in mult_section] for mult_section in multiply]
            except (TypeError, ValueError, OverflowError) as ex:
                ex = repr(ex).split("(", 1)
                ex_type = ex[0]
                ex_message = ex[1][1:-1]
                if public:
                    await itx.delete_original_response()
                await itx.followup.send(f"Wasn't able to roll your dice!\n  {ex_type}: {ex_message}", ephemeral=True)
                return
            # print("result:    ",result)
            out = ["Input:  " + advanced]
            if "*" in advanced:
                out += [' + '.join([' * '.join([str(x) for x in section]) for section in result])]
            if "+" in advanced or '-' in advanced:
                out += [' + '.join([str(_product_of_list(section)) for section in result])]
            out += [str(sum([_product_of_list(section) for section in result]))]
            output = discord.utils.escape_markdown('\n= '.join(out))
            if len(output) >= 1950:
                output = ("Your result was too long! I couldn't send it. Try making your rolls a bit smaller, "
                          "perhaps by splitting it into multiple operations...")
            if len(output) >= 500:
                hide = True
            try:
                await itx.followup.send(output, ephemeral=not public)
            except discord.errors.NotFound:
                if hide:
                    await itx.delete_original_response()
                await itx.user.send(f"Couldn't send you the result of your roll because it took too long "
                                    f"or something. Here you go: \n{output}")

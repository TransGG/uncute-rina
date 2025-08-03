import random
import typing
# ^ for dice rolls (/roll) and selecting a random staff
#  interaction wait time
from typing import TypeVar

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.addons.roll import generate_roll
from resources.checks import MissingAttributesCheckFailure
from resources.customs import Bot, GuildMessage

from extensions.settings.objects import ModuleKeys, AttributeKeys

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


async def _handle_awawa_reaction(
        message: discord.Message, awawawa_emoji: discord.Emoji,
) -> bool:
    """
    Add an emoji to a given message if its content is ababababa or
    awawawawawawawawa etc.

    :param message: The message to check and add reactions to.
    :return: Whether the pat reaction is added.
    """
    # adding headpats on abababa or awawawawa
    msg_content = message.content.lower()

    if len(msg_content) > 5 and (msg_content.startswith("aba")
                                 or msg_content.startswith("awa")):
        # check if the message content is /(ab|aw)+a/i
        replaced = msg_content.replace("ab", "").replace("aw", "")
        if replaced == "a":
            try:
                await message.add_reaction(awawawa_emoji)
                return True
            except discord.errors.Forbidden:
                # user blocked rina :(, or just no perms
                pass

    if len(msg_content) > 9 and msg_content.startswith("a"):
        if any(char not in set("abw") for char in msg_content):
            return False

        try:
            await message.add_reaction(awawawa_emoji)
            return True
        except discord.errors.Forbidden:  # blocked rina :(, or just no perms
            pass

    return False


async def _get_dice_roll_output(dice, faces, mod):
    """Helper to get the text output for a simple /roll."""
    rolls = []
    message_too_long = False
    for _ in range(dice):
        rolls.append(random.randint(1, faces))
    dice_info = (f"I rolled {dice:,} di{'c' * (dice != 1)}e with "
                 f"{faces:,} face{'s' * (faces > 1)}")
    modifier_info = ""
    if mod is None:
        if dice == 1:
            out = f": {str(sum(rolls))}"
        else:
            out = (f":\n"
                   f"{' + '.join([str(roll) for roll in rolls])}  =  "
                   f"{str(sum(rolls))}")
    else:
        modifier_info = f" and a modifier of {mod}"
        out = (f":\n"
               f"({' + '.join([str(roll) for roll in rolls])}) + {mod}  =  "
               f"{str(sum(rolls) + mod)}")
    if len(dice_info) + len(out) > 300:
        out = (f":\n"
               f"With this many numbers, I've simplified it a little. "
               f"You rolled `{sum(rolls) + (mod or 0):,}`.")
        details = await _simplify_roll_output(rolls)
        if len(details) > 1500:
            details = ""
        elif len(details) > 300:
            message_too_long = True
        out += "\n" + details
    elif len(out) > 300:
        message_too_long = True
    output_string = dice_info + modifier_info + out
    return output_string, message_too_long


async def _simplify_roll_output(rolls: list[int]) -> str:
    """Helper to represent dice rolls into (eyes, count) entries."""
    roll_db = {}
    for roll in rolls:
        try:
            roll_db[roll] += 1
        except KeyError:
            roll_db[roll] = 1
    # order dict by the eyes rolled: {"eyes":"count",1:4,2:1,3:4,4:1}
    # x.items() gives a list of tuples [(1,4), (2,1), (3,4), (4,1)]
    #  that is then sorted by the first item in the tuple.
    roll_db = sorted([x for x in roll_db.items()])
    details = "You rolled "
    for roll, count in roll_db:
        details += f"'{roll}'x{count}, "
    return details


class FunAddons(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        self.headpat_wait = 0
        self.rude_comments_opinion_cooldown = 0

    def handle_random_pat_reaction(
            self, message: GuildMessage, headpat_emoji: discord.Emoji
    ) -> bool:
        """
        A helper function to handle on_message events by users
        and randomly add a pat reaction to it.

        :param message: The message to (per chance) add a pat reaction to.
        :param headpat_emoji: The emoji to add to the message.

        :return: Whether a reaction was added to the message.
        """
        channel_name = getattr(message.channel, "name", None)
        channel_category = getattr(message.channel, "category", None)

        # adding headpats every x messages
        self.headpat_wait += 1
        if self.headpat_wait >= 1000:
            # todo: do we want server-specific headpat times?
            # todo attribute: add headpat channel blacklist. Should also
            #  look if messages are in thread of this channel. Should
            #  also be able to be categories.
            if (
                    (type(message.channel) is discord.Thread
                     and message.channel.parent == 987358841245151262)
                    # ^ <#welcome-verify>
                    or channel_name is None
                    or channel_name.startswith('ticket-')
                    or channel_name.startswith('closed-')
                    or channel_category is None
                    # <#Bulletin Board>, <#Moderation Logs>,
                    # <#Verifier Archive>, <#Events>,
                    # <#Open Tickets>, <#Closed Tickets>
                    or channel_category.id in [
                        959584962443632700, 959590295777968128,
                        959928799309484032, 1041487583475138692,
                        995330645901455380, 995330667665707108
                    ]
                    or message.guild.id in [981730502987898960]
                    # ^ don't send in Mod server
            ):
                return False

            self.headpat_wait = 0
            # TODO: re-enable code someday
            #  people asked for no random headpats anymore; or make it
            #  opt-in. See GitHub #23

            # try:
            #     added_pat = True
            #     await message.add_reaction(headpat_emoji)  #headpatWait
            # except discord.errors.Forbidden:
            #     await log_to_guild(
            #         self.client,
            #         message.guild,
            #         f"**:warning: Warning: **Couldn\'t add pat "
            #         f"reaction to {message.jump_url} (Forbidden): "
            #         f"They might have blocked Rina..."
            #     )
            # except discord.errors.HTTPException as ex:
            #     await log_to_guild(
            #         self.client,
            #         message.guild,
            #         f"**:warning: Warning: **Couldn\'t add pat "
            #         f"reaction to {message.jump_url}. "
            #         f"(HTTP/{ex.code}) "
            #         f"They might have blocked Rina..."
            #     )
            # return True

        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if self.client.is_module_enabled(
                message.guild, ModuleKeys.headpat_reactions):
            message = typing.cast(GuildMessage, message)
            headpat_emoji: discord.Emoji | None
            headpat_emoji = self.client.get_guild_attribute(
                message.guild, AttributeKeys.headpat_emoji)
            if headpat_emoji is None:
                raise MissingAttributesCheckFailure(
                    ModuleKeys.headpat_reactions,
                    [AttributeKeys.headpat_emoji])
            self.handle_random_pat_reaction(message, headpat_emoji)
            return

        if self.client.is_module_enabled(
                message.guild, ModuleKeys.awawawa_reactions):
            awawawa_emoji: discord.Emoji | None
            awawawa_emoji = self.client.get_guild_attribute(
                message.guild, AttributeKeys.awawawa_emoji)
            if awawawa_emoji is None:
                raise MissingAttributesCheckFailure(
                    ModuleKeys.awawawa_reactions,
                    [AttributeKeys.awawawa_emoji])
            await _handle_awawa_reaction(message, awawawa_emoji)

    @app_commands.command(name="roll",
                          description="Roll a die or dice with random chance!")
    @app_commands.describe(
        dice="How many dice do you want to roll?",
        faces="How many sides does every die have?",
        mod="Do you want to add a modifier? (add 2 after rolling the dice)",
        advanced="Roll more advanced! example: 1d20+3*2d4. Overwrites "
                 "dice/faces given; 'help' for more"
    )
    async def roll(
            self,
            itx: discord.Interaction[Bot],
            dice: app_commands.Range[int, 1, 999999],
            faces: app_commands.Range[int, 1, 999999],
            public: bool = False,
            mod: int | None = None,
            advanced: str | None = None,
    ):
        itx.response: discord.InteractionResponse[Bot]  # type: ignore

        if advanced is None:
            await itx.response.defer(ephemeral=not public)
            out, too_long = await _get_dice_roll_output(
                dice, faces, mod)
            if too_long:
                await itx.delete_original_response()
            await itx.followup.send(out, ephemeral=too_long)
        else:
            await itx.response.defer(ephemeral=not public)
            advanced = advanced.replace(" ", "")
            if advanced == "help":
                cmd_help = itx.client.get_command_mention_with_args(
                    "help", page="112")
                await itx.response.send_message(
                    f"I don't think I ever added a help command... Ping "
                    f"mysticmia for more information about this command, or "
                    f"run {cmd_help} for more information."
                )

            for char in advanced:
                if char not in "0123456789d+*-":  # kKxXrR": #!!pf≤≥
                    if public:
                        await itx.delete_original_response()
                    await itx.followup.send(
                        f"Invalid input! This command doesn't have "
                        f"support for '{char}' yet!",
                        ephemeral=True,
                    )
                    return
            _add = advanced.replace('-', '+-').split('+')
            add = [add_section for add_section in _add if len(add_section) > 0]
            # print("add:       ",add)
            multiply = []
            for add_section in add:
                multiply.append(add_section.split('*'))
            # print("multiply:  ",multiply)
            try:
                result = [[sum(generate_roll(query))
                           for query in mult_section]
                          for mult_section in multiply]
            except (TypeError, ValueError, OverflowError) as ex:
                ex_type = ex.__class__.__name__
                if public:
                    await itx.delete_original_response()
                await itx.followup.send(
                    f"Wasn't able to roll your dice!\n"
                    f"  {ex_type}: {ex}",
                    ephemeral=True,
                )
                return
            # print("result:    ",result)
            out = ["Input:  " + advanced]
            if "*" in advanced:
                out += [' + '.join([' * '.join([str(x) for x in section])
                                    for section in result])]
            if "+" in advanced or '-' in advanced:
                out += [' + '.join([str(_product_of_list(section))
                                    for section in result])]
            out += [str(sum([_product_of_list(section)
                             for section in result]))]
            output = discord.utils.escape_markdown('\n= '.join(out))
            if len(output) >= 1950:
                output = ("Your result was too long! I couldn't send it. "
                          "Try making your rolls a bit smaller, perhaps by "
                          "splitting it into multiple operations...")
            if len(output) >= 500:
                public = False
            try:
                await itx.followup.send(output, ephemeral=not public)
            except discord.errors.NotFound:
                if public:
                    await itx.delete_original_response()
                await itx.user.send(
                    f"Couldn't send you the result of your roll because "
                    f"it took too long or something. Here you go: \n"
                    f"{output}"
                )

import json  # to read API json responses
import random  # for dice rolls (/roll) and selecting a random staff interaction wait time
import requests  # to read api calls

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from resources.customs.bot import Bot
from resources.utils.utils import log_to_guild  # to log add_poll_reactions

from extensions.addons.equaldexregion import EqualDexRegion
from extensions.addons.views.equaldex_additionalinfo import EqualDexAdditionalInfo
from extensions.addons.views.math_sendpublicbutton import SendPublicButtonMath


STAFF_CONTACT_CHECK_WAIT_MIN = 5000
STAFF_CONTACT_CHECK_WAIT_MAX = 7500

def _product_in_list(mult_list: list):
    a = 1
    for x in mult_list:
        a *= x
    return a


def _generate_roll(query: str) -> list[int]:
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
    if len(remainder) > 0:
        raise TypeError("Idk what happened, but you probably filled something in incorrectly.")
    if dice >= 1000000:
        raise OverflowError(
            f"Sorry, if I let you roll `{dice:,}` dice, then the universe will implode, and Rina will stop "
            f"responding to commands. Please stay below 1 million dice...")
    if faces >= 1000000:
        raise OverflowError(
            f"Uh.. At that point, you're basically rolling a sphere. Even earth has fewer faces than `{faces:,}`. "
            f"Please bowl with a sphere of fewer than 1 million faces...")

    return [(negative * -2 + 1) * random.randint(1, faces) for _ in range(dice)]


class FunAddons(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        self.headpat_wait = 0
        self.staff_contact_check_wait = random.randint(STAFF_CONTACT_CHECK_WAIT_MIN, STAFF_CONTACT_CHECK_WAIT_MAX)
        self.rude_comments_opinion_cooldown = 0

    def handle_random_pat_reaction(self, message: discord.Message) -> bool:
        """
        A helper function to handle on_message events by users and randomly add a pat reaction to it.

        Parameters
        ----------
        message :class:`discord.Message`
            The message to (per chance) add a pat reaction to.

        Returns
        -------
        :class:`bool`:
            Whether a reaction was added to the message.
        """
        # adding headpats every x messages
        self.headpat_wait += 1
        if self.headpat_wait >= 1000:
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
                #     await message.add_reaction("<:TPF_02_Pat:968285920421875744>") #headpatWait
                # except discord.errors.Forbidden:
                #     await log_to_guild(self.client, message.guild, f'**:warning: Warning: **Couldn\'t add pat "
                #                                                    f"reaction to {message.jump_url} (Forbidden): "
                #                                                    f"They might have blocked Rina...')
                # except discord.errors.HTTPException as ex:
                #     await log_to_guild(self.client, message.guild, f'**:warning: Warning: **Couldn\'t add pat "
                #                                                    f"reaction to {message.jump_url}. "
                #                                                    f"(HTTP/{ex.code}) "
                #                                                    f"They might have blocked Rina...')
                return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        added_pat = False
        if not message.author.bot:
            added_pat = self.handle_random_pat_reaction(message)

        # adding headpats on abababa or awawawawa
        msg_content = message.content.lower()
        if not added_pat and len(msg_content) > 5 and (msg_content.startswith("aba") or msg_content.startswith("awa")):
            msg_content = msg_content.replace("ab", "").replace("aw", "")
            if msg_content == "a":
                try:
                    added_pat = True
                    await message.add_reaction("<:TPF_02_Pat:968285920421875744>")
                except discord.errors.Forbidden:  # blocked rina :(
                    pass
                except discord.errors.HTTPException as ex:
                    if ex.code == 10014:  # bad request (emoji doesnt exist: cause it's dev testing environment)
                        await message.add_reaction("☺")  # :relaxed:
                    else:
                        raise
        if not added_pat and len(msg_content) > 9 and msg_content.startswith("a"):
            for char in msg_content:
                if char not in "abw":
                    break
            else:
                try:
                    added_pat = True
                    await message.add_reaction("<:TPF_02_Pat:968285920421875744>")
                except discord.errors.Forbidden:  # blocked rina :(
                    pass
                except discord.errors.HTTPException as ex:
                    if ex.code == 10014:  # bad request (emoji doesnt exist: cause it's dev testing environment)
                        await message.add_reaction("☺")  # :relaxed:
                    else:
                        raise

        if message.author.bot:
            return

        # embed "This conversation was powered by friendship" every x messages # TODO: re-enable code someday
        if False:  # (self.staff_contact_check_wait == 0 or
            #     (self.staff_contact_check_wait < -10 and  # make sure it only sends once (and <-10 for backup)
            #      self.staff_contact_check_wait % 6 == 0)):
            if message.channel.id in [960920453705257061, 999165241894109194, 999165867625566218, 999167335938150410]:
                # TransPlace [general, trans masc treehouse, trans fem forest, enby enclave]
                # TODO: when cleo adds "report" func to EnbyPlace (or other servers in general),
                #  add those server's channel IDs too.

                if message.guild.id == self.client.custom_ids.get("enbyplace_server_id"):
                    mod_ticket_channel_id = 1186054373986537522
                elif message.guild.id == self.client.custom_ids.get("transonance_server_id"):
                    mod_ticket_channel_id = 1108789589558177812
                else:  # elif context.guild_id == client.custom_ids.get("transplace_server_id"):
                    mod_ticket_channel_id = 995343855069175858
                cmd_mention = self.client.get_command_mention("tag")

                options = [
                    "This conversation was powered by friendship.",
                    "This conversation was brought to you by the mods' dwindling patience.",
                    "This conversation was brought to you by **emotional damage**!"
                    "This conversation was powdered by friendship and glitter.",
                    "This conversation was brought to you by trans rights"
                    "This conversation was brought to you by the dwindling patience of the mods.",
                    "This conversation has been trying to reach you about your car's extended warranty.",
                    "This conversation was sponsored by Raid Shadow Legends, one of the biggest mobile role-"
                    "playing gam...",
                    "This conversation was sponsored by Spotify; Want a break from the ads?",
                    "This conversation was sponsored by Homestuck",
                    "This conversation was brought to you by Flex Seal! To show the power of Flex Tape, I sawed "
                    "this boat in half!",
                    "Want to advertise? Call 0900 0000 to place an AD!",
                    "Do you have suggestions for what to place here? Ping mysticmia and share!",
                    "1",  # "Fun fact: ",
                ]
                superpower = random.choice(options)

                if superpower == "1":
                    response = requests.get('https://api.api-ninjas.com/v1/facts?limit=1', headers={
                        # These were headers that were in the browser testing api, but apparently I
                        # only need this one to make it work lol
                        "Origin": "https://api-ninjas.com",
                        # "X-Api-Key": "YOUR_API_KEY",
                        # "Host": "api.api-ninjas.com",
                        # "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 "
                        #               "Firefox/123.0",
                        # "Accept": "*/*",
                        # "Accept-Language": "en-US,en;q=0.5",
                        # "Accept-Encoding": "gzip, deflate, br",
                        # "Referer": "https://api-ninjas.com/",
                        # "Connection": "keep-alive",
                        # "Sec-Fetch-Dest": "empty",
                        # "Sec-Fetch-Mode": "cors",
                        # "Sec-Fetch-Site": "same-site",
                        # "Sec-GPC": "1",
                        # "TE": "trailers"
                    }).json()[0]["fact"]
                    starter = random.choice(["This conversation is cool and all, but did you know ", "Fun fact: "])
                    response = starter + response[0].lower() + response[1:]
                    # make first letter lowercase, so it fits with the rest of the sentence
                    if len(response) > 256:  # embed title length limit is 256 chars.
                        header = options[0]
                    else:
                        header = response
                else:
                    header = superpower

                embed = discord.Embed(
                    color=discord.Color.from_hsv(205 / 360, 65 / 100, 100 / 100),
                    title=header,
                    description=f"See someone breaking the rules? Unsure about a situation? You can always "
                                f"contact staff! Reach us in <#{mod_ticket_channel_id}>, or report a user/message "
                                f"with our bot (more info: {cmd_mention} `tag:report`) (Gives staff a bit more "
                                f"context :). You may always ping/dm a staff member or Moderators if necessary."
                )
                await message.channel.send(embed=embed)
                self.staff_contact_check_wait = random.randint(STAFF_CONTACT_CHECK_WAIT_MIN,
                                                               STAFF_CONTACT_CHECK_WAIT_MAX)
        self.staff_contact_check_wait -= 1

        # give opinion on people hating on rina
        self.rude_comments_opinion_cooldown -= 1
        if self.rude_comments_opinion_cooldown < 0:
            if self.client.user.id in [user.id for user in message.mentions]:
                if (":" in message.content and
                        "middlefinger" in message.content.lower().replace(" ", "")):
                    await message.reply("That's kind of rude... Why would you do that?")
                    self.rude_comments_opinion_cooldown = STAFF_CONTACT_CHECK_WAIT_MIN * 8

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
                # x.items() gives a list of tuples [(1,4),(2,1),(3,4),(4,1)] that is then sorted b
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
                cmd_mention = self.client.get_command_mention("help")
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
            add = [section for section in _add if len(section) > 0]
            # print("add:       ",add)
            multiply = []
            for section in add:
                multiply.append(section.split('*'))
            # print("multiply:  ",multiply)
            try:
                result = [[sum(_generate_roll(query)) for query in section] for section in multiply]
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
                out += [' + '.join([str(_product_in_list(section)) for section in result])]
            out += [str(sum([_product_in_list(section) for section in result]))]
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

import random
import typing

# ^ random compliment from list, random user pronouns from their role
#  list, and random keyboard mash.

import motor.core

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.settings.objects import ModuleKeys
from resources.checks.command_checks import module_not_disabled_check
from resources.customs import Bot
from resources.utils.utils import log_to_guild
# ^ to warn when bot can't add headpat reaction (typically because
#  user blocked Rina)

from extensions.compliments.views import ConfirmPronounsView


async def _choose_and_send_compliment(
        itx: discord.Interaction[Bot],
        user: discord.User | discord.Member,
        compliment_type: str,
        async_rina_db: motor.core.AgnosticDatabase
):
    # todo: split function into multiple functions
    quotes = {
        "fem_quotes": [
            # "Was the sun always this hot? or is it because of you?",
            # "Hey baby, are you an angel? Cuz I’m allergic to feathers.",
            # "I bet you sweat glitter.",
            "Your hair looks stunning!",
            "Being around you is like being on a happy little vacation.",
            "Good girll",
            "Who's a good girl?? You are!!",
            "Amazing! Perfect! Beautiful! How **does** she do it?!",
            "I can tell that you are a very special and talented girl!",
            "Here, have this cute sticker!",
            ("Beep boop :zap: Oh no! my circuits overloaded! Her cuteness was "
             "too much for me to handle!"),
        ],
        "masc_quotes": [
            "You are the best man out there.",
            "You are the strongest guy I know.",
            "You have an amazing energy!",
            "You seem to know how to fix everything!",
            "Waw, you seem like a very attractive guy!",
            "Good boyy!",
            "Who's a cool guy? You are!!",
            "I can tell that you are a very special and talented guy!",
            "You're such a gentleman!",
            "You always know how to make people feel welcome and included :D",
            "Your intelligence and knowledge never cease to amaze me :O",
            ("Beep boop :zap: Oh no! my circuits overloaded! His aura was so "
             "strong that I couldn't generate a cool compliment!"),
        ],
        "they_quotes": [
            "I can tell that you are a very special and talented person!",
            "Their, their... ",
        ],
        "it_quotes": [
            "I bet you do the crossword puzzle in ink!",
        ],
        "unisex_quotes": [
            # unisex quotes are added to each of the other quotes later on.
            "Hey I have some leftover cookies.. \\*wink wink\\*",
            # "_Let me just hide this here-_ hey wait, are you looking?!",
            # ^ it was meant to be cookies TwT
            "Would you like a hug?",
            # ("Would you like to walk in the park with me? I gotta walk"
            #  " my catgirls"),
            # ^ got misinterpreted too
            "morb",
            "You look great today!",
            "You light up the room!",
            "On a scale from 1 to 10, you’re an 11!",
            'When you say, “I meant to do that,” I totally believe you.',
            "You should be thanked more often. So thank you!",
            "You are so easy to have a conversation with!",
            "Ooh you look like a good candidate to give my pet blahaj to!",
            "Here, have a sticker!",
            "You always know how to put a positive spin on things!",
            "You make the world a better place just by being in it",
            "Your strength and resilience is truly inspiring.",
            ("You have a contagious positive attitude that lifts up "
             "those around you."),
            ("Your positive energy is infectious and makes everyone "
             "feel welcomed!"),
            ("You have a great sense of style and always look so put "
             "together <3"),
            "You are a truly unique and wonderful person!",
        ]
    }
    compliment_type = {
        "she/her": "fem_quotes",
        "he/him": "masc_quotes",
        "they/them": "they_quotes",
        "it/its": "it_quotes",
        "unisex": "unisex_quotes",
    }[compliment_type]

    for x in quotes:
        if x == "unisex_quotes":
            continue
        else:
            quotes[x] += quotes["unisex_quotes"]

    collection = async_rina_db["complimentblacklist"]  # todo: use DatabaseKeys
    query = {"user": user.id}
    search: dict[str, int | list] = await collection.find_one(query)
    blacklist: list = []
    if search is not None:
        try:
            blacklist += search["list"]
        except KeyError:
            pass
    query = {"user": itx.user.id}

    search = await collection.find_one(query)
    if search is not None:
        try:
            blacklist += search["personal_list"]
        except KeyError:
            pass

    for string in blacklist:
        dec = 0
        for x in range(len(quotes[compliment_type])):
            if string in quotes[compliment_type][x - dec]:
                del quotes[compliment_type][x - dec]
                dec += 1
    if len(quotes[compliment_type]) == 0:
        quotes[compliment_type].append(
            "No compliment quotes could be given... You and/or this person "
            "have blacklisted every quote."
        )

    base = f"{itx.user.mention} complimented {user.mention}!\n"
    # cmd_mention = client.get_command_mention("developer_request")
    # cmd_mention1 = client.get_command_mention("complimentblacklist")
    suffix = ""  # (
    #     f"\n\nPlease give suggestions for compliments! DM "
    #     f"<@262913789375021056>, make a staff ticket, or use {cmd_mention} "
    #     f"to suggest one. Do you dislike this compliment? Use "
    #     f"{cmd_mention1} `location:being complimented` `mode:Add` "
    #     f"`string: ` and block specific words (or the letters \"e\" and "
    #     f"\"o\" to block every compliment"
    # )
    if itx.response.is_done():  # todo: add "give compliment back" button
        # should happen if user used the modal to select a pronoun role
        try:
            # todo: make a util function to "send or followup")
            await itx.channel.send(
                content=base + random.choice(quotes[compliment_type]) + suffix,
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, users=[user], roles=False,
                    replied_user=False)
            )
        except discord.Forbidden:
            # can't send in channel, follow up to interaction instead.
            await itx.followup.send(
                content=base + random.choice(quotes[compliment_type]) + suffix,
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, users=[user], roles=False,
                    replied_user=False)
            )
    else:
        await itx.response.send_message(
            base + random.choice(quotes[compliment_type]) + suffix,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=[user], roles=False, replied_user=False)
        )


async def _send_confirm_gender_modal(
        client: Bot,
        itx: discord.Interaction[Bot],
        user: discord.User | discord.Member
) -> None:
    # Define a simple View that gives us a confirmation menu
    view = ConfirmPronounsView(timeout=60)
    await itx.response.send_message(
        f"{user.mention} doesn't have any pronoun roles! Which pronouns "
        f"would like to use for the compliment?",
        view=view, ephemeral=True)
    await view.wait()
    if view.value is None:
        await itx.edit_original_response(content=':x: Timed out...', view=None)
    else:
        await _choose_and_send_compliment(itx, user, view.value,
                                          client.async_rina_db)


async def _rina_used_deflect_and_it_was_very_effective(
        message: discord.Message
) -> None:
    """
    Rina's secret superpower: deflecting compliments :>. Don't
    question it.

    :param message: The message to analyze for compliment
     reflection purposes.
    """
    responses = [
        "I'm not cute >_<",
        "I'm not cute! I'm... Tough! Badass!",
        "Nyaa~",
        "Who? Me? No you're mistaken.",
        "I very much deny the cuteness of someone like myself",
        "I don't think so.",
        "Haha. Good joke. Tell me another tomorrow",
        "No, I'm !cute.",
        ("[shocked] Wha- w. .. w what?? .. NOo? no im nott?\nwhstre you "
         "tslking about?"),
        ("Oh you were talking to me? I thought you were talking about "
         "everyone else here,"),
        "Maybe.. Maybe I am cute.",
        "If the sun was dying, would you still think I was cute?",
        "Awww. Thanks sweety, but you've got the wrong number",
        ":joy: You *reaaally* think so? You've gotta be kidding me.",
        ("If you're gonna be spamming this, .. maybe #general isn't the "
         "best channel for that."),
        ("Such nice weather outside, isn't it? What- you asked me a "
         "question?\nNo you didn't, you're just talking to yourself."),
        ("".join(random.choice("acefgilrsuwnop" * 3 + ";;  " * 2)
                 for _ in range(random.randint(10, 25)))),
        # 3:2 letters to symbols
        ("Oh I heard about that! That's a way to get randomized passwords "
         "from a transfem!"),
        ("Cuties are not gender-specific. For example, my cat is a cutie!\n"
         "Oh wait, species aren't the same as genders. Am I still a catgirl "
         "then? Trans-species?"),
        "...",
        "Hey that's not how it works!",
        "Hey my lie detector said you are lying.",
        "No I am not cute",
        "k",
        (message.author.nick or message.author.name) + ", stop lying >:C",
        "BAD!",
        ("https://cdn.discordapp.com/emojis/920918513969950750.webp"
         "?size=4096&quality=lossless"),
        ("[Checks machine]; Huh? Is my lie detector broken? I should "
         "fix that.."),
    ]
    femme_responses = [
        "If you think I'm cute, then you must be uber-cute!!",
        "Ehe, cutie what do u need help with?",
        "You too!",
        "No, you are <3",
        "Nope. I doubt it. There's no way I can be as cute as you",
        ("You gotta praise those around you as well. "
         + (message.author.nick or message.author.name)
         + ", for example, is very cute."),
        ("Oh by the way, did I say "
         + (message.author.nick or message.author.name)
         + " was cute yet? I probably didn't. "
         + (message.author.nick or message.author.name)
         + "? You're very cute"),
        "You know I'm not a mirror, right?",
        "*And the oscar for cutest responses goes to..  YOU!!*",
        "You're also part of the cuties set",
        ("Hey, you should be talking about yourself first! After all, how do "
         "you keep up with being such a cutie all the time?")
    ]
    # check if user would like femme responses telling them they're cute
    for role in message.author.roles:
        if role.name.lower() == "she/her":
            responses += femme_responses
    respond = random.choice(responses)
    if respond == "BAD!":
        # noinspection LongLine
        await message.channel.send(
            "https://cdn.discordapp.com/emojis/902351699182780468.gif?size=56&quality=lossless",
            allowed_mentions=discord.AllowedMentions.none()
        )
    await message.channel.send(
        respond,
        allowed_mentions=discord.AllowedMentions.none()
    )


async def _add_to_blacklist(itx, db_location, string):
    """
    Add a string to the command executor's blacklist.
    :param itx: The interaction with the user/executor, and itx.client.
    :param db_location: Whether to add it to the sending or
     receiving blacklist.
    :param string: The string to add to the blacklist.
    :return: The new blacklist.
    """
    collection = itx.client.async_rina_db["complimentblacklist"]
    query = {"user": itx.user.id}
    search = await collection.find_one(query)
    blacklist = []
    if search is not None:
        blacklist = search.get(db_location, [])
    blacklist.append(string)
    await collection.update_one(
        query,
        {"$set": {db_location: blacklist}},
        upsert=True
    )
    return blacklist


class Compliments(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @staticmethod
    def _contains_cuteness_assignment(msg: str):
        # todo: upgrade cute-call detection hardware
        return (
            ((("cute" or "cutie" or "adorable" in msg)
              and "not" in msg)
             or "uncute" in msg)
            and "not uncute" not in msg
        )

    @commands.Cog.listener()  # Rina reflecting cuteness compliments
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if self.client.user.mention in message.content.split():
            msg = message.content.lower()
            called_cute: bool | None = self._contains_cuteness_assignment(
                msg.content.lower())
            if called_cute is True:
                try:
                    await message.add_reaction("<:this:960916817801535528>")
                except (discord.HTTPException or discord.NotFound):
                    await log_to_guild(
                        self.client,
                        message.guild,
                        (f"**:warning: Warning: **Couldn't add pat "
                         f"reaction to {message.jump_url}")
                    )
                    raise
            elif called_cute is False:
                await _rina_used_deflect_and_it_was_very_effective(message)
            elif any([x in msg for x in [
                "can i have a pat",
                "can i have a headpat",
                "can i have pat",
                "can i have headpat",
                "can you pat",
                "can you headpat",
                "can u pat",
                "can u headpat",
                "please pat",
                "pls pat",
                "please headpat",
                "pls headpat",
                "i want a pat",
                "i want a headpat",
                "i want pat",
                "i want headpat",
                "pats please",
                "headpats please",
                "pats pls",
                "headpats pls",
                "pat pls",
                "headpat pls",
                "pat please",
                "headpat please"
            ]]):
                try:
                    # todo: make server settings emoji
                    # todo: make server module toggleable
                    await message.add_reaction(
                        "<:TPF_02_Pat:968285920421875744>")
                except discord.errors.HTTPException:
                    try:
                        await message.channel.send(
                            "Unfortunately I can't give you a headpat (for "
                            "some reason), so have this instead:\n"
                            "<:TPF_02_Pat:968285920421875744>"
                        )
                    except discord.errors.Forbidden:
                        pass
            else:
                cmd_mention = self.client.get_command_mention("help")
                await message.channel.send(
                    f"I use slash commands! Use /`command`  and see what cool "
                    f"things might pop up! or try {cmd_mention}\n"
                    f"PS: If you're trying to call me cute: no im not",
                    delete_after=8
                )

    @module_not_disabled_check(ModuleKeys.compliments)
    @app_commands.command(name="compliment",
                          description="Complement someone fem/masc/enby")
    @app_commands.describe(user="Who do you want to compliment?")
    async def compliment(
            self,
            itx: discord.Interaction[Bot],
            user: discord.User
    ):
        # discord.User because discord.Member gets
        #  errors.TransformerError in DMs.
        user_roles = getattr(user, "roles", [])[:]
        # ^ Fetch user's roles, and copy the list to prevent modifying
        #  the original list of roles.

        roles = ["he/him", "she/her", "they/them", "it/its"]
        # pick a random order for which pronoun role to pick
        random.shuffle(user_roles)
        for role in user_roles:
            if role.name.lower() in roles:  # look for pronoun roles
                await _choose_and_send_compliment(
                    itx, user, role.name.lower(), itx.client.async_rina_db)
                return
        await _send_confirm_gender_modal(itx.client, itx, user)

    @app_commands.command(
        name="complimentblacklist",
        description="If you dislike words in certain compliments"
    )
    @app_commands.choices(location=[
        discord.app_commands.Choice(
            name='When complimenting someone else', value=1),
        discord.app_commands.Choice(
            name='When I\'m being complimented by others', value=2)
    ])
    @app_commands.choices(mode=[
        discord.app_commands.Choice(
            name='Add a string to your compliments blacklist', value=1),
        discord.app_commands.Choice(
            name='Remove a string from your compliments blacklist', value=2),
        discord.app_commands.Choice(
            name='Check your blacklisted strings', value=3)
    ])
    @app_commands.describe(
        location="Blacklist when giving compliments / when receiving "
                 "compliments from others",
        string="What sentence or word do you want to blacklist? "
               "(eg: 'good girl' or 'girl')"
    )
    async def complimentblacklist(
            self,
            itx: discord.Interaction[Bot],
            location: int,
            mode: int,
            string: str | None = None
    ):  # todo: split function into multiple smaller functions
        itx.response: discord.InteractionResponse[Bot]  # type: ignore
        itx.followup: discord.Webhook  # type: ignore
        if location == 1:
            db_location = "personal_list"
        elif location == 2:
            db_location = "list"
        else:
            raise NotImplementedError("This shouldn't happen.")

        if mode == 1:  # add an item to the blacklist
            if string is None:
                await itx.response.send_message(
                    "With this command, you can blacklist a section of text "
                    "in compliments. For example, if you don't like being "
                    "called 'Good girl', you can blacklist this compliment by "
                    "blacklisting 'good' or 'girl'. \n"
                    "Or if you don't like hugging people, you can "
                    "blacklist 'hug'.\n"
                    "Note: it's case sensitive",
                    ephemeral=True
                )
                return
            if len(string) > 150:
                await itx.response.send_message(
                    "Please make strings shorter than 150 characters...",
                    ephemeral=True
                )
                return
            await itx.response.defer(ephemeral=True)
            blacklist = await _add_to_blacklist(itx, db_location, string)
            await itx.followup.send(
                f"Successfully added {repr(string)} to your blacklist. "
                f"({len(blacklist)} item{'s' * (len(blacklist) != 1)} in your "
                f"blacklist now)",
                ephemeral=True)

        elif mode == 2:  # Remove item from black list
            if string is None:
                cmd_mention = itx.client.get_command_mention(
                    "complimentblacklist")
                await itx.response.send_message(
                    f"Type the id of the string you want to remove. To find "
                    f"the id, type {cmd_mention} `mode:Check`.",
                    ephemeral=True)
                return
            try:
                string = int(string)
            except ValueError:
                await itx.response.send_message(
                    "To remove a string from your blacklist, you must give "
                    "the id of the string you want to remove. This should be "
                    "a number... You didn't give a number...",
                    ephemeral=True)
                return
            collection = itx.client.async_rina_db["complimentblacklist"]
            query = {"user": itx.user.id}
            search0: dict[
                typing.Literal["personal_list", "list"],
                list[str]] = await collection.find_one(query)
            if search0 is None:
                await itx.response.send_message(
                    "There are no items on your blacklist, so you can't "
                    "remove any either...",
                    ephemeral=True
                )
                return
            blacklist = search0.get(db_location, [])

            try:
                del blacklist[string]
            except IndexError:
                cmd_mention = itx.client.get_command_mention(
                    "complimentblacklist")
                await itx.response.send_message(
                    f"Couldn't delete that ID, because there isn't any item "
                    f"on your list with that ID. Use {cmd_mention} "
                    f"`mode:Check` to see the IDs assigned to each item on "
                    f"your list",
                    ephemeral=True)
                return
            await collection.update_one(
                query,
                {"$set": {db_location: blacklist}},
                upsert=True
            )
            await itx.response.send_message(
                f"Successfully removed `{string}` from your blacklist. Your "
                f"blacklist now contains {len(blacklist)} "
                f"string{'s' * (len(blacklist) != 1)}.",
                ephemeral=True)

        elif mode == 3:  # check
            collection = itx.client.async_rina_db["complimentblacklist"]
            query = {"user": itx.user.id}
            search1: dict[str, int | list] = await collection.find_one(query)  # type: ignore # noqa
            if search1 is None:
                await itx.response.send_message(
                    "There are no strings in your blacklist, so... nothing "
                    "to list here...",
                    ephemeral=True
                )
                return
            blacklist = search1.get(db_location, [])
            length = len(blacklist)

            ans = []
            for blackboard_id in range(length):
                ans.append(f"`{blackboard_id}`: {blacklist[blackboard_id]}")
            ans = '\n'.join(ans)
            await itx.response.send_message(
                f"Found {length} string{'s' * (length != 1)}:\n{ans}"[:2000],
                ephemeral=True
            )

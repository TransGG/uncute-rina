import json  # to read API json responses
import requests  # to read api calls

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.settings.objects import (
    ModuleKeys,
    AttributeKeys,
    MessageableGuildChannel,
)
from resources.checks import ModuleNotEnabledCheckFailure, module_enabled_check
from resources.checks.command_checks import is_in_dms
from resources.customs import Bot
from resources.utils.utils import log_to_guild  # to log add_poll_reactions


MaybeEmoji = discord.Emoji | discord.PartialEmoji | None


STAFF_CONTACT_CHECK_WAIT_MIN = 5000
STAFF_CONTACT_CHECK_WAIT_MAX = 7500

currency_options = {
    code: 0 for code in (
        "AED,AFN,ALL,AMD,ANG,AOA,ARS,AUD,AWG,AZN,BAM,BBD,BDT,BGN,BHD,BIF,BMD,"
        "BND,BOB,BRL,BSD,BTC,BTN,BWP,BYN,BZD,CAD,CDF,CHF,CLF,CLP,CNH,CNY,COP,"
        "CRC,CUC,CUP,CVE,CZK,DJF,DKK,DOP,DZD,EGP,ERN,ETB,EUR,FJD,FKP,GBP,GEL,"
        "GGP,GHS,GIP,GMD,GNF,GTQ,GYD,HKD,HNL,HRK,HTG,HUF,IDR,ILS,IMP,INR,IQD,"
        "IRR,ISK,JEP,JMD,JOD,JPY,KES,KGS,KHR,KMF,KPW,KRW,KWD,KYD,KZT,LAK,LBP,"
        "LKR,LRD,LSL,LYD,MAD,MDL,MGA,MKD,MMK,MNT,MOP,MRU,MUR,MVR,MWK,MXN,MYR,"
        "MZN,NAD,NGN,NIO,NOK,NPR,NZD,OMR,PAB,PEN,PGK,PHP,PKR,PLN,PYG,QAR,RON,"
        "RSD,RUB,RWF,SAR,SBD,SCR,SDG,SEK,SGD,SHP,SLE,SLL,SOS,SRD,SSP,STD,STN,"
        "SVC,SYP,SZL,THB,TJS,TMT,TND,TOP,TRY,TTD,TWD,TZS,UAH,UGX,USD,UYU,UZS,"
        "VEF,VES,VND,VUV,WST,XAF,XAG,XAU,XCD,XCG,XDR,XOF,XPD,XPF,XPT,YER,ZAR,"
        "ZMW,ZWG,ZWL"
        .split(",")
    )
}
conversion_rates = {  # [default 0, incrementation]
    "temperature": {
        "Celsius": [273.15, 1, "°C"],
        "Kelvin": [0, 1, "K"],
        "Fahrenheit": [459.67, 1.8, "°F"],
        "Rankine": [0, 1.8, "°R"]
    },
    "length": {
        "kilometer": [0, 0.001, "km"],
        "hectometer": [0, 0.01, "hm"],
        "meter": [0, 1, "m"],
        "decimeter": [0, 10, "dm"],
        "centimeter": [0, 100, "cm"],
        "millimeter": [0, 1000, "mm"],
        "micrometer": [0, 10 ** 6, "μm"],
        "nanometer": [0, 10 ** 9, "nm"],
        "picometer": [0, 10 ** 12, "pm"],
        "femtometer": [0, 10 ** 15, "fm"],
        "ångström": [0, 10 ** 10, "Å"],

        "mile": [0, 0.0006213711922373339, "mi"],
        "yard": [0, 1.09361329833770778652, "yd"],
        "foot": [0, 3.28083989501312335958, "ft"],
        "inch": [0, 39.37007874015748031496, "in"],

    },
    "surface area": {
        "square kilometer": [0, 0.000001, "km²"],
        "square meter": [0, 1, "m²"],
        "square centimeter": [0, 10000, "cm²"],
        "square mile": [0, 0.00000038610215854781256, "mi²"],
        "square yard": [0, 1.19599, "yd²"],
        "square feet": [0, 10.76391, "ft²"],
        "square inch": [0, 1550, "in²"],
        "hectare": [0, 0.0001, "ha"],
        "acre": [0, 0.00024710538146716534, "ac"]
    },
    "volume": {
        "cubic meter": [0, 1, "m³"],
        "cubic centimeter": [0, 1000000, "cm³"],
        "cubic feet": [0, 35.31466666, "ft³"],
        "quart": [0, 1056.688209, "qt"],
        "pint": [0, 2113.376419, "pt"],
        "fluid ounce": [0, 33814.0227, "fl oz"],
        "milliliter": [0, 1000000, "mL"],
        "liter": [0, 1000, "L"],
        "gallon": [0, 264.172052, "gal"],
        "cup": [0, 4226.752838, "cp"],
    },
    "speed": {
        "meter per second": [0, 1, "m/s"],
        "feet per second": [0, 3.28084, "ft/s"],
        "kilometers per hour": [0, 3.6, "km/h"],
        "miles per hour": [0, 2.23694, "mph"],
        "knots": [0, 1.94384, "kn"]
    },
    "weight": {
        "kilogram": [0, 1, "kg"],
        "gram": [0, 1000, "g"],
        "milligram": [0, 1000000, "mg"],
        "ounce": [0, 35.273962, "oz"],  # 28.349523125
        "pound": [0, 2.20462262, "lb"],  # 0.45359237
        "stone": [0, 0.157473],
        "US ton": [0, 0.001102311310924388],
        "UK ton": [0, 0.0009842065264486655],
        "Metric ton": [0, 0.001],
    },
    "currency": currency_options,
    "time": {
        # 365.2421896698-6.15359\cdot10^{-6}a-7.29
        #  \cdot10^{-10}a^{2}+2.64\cdot10^{-10}a^{3}
        #     where `a` is centuries of 36525 SI days
        # 31556925.1 <- this will hold up for 3 years (until
        #  2025-7-13T21:48:21.351744),
        #     after which it will be 31556925.0
        # 31556925.0 will hold up for another 18 years (until 2044);
        #  after which it will be 31556924.9 for 19 years (2063)
        "decennium": [0, 1 / 315569251.0, "dec"],
        "year": [0, 1 / 31556925.1, "yr"],
        "month": [0, 12 / 31556925.1, "mo"],
        "week": [0, 1 / 604800, "wk"],
        "day": [0, 1 / 86400, "d"],
        "hour": [0, 1 / 3600, "hr"],
        "minute": [0, 1 / 60, "min"],
        "second": [0, 1, "sec"],
        "millisecond": [0, 10 ** 3, "ms"],
        "microsecond": [0, 10 ** 6, "μs"],
        "shake": [0, 10 ** 8, "shake"],
        "nanosecond": [0, 10 ** 9, "ns"],
        "picosecond": [0, 10 ** 12, "ps"],
        "femtosecond": [0, 10 ** 15, "fs"],
    }
}


def _get_emoji_from_str(
        client: Bot, emoji_str: str | None
) -> discord.Emoji | discord.PartialEmoji | None:
    """
    Get a matching (partial) emoji object from an emoji string or
    emoji ID.

    :param client: The client/bot whose servers to check for the emoji.
    :param emoji_str: The emoji (<a:Test_Emoji:0123456789> -> Emoji)
     or id (0123456789 -> PartialEmoji) to look for.

    :return: PartialEmoji if emoji is Unicode; Emoji if emoji is custom;
     or None if emoji wasn't found or can't be used by the bot (not in
     the server?).

    .. note::

        :py:func:`discord.PartialEmoji.from_str` turns "e" into
        ``<PartialEmoji name="e", id=None>`` this means
        :py:func:`discord.PartialEmoji.is_unicode_emoji` will return
        ``True`` because ``id == None`` (and ``name != None`` is
        implied?) so it might still raise a NotFound error.
    """
    if emoji_str is None:
        return None
    elif emoji_str.isdecimal():
        return client.get_emoji(int(emoji_str))  # returns None if not found
    else:
        emoji_partial = discord.PartialEmoji.from_str(emoji_str)
        if (
                emoji_partial is None
                or emoji_partial.is_unicode_emoji()
                or emoji_partial.id is None  # <- for type checking.
                # ^ Technically already done by is_unicode_emoji.
        ):
            # see docstring note
            return emoji_partial
        emoji = client.get_emoji(emoji_partial.id)
        if emoji is None:
            return None
        if not emoji.is_usable():
            return None
        return emoji


async def _unit_autocomplete(itx: discord.Interaction[Bot], current: str):
    options = conversion_rates.copy()
    if itx.namespace.mode not in options:
        return []  # user hasn't selected a mode yet.
    options = options[itx.namespace.mode]
    if itx.namespace.mode == "currency":
        return [app_commands.Choice(name=option, value=option)
                for option in options
                if option.lower().startswith(current.lower())
                ][:10]
    else:
        return [app_commands.Choice(name=option, value=option)
                for option in options
                if current.lower() in option.lower()
                ][:25]


async def _role_autocomplete(itx: discord.Interaction[Bot], current: str):
    """Autocomplete for /remove-role command."""
    if isinstance(itx.user, discord.User):
        return []
    role_options = {
        1126160553145020460: ("Hide Politics channel role", "NPA"),  # NPA
        1126160612620243044: ("Hide Venting channel role", "NVA")  # NVA
    }
    options = []

    for role in itx.user.roles:
        if role.id in role_options:
            if (current.lower() in role_options[role.id][0].lower()
                    or current.lower() in role_options[role.id][1].lower()):
                options.append(role.id)
    if options:
        return [app_commands.Choice(name=role_options[role_id][0],
                                    value=role_options[role_id][1])
                for role_id in options
                ][:15]
    else:
        return [
            app_commands.Choice(name="You don't have any roles to remove!",
                                value="none")
        ]


class OtherAddons(commands.Cog):
    def __init__(self):
        pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if "celcius" in message.content.lower():
            await message.reply(
                "Fun fact: Celsius was named after a guy named "
                "['Anders Celsius']"
                "(https://en.wikipedia.org/wiki/Anders_Celsius). "
                "'Celcius' is therefore an incorrect spelling. :)"
            )

    @app_commands.command(name="convert_unit",
                          description="Convert temperature or distance from "
                                      "imperial to metric etc."
                          )
    @app_commands.choices(mode=[
        discord.app_commands.Choice(
            name='Currency (USD, EUR, CAD, etc.)', value="currency"),
        discord.app_commands.Choice(
            name='Length (miles,km,inch)', value="length"),
        discord.app_commands.Choice(
            name='Speed (mph, km/h, m/s, etc.)', value="speed"),
        discord.app_commands.Choice(
            name='Surface area (sq.ft., m^2)', value="surface area"),
        discord.app_commands.Choice(
            name='Temperature (Fahrenheit, C, K, etc.)', value="temperature"),
        discord.app_commands.Choice(
            name='Time (year, minute, sec, etc.)', value="time"),
        discord.app_commands.Choice(
            name='Volume (m^3)', value="volume"),
        discord.app_commands.Choice(
            name='Weight (pounds, ounces, kg, gram, etc.)', value="weight"),
    ])
    @app_commands.describe(
        mode="What category of unit do you want to convert",
        from_unit="Which unit do you want to convert from?",
        public="Do you want to share the result with everyone in chat?"
    )
    @app_commands.rename(from_unit='from')
    @app_commands.autocomplete(from_unit=_unit_autocomplete)
    @app_commands.rename(from_unit='to')
    @app_commands.autocomplete(to_unit=_unit_autocomplete)
    @app_commands.allowed_installs(
        guilds=True, users=True)
    @app_commands.allowed_contexts(
        guilds=True, private_channels=True, dms=True)
    async def convert_unit(
            self,
            itx: discord.Interaction[Bot],
            mode: str,
            from_unit: str,
            value: float,
            to_unit: str,
            public: bool = False
    ):
        rates = conversion_rates.copy()
        if mode not in rates:
            await itx.response.send_message(
                "You didn't give a valid conversion method/mode!",
                ephemeral=True
            )
            return
        if mode == "currency":
            # more info:
            #  https://docs.openexchangerates.org/reference/latest-json
            params = {
                "appid": itx.client.api_tokens['Open Exchange Rates'],
                "show_alternative": "true",
            }
            response_api = requests.get(
                "https://openexchangerates.org/api/latest.json",
                params=params
            ).text
            data = json.loads(response_api)
            if data.get("error", 0):
                await itx.response.send_message(
                    "I'm sorry, something went wrong while trying to get "
                    "the latest currency exchange rates.",
                    ephemeral=True
                )
                return
            options = {x: [0, data['rates'][x], x] for x in data['rates']}
            from_unit = from_unit.upper()
            to_unit = to_unit.upper()
        else:
            options = rates[mode]
        if from_unit not in options or to_unit not in options:
            await itx.response.send_message(
                "Your unit conversion things need to be options that are "
                "in the list/database (as given by the autocomplete)!",
                ephemeral=True
            )
            return
        base_value = (value + options[from_unit][0]) / options[from_unit][1]
        # base_value is essentially the "x" in the conversion rates
        #      {"Celsius": [273.15, 1],
        #       "Fahrenheit": [459.67, 1.8]}
        # x = (273.15 + C degrees Celsius) / 1
        # result = x * 1.8 - 459.67
        result = (base_value * options[to_unit][1]) - options[to_unit][0]
        result = round(result, 12)
        formatted_value = int(value) if value.is_integer() else value
        if mode == "currency":
            await itx.response.send_message(
                f"Converted {mode} from {formatted_value} {from_unit} to "
                f"{result} {options[to_unit][2]}.",
                ephemeral=not public
            )
        else:
            await itx.response.send_message(
                f"Converted {mode} from {formatted_value} {from_unit} to "
                f"{to_unit}: {result} {options[to_unit][2]}.",
                ephemeral=not public
            )

    @app_commands.command(
        name="add_poll_reactions",
        description="Make rina add an upvote/downvote emoji to a message"
    )
    @app_commands.rename(
        message_id_str="message_id",
        upvote_emoji_str="upvote_emoji",
        downvote_emoji_str="downvote_emoji",
        neutral_emoji_str="neutral_emoji",
    )
    @app_commands.describe(
        message_id_str="What message do you want to add the votes to?",
        upvote_emoji_str="What emoji do you want to react first?",
        downvote_emoji_str="What emoji do you want to react second?",
        neutral_emoji_str="Neutral emoji option (placed between the "
                          "up/downvote)"
    )
    async def add_poll_reactions(
            self,
            itx: discord.Interaction[Bot],
            message_id_str: str,
            upvote_emoji_str: str,
            downvote_emoji_str: str,
            neutral_emoji_str: str | None = None
    ):
        if not is_in_dms(itx.guild) and not itx.client.is_module_enabled(
                itx.guild, ModuleKeys.poll_reactions):
            # Server specifically disabled this feature.
            raise ModuleNotEnabledCheckFailure(ModuleKeys.poll_reactions)
        if itx.channel is None:
            await itx.response.send_message(
                "I don't know what channel you're sending this in, so I "
                "can't find the message you're referring to either. Make "
                "sure you're in a channel I can see!",
                ephemeral=True
            )
            return
        if isinstance(itx.channel, (discord.ForumChannel, discord.StageChannel,
                                    discord.CategoryChannel)):
            await itx.response.send_message(
                "I can't add emojis to messages in this channel, because "
                "these channels typically don't contain any messages in the "
                "first place. Make sure you're running this command in the "
                "correct channel!",
                ephemeral=True
            )
            return

        errors = []
        message: None | discord.Message = None  # happy IDE
        if message_id_str.isdecimal():
            message_id = int(message_id_str)
            try:
                message = await itx.channel.fetch_message(message_id)
            except discord.errors.NotFound:
                errors.append("- I couldn't find a message with this ID!")
            except discord.errors.Forbidden:
                errors.append(
                    "- I'm not allowed to find a message in this channel!")
            except discord.errors.HTTPException:
                errors.append("- Fetching the message failed.")
        else:
            errors.append("- The message ID needs to be a number!")

        upvote_emoji: MaybeEmoji = _get_emoji_from_str(
            itx.client, upvote_emoji_str)
        if upvote_emoji is None:
            errors.append("- I can't use this upvote emoji! "
                          "(perhaps it's a nitro emoji)")

        downvote_emoji: MaybeEmoji = _get_emoji_from_str(
            itx.client, downvote_emoji_str)
        if downvote_emoji is None:
            errors.append("- I can't use this downvote emoji! "
                          "(perhaps it's a nitro emoji)")

        if neutral_emoji_str is not None:
            neutral_emoji: MaybeEmoji = _get_emoji_from_str(
                itx.client, neutral_emoji_str)
            if neutral_emoji is None:
                errors.append("- I can't use this neutral emoji! "
                              "(perhaps it's a nitro emoji)")
        else:
            neutral_emoji = None

        blacklisted_channels: list[MessageableGuildChannel] = []
        if itx.guild is not None:
            blacklisted_channels = itx.client.get_guild_attribute(
                itx.guild, AttributeKeys.poll_reaction_blacklisted_channels) \

        if (blacklisted_channels is not None
                and itx.channel.id in blacklisted_channels):
            errors.append("- :no_entry: You are not allowed to use this "
                          "command in this channel!")

        if errors or not message:
            await itx.response.send_message(
                "Couldn't add poll reactions:\n"
                + '\n'.join(errors),
                ephemeral=True
            )
            return
        assert upvote_emoji is not None
        assert downvote_emoji is not None

        try:
            await itx.response.send_message("Adding emojis...", ephemeral=True)
            await message.add_reaction(upvote_emoji)
            if neutral_emoji is not None:
                await message.add_reaction(neutral_emoji)
            await message.add_reaction(downvote_emoji)
            await itx.edit_original_response(
                content=":white_check_mark: Successfully added emojis")
        except discord.errors.Forbidden:
            await itx.edit_original_response(
                content=":no_entry: Couldn't add all poll reactions: "
                        "Forbidden (maybe the user you're trying to add "
                        "reactions to has blocked Rina)"
            )
            return
        except discord.errors.NotFound:
            await itx.edit_original_response(
                content=":no_entry: Couldn't add all poll reactions: "
                        "(at least) one of the emojis was not a real emoji!"
            )
        except discord.errors.HTTPException as ex:
            if ex.status == 400:
                await itx.edit_original_response(
                    content=":no_entry: Couldn't add all poll reactions: "
                            "(at least) one of the emojis was not a real "
                            "emoji!"
                )
            else:
                await itx.edit_original_response(
                    content=":warning: Adding emojis failed!"
                )
        cmd_poll = itx.client.get_command_mention("add_poll_reactions")

        if not is_in_dms(itx.guild):
            await log_to_guild(
                itx.client,
                itx.guild,
                f"{itx.user.name} ({itx.user.id}) used {cmd_poll} "
                f"on message {message.jump_url}"
            )

    @app_commands.command(
        name="get_rina_command_mention",
        description="Sends a hidden command mention for your command"
    )
    @app_commands.describe(
        command="Command to get a mention for (with/out slash)"
    )
    async def find_command_mention_itx(
            self,
            itx: discord.Interaction[Bot],
            command: str
    ):
        command = command.removeprefix("/").lower()
        try:
            for section in command.split(" "):
                # "/vctable create" would be invalidated because spaces
                # aren't allowed, but it's still a valid command mention.
                app_commands.commands.validate_name(section)
        except ValueError:
            await itx.response.send_message(
                "Heads up: your command contains unavailable characters. "
                "Discord only allows names to be between 1-32 characters "
                "and contain only lower-case letters, numbers, hyphens, "
                "underscores, or spaces (for command groups).",
                ephemeral=True
            )
            return

        try:
            cmd_mention = itx.client.get_command_mention(command)
        except ValueError as ex:
            await itx.response.send_message(str(ex), ephemeral=True)
            return
        await itx.response.send_message(
            f"Your input: `{command}`.\n"
            f"Command mention: {cmd_mention}.\n"
            f"Raw command mention: `{cmd_mention}`\n"
            "-# Did it not work? Try it with `help`",
            ephemeral=True
        )

    @app_commands.command(name="remove-role",
                          description="Remove one of your agreement roles")
    @app_commands.describe(role_name="The name of the role to remove")
    @app_commands.autocomplete(role_name=_role_autocomplete)
    @module_enabled_check(ModuleKeys.remove_role_command)
    async def remove_role(self, itx: discord.Interaction[Bot], role_name: str):
        if isinstance(itx.user, discord.User):
            # It shouldn't be a discord.User cause the app_command check
            #  prevents DMs. But to make the type checker happy, here you go.
            await itx.response.send_message(
                "The bot did not see you as Member of a server, so I couldn't "
                "remove any roles from you! Make sure you're running this in "
                "the channel of a server.",
                ephemeral=True
            )
            return

        role_options = {
            "npa": ["NPA", 1126160553145020460],
            "nva": ["NVA", 1126160612620243044],
        }
        if role_name.lower() not in role_options:
            await itx.response.send_message(
                "You can't remove that role!", ephemeral=True)
            return

        role_id = role_options[role_name.lower()][1]
        try:
            matching_roles = [r for r in itx.user.roles
                              if r.id == role_id]
            # it only selects the first one of them, but oh well.
            for role in matching_roles:
                await itx.user.remove_roles(
                    role,
                    reason="Removed by user using /remove-role"
                )
                await itx.response.send_message(
                    "Successfully removed role!", ephemeral=True)
                return
        except discord.Forbidden:
            await itx.response.send_message(
                "I couldn't remove this role! (Forbidden)",
                ephemeral=True
            )
            return

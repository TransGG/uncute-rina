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

currency_options = {
    code: 0 for code in (
        "AED,AFN,ALL,AMD,ANG,AOA,ARS,AUD,AWG,AZN,BAM,BBD,BDT,BGN,BHD,BIF,BMD,BND,BOB,BRL,BSD,BTC,BTN,BWP,BYN,BZD,CAD,"
        "CDF,CHF,CLF,CLP,CNH,CNY,COP,CRC,CUC,CUP,CVE,CZK,DJF,DKK,DOP,DZD,EGP,ERN,ETB,EUR,FJD,FKP,GBP,GEL,GGP,GHS,GIP,"
        "GMD,GNF,GTQ,GYD,HKD,HNL,HRK,HTG,HUF,IDR,ILS,IMP,INR,IQD,IRR,ISK,JEP,JMD,JOD,JPY,KES,KGS,KHR,KMF,KPW,KRW,KWD,"
        "KYD,KZT,LAK,LBP,LKR,LRD,LSL,LYD,MAD,MDL,MGA,MKD,MMK,MNT,MOP,MRU,MUR,MVR,MWK,MXN,MYR,MZN,NAD,NGN,NIO,NOK,NPR,"
        "NZD,OMR,PAB,PEN,PGK,PHP,PKR,PLN,PYG,QAR,RON,RSD,RUB,RWF,SAR,SBD,SCR,SDG,SEK,SGD,SHP,SLL,SOS,SRD,SSP,STD,STN,"
        "SVC,SYP,SZL,THB,TJS,TMT,TND,TOP,TRY,TTD,TWD,TZS,UAH,UGX,USD,UYU,UZS,VES,VND,VUV,WST,XAF,XAG,XAU,XCD,XDR,XOF,"
        "XPD,XPF,XPT,YER,ZAR,ZMW,ZWL".split(","))}
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
        # 365.2421896698-6.15359\cdot10^{-6}a-7.29\cdot10^{-10}a^{2}+2.64\cdot10^{-10}a^{3}
        #     where `a` is centuries of 36525 SI days
        # 31556925.1 <- this will hold up for 3 years (until 2025-7-13T21:48:21.351744),
        #     after which it will be 31556925.0
        # 31556925.0 will hold up for another 18 years (until 2044); after which it will be
        #     31556924.9 for 19 years (2063)
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


def get_emoji_from_str(
        client: Bot, emoji_str: str | None
) -> discord.Emoji | discord.PartialEmoji | None:
    """
    Get a matching (partial) emoji object from an emoji string or emoji ID.

    Parameters
    -----------
    client: :class:`Bot`
        The client/bot whose servers to check for the emoji.
    emoji_str: :class:`str` | :class:`None`
        The emoji (<a:Test_Emoji:0123456789> -> Emoji) or id (0123456789 -> PartialEmoji) to look for.

    Returns
    --------
    :class:`None`
        if no emoji found, or it can't be used by the bot (not in the server).
    :class:`discord.PartialEmoji`
        if emoji is unicode.
    :class:`discord.Emoji`
        if emoji is valid and can be used but the bot.
    """
    if emoji_str is None:
        return None
    elif emoji_str.isdecimal():
        return client.get_emoji(int(emoji_str))  # returns None if not found
    else:
        emoji_partial = discord.PartialEmoji.from_str(emoji_str)
        if emoji_partial is None or emoji_partial.is_unicode_emoji():
            # note: PartialEmoji.from_str turns "e" into <PartialEmoji name="e", id=None>
            #   this means .is_unicode_emoji will return True because id == None (and name != None?)
            #   so it might still raise a NotFound error
            return emoji_partial
        emoji = client.get_emoji(emoji_partial.id)
        if emoji is None:
            return None
        if not emoji.is_usable():
            return None
        return emoji


async def unit_autocomplete(itx: discord.Interaction, current: str):
    options = conversion_rates.copy()
    if itx.namespace.mode not in options:
        return []  # user hasn't selected a mode yet.
    options = options[itx.namespace.mode]
    if itx.namespace.mode == "currency":
        return [
                   app_commands.Choice(name=option, value=option)
                   for option in options if option.lower().startswith(current.lower())
               ][:10]
    else:
        return [
                   app_commands.Choice(name=option, value=option)
                   for option in options if current.lower() in option.lower()
               ][:25]


class OtherAddons(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:  # mention targeted user if added to mod-ticket with /add target:@user
            # message.channel.category.id
            if message.channel.category.id in [995330645901455380, 995330667665707108, 1086349703182041089]:
                print("embeds:", len(message.embeds), "| message.author.id:", message.author.id)
                if message.author.id == 557628352828014614 and len(message.embeds) == 1:
                    # if ticket tool adds a user to a ticket, reply by mentioning the newly added user
                    components = message.embeds[0].description.split(" ")
                    print("components:", repr(components))
                    print("@" in components[0])
                    print(f'{components[1]} {components[2]} {components[3]} == "added to ticket"',
                          f"{components[1]} {components[2]} {components[3]}" == "added to ticket")
                    if "@" in components[0] and f"{components[1]} {components[2]} {components[3]}" == "added to ticket":
                        await message.channel.send("Obligatory ping to notify newly added user: " + components[0],
                                                   allowed_mentions=discord.AllowedMentions.all())
        except (AttributeError, discord.errors.ClientException):
            # channel.category apparently discord raises ClientException: Parent channel not found,
            # instead of attribute error
            pass

        if message.author.bot:
            return

        if "celcius" in message.content.lower():
            await message.reply(
                "Fun fact: Celsius was named after a guy named "
                "['Anders Celsius'](https://en.wikipedia.org/wiki/Anders_Celsius). "
                "'Celcius' is therefore an incorrect spelling. :)")

    @app_commands.command(name="convert_unit",
                          description="Convert temperature or distance from imperial to metric etc.")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Currency (USD, EUR, CAD, etc.)', value="currency"),
        discord.app_commands.Choice(name='Length (miles,km,inch)', value="length"),
        discord.app_commands.Choice(name='Speed (mph, km/h, m/s, etc.)', value="speed"),
        discord.app_commands.Choice(name='Surface area (sq.ft., m^2)', value="surface area"),
        discord.app_commands.Choice(name='Temperature (Fahrenheit, C, K, etc.)', value="temperature"),
        discord.app_commands.Choice(name='Time (year, minute, sec, etc.)', value="time"),
        discord.app_commands.Choice(name='Volume (m^3)', value="volume"),
        discord.app_commands.Choice(name='Weight (pounds, ounces, kg, gram, etc.)', value="weight"),
    ])
    @app_commands.describe(mode="What category of unit do you want to convert",
                           from_unit="Which unit do you want to convert from?",
                           public="Do you want to share the result with everyone in chat?")
    @app_commands.rename(from_unit='from')
    @app_commands.autocomplete(from_unit=unit_autocomplete)
    @app_commands.rename(from_unit='to')
    @app_commands.autocomplete(to_unit=unit_autocomplete)
    async def convert_unit(
            self, itx: discord.Interaction, mode: str, from_unit: str, value: float, to_unit: str, public: bool = False
    ):
        rates = conversion_rates.copy()
        if mode not in rates:
            await itx.response.send_message("You didn't give a valid conversion method/mode!", ephemeral=True)
            return
        if mode == "currency":
            # more info: https://docs.openexchangerates.org/reference/latest-json
            api_key = self.client.api_tokens['Open Exchange Rates']
            response_api = requests.get(
                f"https://openexchangerates.org/api/latest.json?app_id={api_key}&show_alternative=true").text
            data = json.loads(response_api)
            if data.get("error", 0):
                await itx.response.send_message(f"I'm sorry, something went wrong while trying to get the latest data",
                                                ephemeral=True)
                return
            options = {x: [0, data['rates'][x], x] for x in data['rates']}
            from_unit = from_unit.upper()
            to_unit = to_unit.upper()
        else:
            options = rates[mode]
        if from_unit not in options or to_unit not in options:
            await itx.response.send_message("Your unit conversion things need to be options that are in the "
                                            "list/database (as given by the autocomplete)!",
                                            ephemeral=True)
            return
        base_value = (value + options[from_unit][0]) / options[from_unit][1]
        # base_value is essentially the "x" in the conversion rates
        #      {"Celsius": [273.15, 1],
        #       "Fahrenheit": [459.67, 1.8]}
        # x = (273.15 + C degrees Celsius) / 1
        # result = x * 1.8 - 459.67
        result = (base_value * options[to_unit][1]) - options[to_unit][0]
        result = round(result, 12)
        if mode == "currency":
            await itx.response.send_message(
                f"Converting {mode} from {value} {from_unit} to {result} {options[to_unit][2]}", ephemeral=not public)
        else:
            await itx.response.send_message(
                f"Converting {mode} from {value} {from_unit} to {to_unit}: {result} {options[to_unit][2]}",
                ephemeral=not public)

    @app_commands.command(name="add_poll_reactions", description="Make rina add an upvote/downvote emoji to a message")
    @app_commands.describe(message_id="What message do you want to add the votes to?",
                           upvote_emoji="What emoji do you want to react first?",
                           downvote_emoji="What emoji do you want to react second?",
                           neutral_emoji="Neutral emoji option (placed between the up/downvote)")
    async def add_poll_reactions(
            self, itx: discord.Interaction, message_id: str,
            upvote_emoji: str, downvote_emoji: str, neutral_emoji: str | None = None
    ):
        errors = []
        message: None | discord.Message = None  # happy IDE
        if message_id.isdecimal():
            message_id = int(message_id)
            try:
                message = await itx.channel.fetch_message(message_id)
            except discord.errors.NotFound:
                errors.append("- I couldn't find a message with this ID!")
            except discord.errors.Forbidden:
                errors.append("- I'm not allowed to find a message in this channel!")
            except discord.errors.HTTPException:
                errors.append("- Fetching the message failed.")
        else:
            errors.append("- The message ID needs to be a number!")

        upvote_emoji: (discord.Emoji | discord.PartialEmoji | None) = get_emoji_from_str(self.client, upvote_emoji)
        if upvote_emoji is None:
            errors.append("- I can't use this upvote emoji! (perhaps it's a nitro emoji)")

        downvote_emoji: (discord.Emoji | discord.PartialEmoji | None) = get_emoji_from_str(self.client, downvote_emoji)
        if downvote_emoji is None:
            errors.append("- I can't use this downvote emoji! (perhaps it's a nitro emoji)")

        if neutral_emoji is None:
            neutral_emoji: (discord.Emoji | discord.PartialEmoji | None) = get_emoji_from_str(self.client,
                                                                                              neutral_emoji)
            if neutral_emoji is None:
                errors.append("- I can't use this neutral emoji! (perhaps it's a nitro emoji)")

        if itx.guild.id != self.client.custom_ids["staff_server_id"]:
            blacklisted_channels = await self.client.get_guild_info(itx.guild, "pollReactionsBlacklist")
            if itx.channel.id in blacklisted_channels:
                errors.append("- :no_entry: You are not allowed to use this command in this channel!")

        if errors or not message:
            await itx.response.send_message("Couldn't add poll reactions:\n" + '\n'.join(errors), ephemeral=True)
            return

        try:
            await itx.response.send_message("Adding emojis...", ephemeral=True)
            await message.add_reaction(upvote_emoji)
            if neutral_emoji:
                await message.add_reaction(neutral_emoji)
            await message.add_reaction(downvote_emoji)
            await itx.edit_original_response(content=":white_check_mark: Successfully added emojis")
        except discord.errors.Forbidden:
            await itx.edit_original_response(content=":no_entry: Couldn't add all poll reactions: Forbidden "
                                                     "(maybe the user you're trying to add reactions to has "
                                                     "blocked Rina)")
        except discord.errors.NotFound:
            await itx.edit_original_response(content=":no_entry: Couldn't add all poll reactions: (at least) "
                                                     "one of the emojis was not a real emoji!")
        except discord.errors.HTTPException as ex:
            if ex.status == 400:
                await itx.edit_original_response(content=":no_entry: Couldn't add all poll reactions: "
                                                         "(at least) one of the emojis was not a real emoji!")
            else:
                await itx.edit_original_response(content=":warning: Adding emojis failed!")
        cmd_mention = self.client.get_command_mention("add_poll_reactions")
        await log_to_guild(self.client, itx.guild,
                           f"{itx.user.name} ({itx.user.id}) used {cmd_mention} on message {message.jump_url}")

    @app_commands.command(name="get_rina_command_mention",
                          description="Sends a hidden command mention for your command")
    @app_commands.describe(command="Command to get a mention for (with/out slash)")
    async def find_command_mention_itx(self, itx: discord.Interaction, command: str):
        command = command.removeprefix("/").lower()
        try:
            app_commands.commands.validate_name(command)
        except ValueError:
            await itx.response.send_message(
                "Heads up: your command contains unavailable characters. Discord only allows "
                "names to be between 1-32 characters and contain only lower-case letters, "
                "numbers, hyphens, underscores, or spaces (for command groups).",
                ephemeral=True)
            return

        cmd_mention = self.client.get_command_mention(command)
        await itx.response.send_message(
            f"Your input: `{command}`.\n"
            f"Command mention: {cmd_mention}.\n"
            f"Raw command mention: `{cmd_mention}`\n"
            "-# Did it not work? Try it with `help`",
            ephemeral=True
        )

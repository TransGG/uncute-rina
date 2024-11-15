import discord, discord.ext.commands as commands, discord.app_commands as app_commands
import requests # to read api calls
import json # to read API json responses
import random # for dice rolls (/roll) and selecting a random staff interaction wait time
from resources.utils.utils import log_to_guild # to log add_poll_reactions
from resources.customs.addons import EqualDexRegion
from resources.views.addons import EqualDex_AdditionalInfo, SendPublicButton_Math
from resources.customs.bot import Bot

STAFF_CONTACT_CHECK_WAIT_MIN = 5000
STAFF_CONTACT_CHECK_WAIT_MAX = 7500


currency_options = {
    code: 0 for code in "AED,AFN,ALL,AMD,ANG,AOA,ARS,AUD,AWG,AZN,BAM,BBD,BDT,BGN,BHD,BIF,BMD,BND,BOB,BRL,BSD,BTC,BTN,BWP,BYN,BZD,CAD,CDF,"
                        "CHF,CLF,CLP,CNH,CNY,COP,CRC,CUC,CUP,CVE,CZK,DJF,DKK,DOP,DZD,EGP,ERN,ETB,EUR,FJD,FKP,GBP,GEL,GGP,GHS,GIP,GMD,GNF,"
                        "GTQ,GYD,HKD,HNL,HRK,HTG,HUF,IDR,ILS,IMP,INR,IQD,IRR,ISK,JEP,JMD,JOD,JPY,KES,KGS,KHR,KMF,KPW,KRW,KWD,KYD,KZT,LAK,"
                        "LBP,LKR,LRD,LSL,LYD,MAD,MDL,MGA,MKD,MMK,MNT,MOP,MRU,MUR,MVR,MWK,MXN,MYR,MZN,NAD,NGN,NIO,NOK,NPR,NZD,OMR,PAB,PEN,"
                        "PGK,PHP,PKR,PLN,PYG,QAR,RON,RSD,RUB,RWF,SAR,SBD,SCR,SDG,SEK,SGD,SHP,SLL,SOS,SRD,SSP,STD,STN,SVC,SYP,SZL,THB,TJS,"
                        "TMT,TND,TOP,TRY,TTD,TWD,TZS,UAH,UGX,USD,UYU,UZS,VES,VND,VUV,WST,XAF,XAG,XAU,XCD,XDR,XOF,XPD,XPF,XPT,YER,"
                        "ZAR,ZMW,ZWL".split(",")}
conversion_rates = { # [default 0, incrementation]
    "temperature":{
        "Celsius"    : [273.15, 1, "°C"],
        "Kelvin"     : [0, 1, "K"],
        "Fahrenheit" : [459.67, 1.8, "°F"],
        "Rankine"    : [0, 1.8, "°R"]
    },
    "length":{
        "kilometer"  : [0, 0.001, "km"],
        "hectometer" : [0, 0.01, "hm"],
        "meter"      : [0, 1, "m"],
        "decimeter"  : [0, 10, "dm"],
        "centimeter" : [0, 100, "cm"],
        "millimeter" : [0, 1000, "mm"],
        "micrometer" : [0, 10 ** 6, "μm"],
        "nanometer"  : [0, 10 ** 9, "nm"],
        "picometer"  : [0, 10 ** 12, "pm"],
        "femtometer" : [0, 10 ** 15, "fm"],
        "ångström"   : [0, 10 ** 10, "Å"],

        "mile"       : [0, 0.0006213711922373339, "mi"],
        "yard"       : [0, 1.09361329833770778652, "yd"],
        "foot"       : [0, 3.28083989501312335958, "ft"],
        "inch"       : [0, 39.37007874015748031496, "in"],

    },
    "surface area": {
        "square kilometer"  : [0, 0.000001, "km²"],
        "square meter"      : [0, 1, "m²"],
        "square centimeter" : [0, 10000, "cm²"],
        "square mile"       : [0, 0.00000038610215854781256, "mi²"],
        "square yard"       : [0, 1.19599, "yd²"],
        "square feet"       : [0, 10.76391, "ft²"],
        "square inch"       : [0, 1550, "in²"],
        "hectare"           : [0, 0.0001, "ha"],
        "acre"              : [0, 0.00024710538146716534, "ac"]
    },
    "volume": {
        "cubic meter"      : [0, 1, "m³"],
        "cubic centimeter" : [0, 1000000, "cm³"],
        "cubic feet"       : [0, 35.31466666, "ft³"],
        "quart"            : [0, 1056.688209, "qt"],
        "pint"             : [0, 2113.376419, "pt"],
        "fluid ounce"      : [0, 33814.0227, "fl oz"],
        "milliliter"       : [0, 1000000, "mL"],
        "liter"            : [0, 1000, "L"],
        "gallon"           : [0, 264.172052, "gal"],
        "cup"              : [0, 4226.752838, "cp"],
    },
    "speed": {
        "meter per second"    : [0, 1, "m/s"],
        "feet per second"     : [0, 3.28084, "ft/s"],
        "kilometers per hour" : [0, 3.6, "km/h"],
        "miles per hour"      : [0, 2.23694, "mph"],
        "knots"               : [0, 1.94384, "kn"]
    },
    "weight": {
        "kilogram"  : [0, 1, "kg"],
        "gram"      : [0, 1000, "g"],
        "milligram" : [0, 1000000, "mg"],
        "ounce"     : [0, 35.273962, "oz"], # 28.349523125
        "pound"     : [0, 2.20462262, "lb"], # 0.45359237
        "stone"     : [0, 0.157473],
        "US ton"    : [0, 0.001102311310924388],
        "UK ton"    : [0, 0.0009842065264486655],
        "Metric ton": [0, 0.001],
    },
    "currency":currency_options,
    "time": {
        # 365.2421896698-6.15359\cdot10^{-6}a-7.29\cdot10^{-10}a^{2}+2.64\cdot10^{-10}a^{3} where a is centuries of 36525 SI days
        # 31556925.1 <- this will hold up for 3 years (until 2025-7-13T21:48:21.351744), after which it will be 31556925.0
        # 31556925.0 will hold up for another 18 years (until 2044); after which it will be 31556924.9 for 19 years (2063)
        "decenium"          : [0, 1/315569251.0, "dec"],
        "year"              : [0, 1/31556925.1, "yr"],
        "month"             : [0, 12/31556925.1, "mo"],
        "week"              : [0, 1/604800, "wk"],
        "day"               : [0, 1/86400, "d"],
        "hour"              : [0, 1/3600, "hr"],
        "minute"            : [0, 1/60, "min"],
        "second"            : [0, 1, "sec"],
        "millisecond"       : [0, 10**3, "ms"],
        "microsecond"       : [0, 10**6, "μs"],
        "shake"             : [0, 10**8, "shake"],
        "nanosecond"        : [0, 10**9, "ns"],
        "picosecond"        : [0, 10**12, "ps"],
        "femtosecond"       : [0, 10**15, "fs"],
    }
}


def generateOutput(responses: list[str], author: discord.User):
    """
    Convert a list of verification follow-up questions into a nicely written message

    Parameters
    -----------
    responses: :class:`list[str]`
        A list of questions to be asked to the user (parameter 'author')
    author: :class:`discord.User`
        The user to mention for the response

    Returns
    --------
    response: :class:`str`
        A nicely written response with fluff and pre/postfixes, as well as listing keywords (first of all / next / also).
    """
    output = ""
    if len(responses) > 0:
        output += f"""Hey there {author.mention},
Thank you for taking the time to answer our questions
If you don't mind, could you answer some more for us?"""

    keywords = ["First of all","Next","aaand..","Also","Lastly","PS","PPS","PPPS","PPPPS","PPPPPS","PPPPPPS"]
    for index in range(len(responses)):
        output += f"""

{keywords[index]},
{responses[index]}"""

    if len(output) > 0:
        output += """

Once again, if you dislike answering any of these or following questions, feel free to tell me. I can give others.
Thank you in advance :)"""
    else:
        output += "\n:warning: Couldn't think of any responses."
    return output

def get_emoji_from_str(client: Bot, emoji_str: str | discord.utils._MissingSentinel) -> discord.Emoji | discord.PartialEmoji | None:
    """
    Get a matching (partial) emoji object from an emoji string or emoji ID.

    Parameters
    -----------
    client: :class:`Bot`
        The client/bot whose servers to check for the emoji.
    emoji_str: :class:`str` | :class:`discord.utils._MissingSenitel`
        The emoji (<a:Test_Emoji:0123456789> -> Emoji) or id (0123456789 -> PartialEmoji) to look for.

    Returns
    --------
    :class:`None`
        if no emoji found or it can't be used by the bot (not in the server).
    :class:`discord.PartialEmoji`
        if emoji is unicode.
    :class:`discord.Emoji`
        if emoji is valid and can be used but the bot.
    """
    if emoji_str == discord.utils._MissingSentinel:
        return None
    elif emoji_str.isdecimal():
        return client.get_emoji(int(emoji_str)) # returns None if not found
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

def product_in_list(mult_list: list):
    a = 1
    for x in mult_list:
        a *= x
    return a

def generate_roll(query: str) -> list[int]:
    # print(query)
    temp: list[str | int] = query.split("d")
    ## 2d4 = ["2","4"]
    ## 2d3d4 = ["2","3","4"] (huh?)
    ## 4 = 4
    ## [] (huh?)
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
    remainder = temp[1][len(faces):] # (take the length of the now-still-string faces variable)
    try:
        dice = int(dice)
    except ValueError:
        raise ValueError(f"You have to roll a numerical number of dice! (You tried to roll '{dice}' dice)")
    try:
        faces = int(faces)
    except ValueError:
        raise TypeError(
            f"You have to roll a die with a numerical number of faces! (You tried to roll {dice} dice with '{faces}' faces)")
    if len(remainder) > 0:
        raise TypeError("Idk what happened, but you probably filled something in incorrectly.")
    if dice >= 1000000:
        raise OverflowError(f"Sorry, if I let you roll `{dice:,}` dice, then the universe will implode, and Rina will stop responding to commands. Please stay below 1 million dice...")
    if faces >= 1000000:
        raise OverflowError(f"Uh.. At that point, you're basically rolling a sphere. Even earth has fewer faces than `{faces:,}`. Please bowl with a sphere of fewer than 1 million faces...")

    return [(negative*-2+1)*random.randint(1, faces) for _ in range(dice)]


class SearchAddons(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @app_commands.command(name="equaldex", description="Find info about LGBTQ+ laws in different countries!")
    @app_commands.describe(country_id="What country do you want to know more about? (GB, US, AU, etc.)")
    async def equaldex(self, itx: discord.Interaction, country_id: str):
        illegal_characters = ""
        for char in country_id.lower():
            if char not in "abcdefghijklmnopqrstuvwxyz":
                if char not in illegal_characters:
                    illegal_characters += char
        if len(illegal_characters) > 1:
            await itx.response.send_message(f"You can't use the following characters for country_id!\n> {illegal_characters}", ephemeral=True)
            return

        response_api = requests.get(
            f"https://www.equaldex.com/api/region?regionid={country_id}&formatted=true").text
        # returns ->  <pre>{"regions":{...}}</pre>  <- so you need to remove the <pre> and </pre> parts
        # it also has some <br \/>\r\n strings in there for some reason..? so uh
        jsonizing_table = {
            r"<br \/>\r\n":r"\n",
            "<pre>":"",
             "</pre>":""
        }
        for key in jsonizing_table:
            response_api = response_api.replace(key, jsonizing_table[key])
        data = json.loads(response_api)
        if "error" in data:
            if country_id.lower() == "uk":
                await itx.response.send_message(f"I'm sorry, I couldn't find '{country_id}'...\nTry 'GB' instead!", ephemeral=True)
            else:
                await itx.response.send_message(f"I'm sorry, I couldn't find '{country_id}'...",ephemeral=True)
            return

        region = EqualDexRegion(data['regions']['region'])

        embed = discord.Embed(color=7829503, title=region.name)
        for issue in region.issues:
            if type(region.issues[issue]['current_status']) is list:
                value = "No data"
            else:
                value = region.issues[issue]['current_status']['value_formatted']
                # if region.issues[issue]['current_status']['value'] in ['Legal',
                #                                                        'Equal',
                #                                                        'No censorship',
                #                                                        'Legal, '
                #                                                        'surgery not required',
                #                                                        "Sexual orientation and gender identity",
                #                                                        "Recognized"]:
                #     value = "❤️ " + value
                # elif region.issues[issue]['current_status']['value'] in ["Illegal"]:
                #     value = "🚫 " + value
                # elif region.issues[issue]['current_status']['value'] in ["Not legally recognized",
                #                                                          "Not banned",
                #                                                          "Varies by Region"]:
                #     value = "🟨 " + value
                # else:
                #     value = "➖ " + value
                if len(region.issues[issue]['current_status']['description']) > 0:
                    value += f" ({region.issues[issue]['current_status']['description']})"
                elif len(region.issues[issue]['description']) > 0:
                    value += f" ({region.issues[issue]['description']})"
                if len(value) > 1024:
                    value = value[:1020]+"..."
            embed.add_field(name   = region.issues[issue]['label'],
                            value  = value,
                            inline = False)
        embed.set_footer(text=f"For more info, click the button below,")
        view = EqualDex_AdditionalInfo(region.url)
        await itx.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="math", description="Ask Wolfram Alpha a question")
    async def math(self, itx: discord.Interaction, query: str):
        await itx.response.defer(ephemeral=True)
        if query.lower() in ["help", "what is this", "what is this?"]:
            await itx.followup.send(
                "This is a math command that connects to the Wolfram Alpha website! "
                "You can ask it math or science questions, and it will answer them for you! Kinda like an AI. "
                "It uses scientific data. Here are some example queries:\n"
                "- What is 9+10\n"
                "- What is the derivative of 4x^2+3x+5\n"
                "- What color is the sky?", ephemeral=True)
            return
        if "&" in query:
            await itx.followup.send("Your query cannot contain an ampersand (&/and symbol)! (it can mess with the URL)\n"
                                    "For the bitwise 'and' operator, try replacing '&' with ' bitwise and '. Example '4 & 6' -> '4 bitwise and 6'\n"
                                    "For other uses, try replacing the ampersand with 'and' or the word(s) it symbolizes.", ephemeral=True)
            return
        query = query.replace("+", " plus ") # plusses are interpreted as a spacebar in urls. In LaTeX, that can mean multiply
        api_key = self.client.api_tokens['Wolfram Alpha']
        try:
            data = requests.get(
                f"https://api.wolframalpha.com/v2/query?appid={api_key}&input={query}&output=json").json()
        except requests.exceptions.JSONDecodeError:
            await itx.followup.send("Your input gave a malformed result! Perhaps it took too long to calculate...", ephemeral=True)
            return

        data = data["queryresult"]
        if data["success"]:
            interpreted_input = ""
            output = ""
            other_primary_outputs = []
            error_or_nodata = 0
            for pod in data["pods"]:
                subpods = []
                if pod["id"] == "Input":
                    for subpod in pod["subpods"]:
                        subpods.append(subpod["plaintext"].replace("\n", "\n>     "))
                    interpreted_input = '\n> '.join(subpods)
                if pod["id"] == "Result":
                    for subpod in pod["subpods"]:
                        if subpod.get("nodata") or subpod.get("error"): # error or nodata == True
                            error_or_nodata += 1
                        subpods.append(subpod["plaintext"].replace("\n", "\n>     "))
                    output = '\n> '.join(subpods)
                elif pod.get("primary", False):
                    for subpod in pod["subpods"]:
                        if len(subpod["plaintext"]) == 0:
                            continue
                        if subpod.get("nodata") or subpod.get("error"): # error or nodata == True
                            error_or_nodata += 1
                        other_primary_outputs.append(subpod["plaintext"].replace("\n", "\n>     "))
            if len(output) == 0 and len(other_primary_outputs) == 0:
                error_or_nodata = 0
                # if there is no result and all other pods are 'primary: False'
                for pod in data["pods"]:
                    if pod["id"] not in ["Input", "Result"]:
                        for subpod in pod["subpods"]:
                            if len(subpod["plaintext"]) == 0:
                                continue
                            if subpod.get("nodata") or subpod.get("error"): # error or nodata == True
                                error_or_nodata += 1
                            other_primary_outputs.append(subpod["plaintext"].replace("\n", "\n>     "))
            if len(other_primary_outputs) > 0:
                other_results = '\n> '.join(other_primary_outputs)
                other_results = "\nOther results:\n> " + other_results
            else:
                other_results = ""
            if len(other_primary_outputs) + bool(len(output)) <= error_or_nodata:
                # if there are more or an equal amount of errors as there are text entries
                await itx.followup.send(f"There was no data for your answer!\n"
                                        f"It seems all your answers had an error or were 'nodata entries', meaning "
                                        f"you might need to try a different query to get an answer to your question!", ephemeral=True)
                return
            assumptions = []
            if "assumptions" in data:
                if type(data["assumptions"]) is dict:
                    # only 1 assumption, instead of a list. So just make a list of 1 assumption instead.
                    data["assumptions"] = [data["assumptions"]]
                for assumption in data.get("assumptions", []):
                    assumption_data = {} # because Wolfram|Alpha is being annoyingly inconsistent.
                    if "word" in assumption:
                        assumption_data["${word}"] = assumption["word"]
                    for value_index in range(len(assumption["values"])):
                        assumption_data["${desc"+str(value_index + 1)+"}"] = assumption["values"][value_index]["desc"]
                        try:
                            assumption_data["${word"+str(value_index + 1)+"}"] = assumption["values"][value_index]["word"]
                        except KeyError:
                            pass # the "word" variable is only there sometimes. for some stupid reason.

                    template: str = assumption["template"]
                    for replacer in assumption_data:
                        template = template.replace(replacer, assumption_data[replacer])
                    if template.endswith("."):
                        template = template[:-1]
                    assumptions.append(template + "?")
            if len(assumptions) > 0:
                alternatives = "\nAssumptions:\n> " + '\n> '.join(assumptions)
            else:
                alternatives = ""
            warnings = []
            if "warnings" in data:
                # not sure if multiple warnings will be stored into a list instead
                # Edit: Turns out they do.
                if type(data["warnings"]) is list:
                    for warning in data["warnings"]:
                        warnings.append(warning["text"])
                else:
                    warnings.append(data["warnings"]["text"])
            if len(data.get("timedout", "")) > 0:
                warnings.append("Timed out: " + data["timedout"].replace(",", ", "))
            if len(data.get("timedoutpods", "")) > 0:
                warnings.append("Timed out pods: " + data["timedout"].replace(",", ", "))
            if len(warnings) > 0:
                warnings = "\nWarnings:\n> " + '\n> '.join(warnings)
            else:
                warnings = ""
            view = SendPublicButton_Math(self.client)
            await itx.followup.send(
                f"Input\n> {interpreted_input}\n"
                f"Result:\n> {output}" +
                other_results +
                alternatives +
                warnings, view=view, ephemeral=True)
            await view.wait()
            if view.value is None:
                await itx.edit_original_response(view=None)
            return
        else:
            if data["error"]:
                code = data["error"]["code"]
                message = data["error"]["msg"]
                await itx.followup.send(f"I'm sorry, but I wasn't able to give a response to that!\n"
                                                f"> code: {code}\n"
                                                f"> message: {message}", ephemeral=True)
                return
            elif "didyoumeans" in data:
                didyoumeans = {}
                if type(data["didyoumeans"]) is list:
                    for option in data["didyoumeans"]:
                        didyoumeans[option["score"]] = option["val"]
                else:
                    didyoumeans[data["didyoumeans"]["score"]] = data["didyoumeans"]["val"]
                options_sorted = sorted(didyoumeans.items(), key=lambda x: float(x[0]), reverse=True)
                options = [value for _, value in options_sorted]
                options_str = "\n> ".join(options)
                await itx.followup.send(f"I'm sorry, but I wasn't able to give a response to that! However, here are some possible improvements to your prompt:\n"
                                                f"> {options_str}", ephemeral=True)
                return
            elif "languagemsg" in data: # x does not support [language].
                await itx.followup.send(f"Error:\n> {data['languagemsg']['english']}\n"
                                        f"> {data['languagemsg']['other']}", ephemeral=True)
                return
            elif "futuretopic" in data: # x does not support [language].
                await itx.followup.send(f"Error:\n> {data['futuretopic']['topic']}\n"
                                        f"> {data['futuretopic']['msg']}", ephemeral=True)
                return
            # why aren't these in the documentation? cmon wolfram, please.
            elif "tips" in data:
                # not sure if this is put into a list if there are multiple.
                await itx.followup.send(f"Error:\n> {data['tips']['text']}", ephemeral=True)
                return
            elif "examplepage" in data:
                # not sure if this is put into a list if there are multiple.
                await itx.followup.send(f"Here is an example page for the things you can do with {data['examplepage']['category']}:\n"
                                        f"> {data['examplepage']['url']}", ephemeral=True)
                return
            else:
                # welp. Apparently you can get *no* info in the output as well!! UGHHHHH
                await itx.followup.send("Error: No further info\n"
                                        "It appears you filled in something for which I can't get extra feedback..\n"
                                        "Feel free to report the situation to MysticMia#7612", ephemeral=True)
                return
        # await itx.followup.send("debug; It seems you reached the end of the function without "
        #                         "actually getting a response! Please report the query to MysticMia#7612", ephemeral=True)

class FunAddons(commands.Cog):
    def __init__(self, client: Bot):
        global rina_db
        self.client = client
        rina_db = client.rina_db
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
            Whether or not a reaction was added to the message. 
        """
        # adding headpats every x messages
        self.headpat_wait += 1
        if self.headpat_wait >= 1000:
            if (
                    (type(message.channel) is discord.Thread and message.channel.parent == 987358841245151262) or # <#welcome-verify>
                    message.channel.name.startswith('ticket-') or
                    message.channel.name.startswith('closed-') or
                    message.channel.category.id in [959584962443632700, 959590295777968128, 959928799309484032, 1041487583475138692,
                                                    995330645901455380, 995330667665707108] or
                    # <#Bulletin Board>, <#Moderation Logs>, <#Verifier Archive>, <#Events>, <#Open Tickets>, <#Closed Tickets>
                    message.guild.id in [981730502987898960] # don't send in Mod server
            ):
                pass
            else:
                self.headpat_wait = 0
                # people asked for no random headpats anymore; or make it opt-in. See GitHub #23 # TODO: re-enable code someday
                # try:
                #     added_pat = True
                #     await message.add_reaction("<:TPF_02_Pat:968285920421875744>") #headpatWait
                # except discord.errors.Forbidden:
                #     await log_to_guild(self.client, message.guild, f'**:warning: Warning: **Couldn\'t add pat reaction to {message.jump_url} (Forbidden): They might have blocked Rina...')
                # except discord.errors.HTTPException as ex:
                #     await log_to_guild(self.client, message.guild, f'**:warning: Warning: **Couldn\'t add pat reaction to {message.jump_url}. (HTTP/{ex.code}) They might have blocked Rina...')
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
            msg_content = msg_content.replace("ab","").replace("aw","")
            if msg_content == "a":
                try:
                    added_pat = True
                    await message.add_reaction("<:TPF_02_Pat:968285920421875744>")
                except discord.errors.Forbidden: # blocked rina :(
                    pass
                except discord.errors.HTTPException as ex:
                    if ex.code == 10014: # bad request (emoji doesnt exist: cause it's dev testing environment)
                        await message.add_reaction("☺") # :relaxed:
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
                except discord.errors.Forbidden: # blocked rina :(
                    pass
                except discord.errors.HTTPException as ex:
                    if ex.code == 10014: # bad request (emoji doesnt exist: cause it's dev testing environment)
                        await message.add_reaction("☺") # :relaxed:
                    else:
                        raise

        if message.author.bot:
            return

        # embed "This conversation was powered by friendship" every x messages # TODO: re-enable code someday
        if False:#self.staff_contact_check_wait == 0 or (self.staff_contact_check_wait < -10 and self.staff_contact_check_wait % 6 == 0): # make sure it only sends once (and <-10 for backup)
            if message.channel.id in [960920453705257061, 999165241894109194, 999165867625566218, 999167335938150410]:
                # TransPlace [general, trans masc treehouse, trans fem forest, enby enclave] # TODO: when cleo adds "report" func to EnbyPlace (or other servers in general), add those server's channel IDs too.

                if message.guild.id == self.client.custom_ids.get("enbyplace_server_id"):
                    mod_ticket_channel_id = 1186054373986537522
                elif message.guild.id == self.client.custom_ids.get("transonance_server_id"):
                    mod_ticket_channel_id = 1108789589558177812
                else: #elif context.guild_id == client.custom_ids.get("transplace_server_id"):
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
                    "This conversation was sponsored by Raid Shadow Legends, one of the biggest mobile role-playing gam...",
                    "This conversation was sponsored by Spotify; Want a break from the ads?",
                    "This conversation was sponsored by Homestuck",
                    "This conversation was brought to you by Flex Seal! To show the power of Flex Tape, I sawed this boat in half!",
                    "Want to advertise? Call 0900 0000 to place an AD!",
                    "Do you have suggestions for what to place here? Ping mysticmia and share!",
                    "1", #"Fun fact: ",
                ]
                superpower = random.choice(options)

                if superpower == "1":
                    response = requests.get('https://api.api-ninjas.com/v1/facts?limit=1', headers={
                        # "X-Api-Key": "YOUR_API_KEY",
                        "Origin": "https://api-ninjas.com",
                        # "Host": "api.api-ninjas.com", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0", "Accept": "*/*", "Accept-Language": "en-US,en;q=0.5",
                        # "Accept-Encoding": "gzip, deflate, br", "Referer": "https://api-ninjas.com/", "Connection": "keep-alive", "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-site", "Sec-GPC": "1", "TE": "trailers"
                    }).json()[0]["fact"]
                    starter = random.choice(["This conversation is cool and all, but did you know ", "Fun fact: "])
                    response = starter + response[0].lower() + response[1:] # make first letter lowercase so it fits with the rest of the sentence
                    if len(response) > 256: # embed title length limit is 256 chars.
                        header = options[0]
                    else:
                        header = response
                else:
                    header = superpower

                embed = discord.Embed(
                    color=discord.Color.from_hsv(205/360, 65/100, 100/100),
                    title = header,
                    description = f"See someone breaking the rules? Unsure about a situation? You can always contact staff! Reach us in "
                                    f"<#{mod_ticket_channel_id}>, or report a user/message with our bot (more info: {cmd_mention} `tag:report`) "
                                    f"(Gives staff a bit more context :). You may always ping/dm a staff member or Moderators if necessary."
                )
                await message.channel.send(embed=embed)
                self.staff_contact_check_wait = random.randint(STAFF_CONTACT_CHECK_WAIT_MIN, STAFF_CONTACT_CHECK_WAIT_MAX)
        self.staff_contact_check_wait -= 1

        # give opinion on people hating on rina
        self.rude_comments_opinion_cooldown -= 1
        if self.rude_comments_opinion_cooldown < 0:
            if self.client.user.id in [user.id for user in message.mentions]:
                if (    ":" in message.content and
                        "middlefinger" in message.content.lower().replace(" ","")):
                    await message.reply("That's kind of rude... Why would you do that?")
                    self.rude_comments_opinion_cooldown = STAFF_CONTACT_CHECK_WAIT_MIN * 8

    @app_commands.command(name="roll", description="Roll a die or dice with random chance!")
    @app_commands.describe(dice="How many dice do you want to roll?",
                           faces="How many sides does every die have?",
                           mod="Do you want to add a modifier? (add 2 after rolling the dice)",
                           advanced="Roll more advanced! example: 1d20+3*2d4. Overwrites dice/faces given; 'help' for more") # TODO: actually add 'help' command
    async def roll(self, itx: discord.Interaction,
                   dice: app_commands.Range[int, 1, 999999],
                   faces: app_commands.Range[int, 1, 999999],
                   public: bool = False, mod: int | None = None, advanced: str | None = None):
        hide = False
        if advanced is None:
            await itx.response.defer(ephemeral=not public)
            rolls = []
            for _ in range(dice):
                rolls.append(random.randint(1,faces))

            if mod is None:
                if dice == 1:
                    out = f"I rolled {dice} di{'c'*(dice>1)}e with {faces} face{'s'*(faces>1)}: " +\
                          f"{str(sum(rolls))}"
                else:
                    out = f"I rolled {dice} di{'c'*(dice>1)}e with {faces} face{'s'*(faces>1)}:\n" +\
                          f"{' + '.join([str(roll) for roll in rolls])}  =  {str(sum(rolls))}"
            else:
                out = f"I rolled {dice} {'die' if dice == 0 else 'dice'} with {faces} face{'s'*(faces>1)} and a modifier of {mod}:\n" +\
                      f"({' + '.join([str(roll) for roll in rolls])}) + {mod}  =  {str(sum(rolls)+mod)}"
            if len(out) > 300:
                out = f"I rolled {dice:,} {'die' if dice == 0 else 'dice'} with {faces:,} face{'s'*(faces>1)}"+f" and a modifier of {(mod or 0):,}"*(mod is not None)+":\n" +\
                      f"With this many numbers, I've simplified it a little. You rolled `{sum(rolls)+(mod or 0):,}`."
                roll_db = {}
                for roll in rolls:
                    try:
                        roll_db[roll] += 1
                    except KeyError:
                        roll_db[roll] = 1
                # order dict by the eyes rolled: {"eyes":"count",1:4,2:1,3:4,4:1}
                # x.items() gives a list of tuples [(1,4),(2,1),(3,4),(4,1)] that is then sorted by the first item in the tuple
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
            await itx.followup.send(out,ephemeral=not public)
        else:
            await itx.response.defer(ephemeral=not public)
            advanced = advanced.replace(" ","")
            if advanced == "help":
                cmd_mention = self.client.get_command_mention("help")
                await itx.response.send(f"I don't think I ever implemented this... Ping mysticmia for more information about this command, or run {cmd_mention} `page:112` for more information.")

            for char in advanced:
                if char not in "0123456789d+*-":  # kKxXrR": #!!pf≤≥
                    if public:
                        await itx.delete_original_response()
                    await itx.followup.send(f"Invalid input! This command doesn't have support for '{char}' yet!",ephemeral=True)
                    return
            _add = advanced.replace('-', '+-').split('+')
            add = [section for section in _add if len(section) > 0]
            # print("add:       ",add)
            multiply = []
            for section in add:
                multiply.append(section.split('*'))
            # print("multiply:  ",multiply)
            try:
                result = [[sum(generate_roll(query)) for query in section] for section in multiply]
            except (TypeError,ValueError, OverflowError) as ex:
                ex = repr(ex).split("(",1)
                ex_type = ex[0]
                ex_message = ex[1][1:-1]
                if public:
                    await itx.delete_original_response()
                await itx.followup.send(f"Wasn't able to roll your dice!\n  {ex_type}: {ex_message}",ephemeral=True)
                return
            # print("result:    ",result)
            out = ["Input:  " + advanced]
            if "*" in advanced:
                out += [' + '.join([' * '.join([str(x) for x in section]) for section in result])]
            if "+" in advanced or '-' in advanced:
                out += [' + '.join([str(product_in_list(section)) for section in result])]
            out += [str(sum([product_in_list(section) for section in result]))]
            output = discord.utils.escape_markdown('\n= '.join(out))
            if len(output) >= 1950:
                output = "Your result was too long! I couldn't send it. Try making your rolls a bit smaller, perhaps by splitting it into multiple operations..."
            if len(output) >= 500:
                hide = True
            try:
                await itx.followup.send(output,ephemeral=not public)
            except discord.errors.NotFound:
                if hide:
                    await itx.delete_original_response()
                await itx.user.send("Couldn't send you the result of your roll because it took too long or something. Here you go: \n"+output)

class OtherAddons(commands.Cog):
    def __init__(self, client: Bot):
        global rina_db
        self.client = client
        rina_db = client.rina_db

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try: # mention targeted user if added to mod-ticket with /add target:@user
            # message.channel.category.id
            if message.channel.category.id in [995330645901455380, 995330667665707108, 1086349703182041089]:
                print("embeds:", len(message.embeds), "| message.author.id:", message.author.id)
                if message.author.id == 557628352828014614 and len(message.embeds) == 1:
                    # if ticket tool adds a user to a ticket, reply by mentioning the newly added user
                    components = message.embeds[0].description.split(" ")
                    print("components:", repr(components))
                    print("@" in components[0])
                    print(f'{components[1]} {components[2]} {components[3]} == "added to ticket"', f"{components[1]} {components[2]} {components[3]}" == "added to ticket")
                    if "@" in components[0] and f"{components[1]} {components[2]} {components[3]}" == "added to ticket":
                        await message.channel.send("Obligatory ping to notify newly added user: " + components[0], allowed_mentions=discord.AllowedMentions.all())
        except (AttributeError, discord.errors.ClientException):
            # channel.category apparently discord raises ClientException: Parent channel not found, instead of attribute error
            pass

        if message.author.bot:
            return

        if "celcius" in message.content.lower():
            await message.reply("Fun fact: Celsius was named after a guy named ['Anders Celsius'](https://en.wikipedia.org/wiki/Anders_Celsius). 'Celcius' is therefore an incorrect spelling. :)")

    async def unit_autocomplete(self, itx: discord.Interaction, current: str):
        options = conversion_rates.copy()
        if itx.namespace.mode not in options:
            return [] # user hasn't selected a mode yet.
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

    @app_commands.command(name="convert_unit", description="Convert temperature or distance from imperial to metric etc.")
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
    async def convert_unit(self, itx:discord.Interaction, mode: str, from_unit: str, value: float, to_unit: str, public: bool = False):
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
            if data.get("error",0):
                await itx.response.send_message(f"I'm sorry, something went wrong while trying to get the latest data", ephemeral=True)
                return
            options = {x:[0,data['rates'][x],x] for x in data['rates']}
            from_unit = from_unit.upper()
            to_unit = to_unit.upper()
        else:
            options = rates[mode]
        if from_unit not in options or to_unit not in options:
            await itx.response.send_message("Your unit conversion things need to be options that are in the list/database (as given by the autocomplete)!",ephemeral=True)
            return
        base_value = (value + options[from_unit][0]) / options[from_unit][1]
        # base_value is essentially the "x" in the conversion rates
        #      {"Celsius": [273.15, 1],
        #       "Fahrenheit": [459.67, 1.8]}
        # x = (273.15 + C degrees Celsius) / 1
        # result = x * 1.8 - 459.67
        result = (base_value * options[to_unit][1]) - options[to_unit][0]
        result = round(result,12)
        if mode == "currency":
            await itx.response.send_message(f"Converting {mode} from {value} {from_unit} to {result} {options[to_unit][2]}", ephemeral=not public)
        else:
            await itx.response.send_message(f"Converting {mode} from {value} {from_unit} to {to_unit}: {result} {options[to_unit][2]}", ephemeral=not public)

    @app_commands.command(name="add_poll_reactions", description="Make rina add an upvote/downvote emoji to a message")
    @app_commands.describe(message_id="What message do you want to add the votes to?",
                           upvote_emoji="What emoji do you want to react first?",
                           downvote_emoji="What emoji do you want to react second?",
                           neutral_emoji="Neutral emoji option (placed between the up/downvote)")
    async def add_poll_reactions(self, itx: discord.Interaction, message_id: str,
                                 upvote_emoji: str, downvote_emoji: str, neutral_emoji: str | None = None):
        if neutral_emoji is None:
            neutral_emoji = discord.utils.MISSING # neutral_emoji will be re-set to None if the input is not an emoji
        errors = []
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

        if neutral_emoji is not discord.utils.MISSING:
            neutral_emoji: (discord.Emoji | discord.PartialEmoji | None) = get_emoji_from_str(self.client, neutral_emoji)
            if neutral_emoji is None:
                errors.append("- I can't use this neutral emoji! (perhaps it's a nitro emoji)")

        if itx.guild.id != self.client.custom_ids["staff_server_id"]:
            blacklisted_channels = await self.client.get_guild_info(itx.guild, "pollReactionsBlacklist")
            if itx.channel.id in blacklisted_channels:
                errors.append("- :no_entry: You are not allowed to use this command in this channel!")

        if errors:
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
            await itx.edit_original_response(content=":no_entry: Couldn't add all poll reactions: Forbidden (maybe the user you're trying to add reactions to has blocked Rina)")
        except discord.errors.NotFound:
            await itx.edit_original_response(content=":no_entry: Couldn't add all poll reactions: (at least) one of the emojis was not a real emoji!")
        except discord.errors.HTTPException as ex:
            if ex.status == 400:
                await itx.edit_original_response(content=":no_entry: Couldn't add all poll reactions: (at least) one of the emojis was not a real emoji!")
            else:
                await itx.edit_original_response(content=":warning: Adding emojis failed!")
        cmd_mention = self.client.get_command_mention("add_poll_reactions")
        await log_to_guild(self.client, itx.guild, f"{itx.user.name} ({itx.user.id}) used {cmd_mention} on message {message.jump_url}")

    @app_commands.command(name="get_rina_command_mention", description="Sends a hidden command mention for your command")
    @app_commands.describe(command="Command to get a mention for (with/out slash)")
    async def find_command_mention_itx(self, itx: discord.Interaction, command: str):
        command = command.removeprefix("/").lower()
        unallowed_characters = []
        try:
            app_commands.commands.validate_name(command)
        except ValueError:
            await itx.response.send_message("Heads up: your command contains unavailable characters. Discord only allows "
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


async def setup(client):
    await client.add_cog(OtherAddons(client))
    await client.add_cog(FunAddons(client))
    await client.add_cog(SearchAddons(client))

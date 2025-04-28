import json  # to read API json responses
import requests  # to read api calls

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.addons.equaldexregion import EqualDexRegion
from extensions.addons.views.equaldex_additionalinfo import EqualDexAdditionalInfo
from extensions.addons.views.math_sendpublicbutton import SendPublicButtonMath


STAFF_CONTACT_CHECK_WAIT_MIN = 5000
STAFF_CONTACT_CHECK_WAIT_MAX = 7500


class SearchAddons(commands.Cog):
    def __init__(self):
        pass

    @app_commands.command(name="equaldex", description="Find info about LGBTQ+ laws in different countries!")
    @app_commands.describe(country_id="What country do you want to know more about? (GB, US, AU, etc.)")
    async def equaldex(self, itx: discord.Interaction, country_id: str):
        illegal_characters = ""
        for char in country_id.lower():
            if char not in "abcdefghijklmnopqrstuvwxyz":
                if char not in illegal_characters:
                    illegal_characters += char
        if len(illegal_characters) > 1:
            await itx.response.send_message(
                f"You can't use the following characters for country_id!\n> {illegal_characters}", ephemeral=True)
            return
        equaldex_key = itx.client.api_tokens["Equaldex"]
        querystring = {"regionid": country_id, "apiKey": equaldex_key}
        response = requests.get(
            "https://www.equaldex.com/api/region", params=querystring)  # &formatted=true
        response_api = response.text
        # returns ->  <pre>{"regions":{...}}</pre>  <- so you need to remove the <pre> and </pre> parts
        # it also has some <br \/>\r\n strings in there for some reason...? so uh
        jsonizing_table = {
            r"<br \/>\r\n": r"\n",
            "<pre>": "",
            "</pre>": "",
            "<i>": "_",
            r"<\/i>": "_",
            "<b>": "**",
            r"<\/b>": "**"
        }
        for key in jsonizing_table:
            response_api = response_api.replace(key, jsonizing_table[key])
        data = json.loads(response_api)
        if "error" in data and response.status_code == 404:
            if country_id.lower() == "uk":
                await itx.response.send_message(f"I'm sorry, I couldn't find '{country_id}'...\nTry 'GB' instead!",
                                                ephemeral=True)
            else:
                await itx.response.send_message(f"I'm sorry, I couldn't find '{country_id}'...", ephemeral=True)
            return
        elif "error" in data:
            if country_id != country_id.upper():
                await itx.response.send_message(f"Error code: {response.status_code}\n"
                                                f"I'm sorry, I couldn't find '{country_id}'.\n"
                                                f"Have you tried using uppercase? Try with "
                                                f"`country_id:{country_id.upper()}`", ephemeral=True)
            else:
                await itx.response.send_message(f"Error code: {response.status_code}\n"
                                                f"I'm sorry, I couldn't find '{country_id}'.", ephemeral=True)
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
                    if len(region.issues[issue]['current_status']['description']) > 200:
                        value += f" ({region.issues[issue]['current_status']['description'][:200]}..."
                    else:
                        value += f" ({region.issues[issue]['current_status']['description']})"
                elif len(region.issues[issue]['description']) > 0:
                    if len(region.issues[issue]['description']) > 200:
                        value += f" ({region.issues[issue]['description'][:200]}..."
                    else:
                        value += f" ({region.issues[issue]['description']})"
                if len(value) > 1024:
                    value = value[:1020] + "..."
            embed.add_field(name=region.issues[issue]['label'],
                            value=value,
                            inline=False)
        embed.set_footer(text="For more info, click the button below,")
        view = EqualDexAdditionalInfo(region.url)
        await itx.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="math", description="Ask Wolfram Alpha a question")
    async def math(self, itx: discord.Interaction, query: str):
        # todo: shorten function / split, and re-investigate the API docs to see if I can parse stuff better
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
            await itx.followup.send(
                "Your query cannot contain an ampersand (&/and symbol)! (it can mess with the URL)\n"
                "For the bitwise 'and' operator, try replacing '&' with ' bitwise and '. "
                "Example '4 & 6' -> '4 bitwise and 6'\n"
                "For other uses, try replacing the ampersand with 'and' or the word(s) it symbolizes.", ephemeral=True)
            return
        query = query.replace("+",
                              " plus ")
        # pluses are interpreted as a space (`%20`) in urls. In LaTeX, that can mean multiply
        api_key = itx.client.api_tokens['Wolfram Alpha']
        try:
            data = requests.get(
                f"https://api.wolframalpha.com/v2/query?appid={api_key}&input={query}&output=json").json()
        except requests.exceptions.JSONDecodeError:
            await itx.followup.send("Your input gave a malformed result! Perhaps it took too long to calculate...",
                                    ephemeral=True)
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
                        if subpod.get("nodata") or subpod.get("error"):  # error or nodata == True
                            error_or_nodata += 1
                        subpods.append(subpod["plaintext"].replace("\n", "\n>     "))
                    output = '\n> '.join(subpods)
                elif pod.get("primary", False):
                    for subpod in pod["subpods"]:
                        if len(subpod["plaintext"]) == 0:
                            continue
                        if subpod.get("nodata") or subpod.get("error"):  # error or nodata == True
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
                            if subpod.get("nodata") or subpod.get("error"):  # error or nodata == True
                                error_or_nodata += 1
                            other_primary_outputs.append(subpod["plaintext"].replace("\n", "\n>     "))
            if len(other_primary_outputs) > 0:
                other_results = '\n> '.join(other_primary_outputs)
                other_results = "\nOther results:\n> " + other_results
            else:
                other_results = ""
            if len(other_primary_outputs) + bool(len(output)) <= error_or_nodata:
                # if there are more or an equal amount of errors as there are text entries
                await itx.followup.send("There was no data for your answer!\n"
                                        "It seems all your answers had an error or were 'nodata entries', meaning "
                                        "you might need to try a different query to get an answer to your question!",
                                        ephemeral=True)
                return
            assumptions = []
            if "assumptions" in data:
                if type(data["assumptions"]) is dict:
                    # only 1 assumption, instead of a list. So just make a list of 1 assumption instead.
                    data["assumptions"] = [data["assumptions"]]
                for assumption in data.get("assumptions", []):
                    assumption_data = {}  # because Wolfram|Alpha is being annoyingly inconsistent.
                    if "word" in assumption:
                        assumption_data["${word}"] = assumption["word"]
                    if type(assumption["values"]) is dict:
                        # only 1 value, instead of a list. So just make a list of 1 value instead.
                        assumption["values"] = [assumption["values"]]
                    for value_index in range(len(assumption["values"])):
                        assumption_data["${desc" + str(value_index + 1) + "}"] = \
                            assumption["values"][value_index]["desc"]
                        try:
                            assumption_data["${word" + str(value_index + 1) + "}"] = \
                                assumption["values"][value_index]["word"]
                        except KeyError:
                            pass  # the "word" variable is only there sometimes. for some stupid reason.

                    if "template" in assumption:
                        template: str = assumption["template"]
                        for replacer in assumption_data:
                            template = template.replace(replacer, assumption_data[replacer])
                        if template.endswith("."):
                            template = template[:-1]
                        assumptions.append(template + "?")
                    else:
                        template: str = assumption["type"] + " - " + assumption["desc"] + " (todo)"
                        assumptions.append(template)
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
            view = SendPublicButtonMath()
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
                await itx.followup.send(f"I'm sorry, but I wasn't able to give a response to that! However, here "
                                        f"are some possible improvements to your prompt:\n"
                                        f"> {options_str}", ephemeral=True)
                return
            elif "languagemsg" in data:  # x does not support [language].
                await itx.followup.send(f"Error:\n> {data['languagemsg']['english']}\n"
                                        f"> {data['languagemsg']['other']}", ephemeral=True)
                return
            elif "futuretopic" in data:  # x does not support [language].
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
                await itx.followup.send(
                    f"Here is an example page for the things you can do with {data['examplepage']['category']}:\n"
                    f"> {data['examplepage']['url']}", ephemeral=True)
                return
            else:
                # welp. Apparently you can get *no* info in the output as well!! UGHHHHH
                await itx.followup.send("Error: No further info\n"
                                        "It appears you filled in something for which I can't get extra feedback..\n"
                                        "Feel free to report the situation to MysticMia#7612", ephemeral=True)
                return
        # await itx.followup.send("debug; It seems you reached the end of the function without "
        #                         "actually getting a response! Please report the query to MysticMia#7612",
        #                         ephemeral=True)

import json  # to read API json responses

import requests  # to read api calls

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.addons.wolframresult import WolframResult, WolframQueryResult
from resources.customs import Bot

from extensions.addons.equaldexregion import EqualDexRegion
from extensions.addons.views.equaldex_additionalinfo import (
    EqualDexAdditionalInfo
)
from extensions.addons.views.math_sendpublicbutton import (
    SendPublicButtonMath
)


STAFF_CONTACT_CHECK_WAIT_MIN = 5000
STAFF_CONTACT_CHECK_WAIT_MAX = 7500


def format_wolfram_success_output(data: WolframQueryResult) -> str:
    interpreted_input = ""
    output = ""
    other_primary_outputs = []
    error_or_nodata = 0

    if data["numpods"] == 0:
        raise ValueError("TODO")  # Todo: fix

    assert "pods" in data and len(data["pods"]) == data["numpods"]

    for pod in data["pods"]:
        if pod["numsubpods"] == 0 or "subpods" not in pod:
            continue

        subpods = []
        for subpod in pod["subpods"]:
            if ("plaintext" not in subpod
                    or len(subpod["plaintext"]) == 0):
                continue

            if pod["id"] == "Input":
                subpods.append(
                    subpod["plaintext"].replace("\n", "\n>     ")
                )
            else:
                if subpod.get("nodata") or subpod.get("error"):
                    # error or nodata == True
                    error_or_nodata += 1
                if pod["id"] == "Result":
                    subpods.append(
                        subpod["plaintext"].replace("\n", "\n>     ")
                    )
                elif pod.get("primary", False):
                    other_primary_outputs.append(
                        subpod["plaintext"].replace("\n", "\n>     ")
                    )
        if pod["id"] == "Input":
            interpreted_input = "\n> ".join(subpods)
        elif pod["id"] == "Result":
            output = f"\n> ".join(subpods)

    if len(output) == 0 and len(other_primary_outputs) == 0:
        error_or_nodata = 0
        # if there is no result and all other pods are
        #  'primary: False'
        for pod in data["pods"]:
            if pod["numsubpods"] == 0 or "subpods" not in pod:
                continue

            if pod["id"] not in ["Input", "Result"]:
                for subpod in pod["subpods"]:
                    if ("plaintext" not in subpod
                            or len(subpod["plaintext"]) == 0):
                        continue
                    if subpod.get("nodata") or subpod.get("error"):
                        # error or nodata == True
                        error_or_nodata += 1
                    other_primary_outputs.append(
                        subpod["plaintext"].replace("\n", "\n>     ")
                    )
    if len(other_primary_outputs) > 0:
        other_results = '\n> '.join(other_primary_outputs)
        other_results = "\nOther results:\n> " + other_results
    else:
        other_results = ""
    data_count = len(other_primary_outputs) + bool(len(output))
    if data_count <= error_or_nodata:
        raise ValueError(
            "There was no data for your answer!\n"
            "It seems all your answers had an error or were "
            "'nodata entries', meaning you might need to try a "
            "different query to get an answer to your question!"
        )

    assumptions = _format_wolfram_assumptions(data)
    if len(assumptions) > 0:
        alternatives = "\nAssumptions:\n> " + '\n> '.join(assumptions)
    else:
        alternatives = ""
    warnings = []
    if "warnings" in data:
        # not sure if multiple warnings will be stored into a
        #  list instead.
        # Edit: Turns out they do.
        if isinstance(data["warnings"], list):
            for warning in data["warnings"]:
                warnings.append(warning["text"])
        else:
            warnings.append(data["warnings"]["text"])
    if len(data.get("timedout", "")) > 0:
        warnings.append(
            "Timed out: "
            + data["timedout"].replace(",", ", ")
        )
    if len(data.get("timedoutpods", "")) > 0:
        warnings.append(
            "Timed out pods: "
            + data["timedout"].replace(",", ", ")
        )
    if len(warnings) > 0:
        warnings = ("\nWarnings:\n> "
                    + '\n> '.join(warnings))
    else:
        warnings = ""
    return (
        f"Input\n> {interpreted_input}\n"
        f"Result:\n> {output}"
        + other_results
        + alternatives
        + warnings
    )


def _format_wolfram_assumptions(data: WolframQueryResult):
    assumptions = []
    if "assumptions" not in data:
        return assumptions

    # if type(data["assumptions"]) is dict:
    #     # only 1 assumption, instead of a list. So just make
    #     #  a list of 1 assumption instead.
    #     data["assumptions"] = [data["assumptions"]]

    for assumption in data["assumptions"]:
        assert not isinstance(assumption, str)
        if ("count" not in assumption
                or assumption["count"] == 0
                or "values" not in assumption):
            continue


        assumption_data = {}
        # because Wolfram|Alpha is being annoyingly
        #  inconsistent.
        if "word" in assumption:
            assumption_data["${word}"] = assumption["word"]

        if isinstance(assumption["values"], dict):
            # only 1 value, instead of a list. So just make
            #  a list of 1 value instead.
            assumption["values"] = [assumption["values"]]

        for value_index, value in enumerate(assumption["values"]):
            word_id = str(value_index + 1)
            assumption_data["${desc" + word_id + "}"] \
                = value["desc"]
            if "word" not in assumption:
                continue

            assumption_data["${word" + word_id + "}"] \
                = assumption["word"]

        if "template" in assumption:
            template: str = assumption["template"]
            for replacer in assumption_data:
                template = template.replace(
                    replacer, assumption_data[replacer]
                )
            if template.endswith("."):
                template = template[:-1]
            assumptions.append(template + "?")
        else:
            template: str = (
                    assumption["type"]
                    + " - "
                    + assumption["word"]
                    + " (todo)"
            )
            assumptions.append(template)
    return assumptions


def format_wolfram_error_output(data: WolframQueryResult) -> str:
    if data.get("error", False) is True:
        return "Got an error, but no extra data... Kinda weird?"

    if "error" in data and isinstance(data["error"], dict):
        code = data["error"]["code"]
        message = data["error"]["msg"]
        return (
            f"I'm sorry, but I wasn't able to give a response "
            f"to that!\n"
            f"> code: {code}\n"
            f"> message: {message}"
        )
    elif "didyoumeans" in data:
        didyoumeans = {}
        if isinstance(data["didyoumeans"], list):
            for option in data["didyoumeans"]:
                didyoumeans[option["score"]] = option["val"]
        else:
            didyoumeans[data["didyoumeans"]["score"]] \
                = data["didyoumeans"]["val"]
        options_sorted = sorted(
            didyoumeans.items(),
            key=lambda x: float(x[0]),
            reverse=True
        )
        options = [value for _, value in options_sorted]
        options_str = "\n> ".join(options)
        return (
            f"I'm sorry, but I wasn't able to give a response to "
            f"that! However, here are some possible improvements "
            f"to your prompt:\n"
            f"> {options_str}"
        )
    elif "languagemsg" in data:  # x does not support [language].
        return (
            f"Error:\n> {data['languagemsg']['english']}\n"
            f"> {data['languagemsg']['other']}"
        )
    elif "futuretopic" in data:  # x does not support [language].
        return (
            f"Error:\n> {data['futuretopic']['topic']}\n"
            f"> {data['futuretopic']['msg']}"
        )
    # why aren't these in the documentation? cmon wolfram, please.
    elif "tips" in data:
        # not sure if this is put into a list if there are multiple.
        return f"Error:\n> {data['tips']['text']}"
    elif "examplepage" in data:
        # not sure if this is put into a list if there are multiple.
        return (
            f"Here is an example page for the things you can do with "
            f"{data['examplepage']['category']}:\n"
            f"> {data['examplepage']['url']}"
        )
    else:
        # welp. Apparently you can get *no* info in the output
        #  as well!! UGHHHHH
        input_string = data.get("inputstring", None)
        return (
            "Error: No further info\n"
            "It appears you filled in something for which I can't "
            "get extra feedback..\n"
            "Feel free to report the situation to MysticMia#7612"
            + "\n\n"
              "Interpreted input:\n"
              "> {input_string}"
              if input_string is not None
              else ""
        )


class SearchAddons(commands.Cog):
    def __init__(self):
        pass

    @app_commands.command(
        name="equaldex",
        description="Find info about LGBTQ+ laws in different countries!"
    )
    @app_commands.describe(
        country_id="What country do you want to know more about? "
                   "(GB, US, AU, etc.)"
    )
    async def equaldex(self, itx: discord.Interaction[Bot], country_id: str):
        illegal_characters = ""
        for char in country_id.lower():
            if char not in "abcdefghijklmnopqrstuvwxyz":
                if char not in illegal_characters:
                    illegal_characters += char
        if len(illegal_characters) > 1:
            await itx.response.send_message(
                f"You can't use the following characters for country_id!\n"
                f"> {illegal_characters}",
                ephemeral=True
            )
            return
        equaldex_key = itx.client.api_tokens["Equaldex"]
        querystring = {
            "regionid": country_id,
            "apiKey": equaldex_key,
            # "formatted": "true",
        }
        response = requests.get(
            "https://www.equaldex.com/api/region",
            params=querystring
        )
        response_api = response.text
        # returns ->  <pre>{"regions":{...}}</pre>  <- so you need to
        #  remove the <pre> and </pre> parts. It also has some
        #  <br \/>\r\n strings in there for some reason...? so uh
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
                await itx.response.send_message(
                    f"I'm sorry, I couldn't find '{country_id}'...\n"
                    f"Try 'GB' instead!",
                    ephemeral=True)
            else:
                await itx.response.send_message(
                    f"I'm sorry, I couldn't find '{country_id}'...",
                    ephemeral=True
                )
            return
        elif "error" in data:
            if country_id != country_id.upper():
                await itx.response.send_message(
                    f"Error code: {response.status_code}\n"
                    f"I'm sorry, I couldn't find '{country_id}'.\n"
                    f"Have you tried using uppercase? Try with "
                    f"`country_id:{country_id.upper()}`",
                    ephemeral=True
                )
            else:
                await itx.response.send_message(
                    f"Error code: {response.status_code}\n"
                    f"I'm sorry, I couldn't find '{country_id}'.",
                    ephemeral=True
                )
            return

        region = EqualDexRegion(data['regions']['region'])

        embed = discord.Embed(color=7829503, title=region.name)
        for issue in region.issues:
            if type(region.issues[issue]) is list:
                value = "No data"
            else:
                assert type(region.issues[issue]) is not list
                status = region.issues[issue]['current_status']
                value = status['value_formatted']
                # if status['value'] in [
                #     'Legal',
                #     'Equal',
                #     'No censorship',
                #     'surgery not required',
                #     "Sexual orientation and gender identity",
                #     "Recognized"
                # ]:
                #     value = "❤️ " + value
                # elif status['value'] in ["Illegal"]:
                #     value = "🚫 " + value
                # elif status['value'] in ["Not legally recognized",
                #                          "Not banned", "Varies by Region"]:
                #     value = "🟨 " + value
                # else:
                #     value = "➖ " + value
                status_description = \
                    status['description']
                description = region.issues[issue]['description']
                if len(status_description) > 0:
                    if len(status_description) > 200:
                        value += f" ({status_description[:200]}..."
                    else:
                        value += f" ({status_description})"
                elif len(description) > 0:
                    if len(description) > 200:
                        value += f" ({description[:200]}..."
                    else:
                        value += f" ({description})"
                if len(value) > 1024:
                    value = value[:1020] + "..."
            embed.add_field(
                name=region.issues[issue]['label'],
                value=value,
                inline=False,
            )
        embed.set_footer(text="For more info, click the button below,")
        view = EqualDexAdditionalInfo(region.url)
        await itx.response.send_message(
            embed=embed,
            view=view,
            ephemeral=True
        )

    @app_commands.command(name="math",
                          description="Ask Wolfram Alpha a question")
    async def math(self, itx: discord.Interaction[Bot], query: str):
        # todo: shorten function / split, and re-investigate the API
        #  docs to see if I can parse stuff better
        await itx.response.defer(ephemeral=True)
        if query.lower() in ["help", "what is this", "what is this?"]:
            await itx.followup.send(
                "This is a math command that connects to the Wolfram "
                "Alpha website! You can ask it math or science "
                "questions, and it will answer them for you! Kinda "
                "like an AI. It uses scientific data. Here are some "
                "example queries:\n"
                "- What is 9+10\n"
                "- What is the derivative of 4x^2+3x+5\n"
                "- What color is the sky?",
                ephemeral=True
            )
            return
        api_key = itx.client.api_tokens['Wolfram Alpha']
        params = {
            "appid": api_key,
            "input": query,
            "output": "json",
        }
        try:
            api_response: WolframResult = requests.get(
                "https://api.wolframalpha.com/v2/query",
                params=params
            ).json()
        except requests.exceptions.JSONDecodeError:
            await itx.followup.send(
                "Your input gave a malformed result! Perhaps it took "
                "too long to calculate...",
                ephemeral=True
            )
            return

        data: WolframQueryResult = api_response["queryresult"]
        if data.get("success", False):
            try:
                output_string = format_wolfram_success_output(data)
            except ValueError as ex:
                await itx.followup.send(
                    str(ex),
                    ephemeral=True
                )
                return

            view = SendPublicButtonMath()
            await itx.followup.send(
                output_string,
                view=view,
                ephemeral=True
            )
            await view.wait()
            if view.value is None:
                await itx.edit_original_response(view=None)
            return
        else:
            output_string = format_wolfram_error_output(data)
            await itx.followup.send(
                output_string,
                ephemeral=True,
            )
            return
        # await itx.followup.send(
        #     "debug; It seems you reached the end of the function without "
        #     "actually getting a response! Please report the query to "
        #     "MysticMia#7612",
        #     ephemeral=True
        # )

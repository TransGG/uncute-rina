from Uncute_Rina import *
from import_modules import *

report_message_reminder_unix = 0 #int(mktime(datetime.now().timetuple()))
selfies_delete_week_command_cooldown = 0

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
        "Celcius"    : [273.15, 1, "°C"],
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

def generateOutput(responses, author):
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

class SearchAddons(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    nameusage = app_commands.Group(name='nameusage', description='Get data about which names are used in the server')

    @nameusage.command(name="gettop", description="See how often different names occur in this server")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Search most-used usernames', value=1),
        discord.app_commands.Choice(name='Search most-used nicknames', value=2),
        discord.app_commands.Choice(name='Search nicks and usernames', value=3),
    ])
    async def nameusage_gettop(self, itx: discord.Interaction, mode: int):
        await itx.response.defer(ephemeral=True)
        sections = {}
        for member in itx.guild.members:
            member_sections = []
            if mode == 1: # most-used usernames
                names = [member.name]
            elif mode == 2 and member.nick is not None: # most-used nicknames
                names = [member.nick]
            elif mode == 3: # most-used nicks and usernames
                names = [member.name]
                if member.nick is not None:
                    names.append(member.nick)
            else:
                continue

            _pronouns = [
                "she", "her",
                "he", "him",
                "they", "them",
                "it", "its",
            ]
            pronouns = []
            for pronounx in _pronouns:
                for pronouny in _pronouns:
                    pronouns.append(pronounx + " " + pronouny)

            for index in range(len(names)):
                new_name = ""
                for char in names[index]:
                    if char.lower() in "abcdefghijklmnopqrstuvwxyz":
                        new_name += char
                    else:
                        new_name += " "

                for pronoun in pronouns:
                    _name_backup = new_name + " "
                    while new_name != _name_backup:
                        _name_backup = new_name
                        new_name = re.sub(pronoun, "", new_name, flags=re.IGNORECASE)

                names[index] = new_name

            def add(part):
                if part not in member_sections:
                    member_sections.append(part)

            for name in names:
                for section in name.split():
                    if section in member_sections:
                        pass
                    else:
                        parts = []
                        match = 1
                        while match:
                            match = re.search("[A-Z][a-z]*[A-Z]", section, re.MULTILINE)
                            if match:
                                caps = match.span()[1]-1
                                parts.append(section[:caps])
                                section = section[caps:]
                        if len(parts) != 0:
                            for part in parts:
                                add(part)
                            add(section)
                        else:
                            add(section)

            for section in member_sections:
                section = section.lower()
                if section in ["the", "any", "not"]:
                    continue
                if len(section) < 3:
                    continue
                if section in sections:
                    sections[section] += 1
                else:
                    sections[section] = 1

        sections = sorted(sections.items(), key=lambda x:x[1], reverse=True)
        pages = []
        for i in range(int(len(sections)/20+0.999)+1):
            result_page = ""
            for section in sections[0+20*i:20+20*i]:
                result_page += f"{section[1]} {section[0]}\n"
            if result_page == "":
                result_page = "_"
            pages.append(result_page)
        page = 0
        class Pages(discord.ui.View):
            class GetName(discord.ui.Modal, title="Search page with word"):
                def __init__(self, pages, embed_title, timeout=None):
                    super().__init__()
                    self.value = None
                    self.timeout = timeout
                    self.embed_title = embed_title
                    self.pages = pages
                    self.page = None

                    self.word = None
                    self.question_text = discord.ui.TextInput(label='What word to look up in the server name list?',
                                                              placeholder=f"The word you want to look up",
                                                              # style=discord.TextStyle.short,
                                                              # required=True
                                                              )
                    self.add_item(self.question_text)

                async def on_submit(self, itx: discord.Interaction):
                    self.value = 9  # failed; placeholder
                    self.word = self.question_text.value.lower()
                    for page_id in range(len(self.pages)):
                        # self.pages[page_id] returns ['15 nora\n13 rose\n9 brand\n8 george\n4 rina\n3 grace\n3 chroma\n2 eliza\n','1 cleo','_']
                        # split at \n and " " to get [["15", "nora"], ["13", "rose"], ["9", "brand"], ["8", "george"]] and compare self.word with the names
                        if self.word in [name.split(" ")[-1] for name in self.pages[page_id].split("\n")]:
                            self.page = int(page_id / 2)
                            break
                    else:
                        await itx.response.send_message(
                            content=f"I couldn't find '{self.word}' in any of the pages! Perhaps nobody chose this name!",
                            ephemeral=True)
                        return
                    result_page  = self.pages[self.page * 2]
                    result_page2 = self.pages[self.page * 2 + 1]
                    result_page   = result_page.replace(f" {self.word}\n", f" **__{self.word}__**\n")
                    result_page2 = result_page2.replace(f" {self.word}\n", f" **__{self.word}__**\n")
                    embed = discord.Embed(color=8481900, title=self.embed_title)
                    embed.add_field(name="Column 1", value=result_page)
                    embed.add_field(name="Column 2", value=result_page2)
                    embed.set_footer(text="page: " + str(self.page + 1) + " / " + str(int(len(self.pages) / 2)))
                    await itx.response.edit_message(embed=embed)
                    self.value = 1
                    self.stop()

            def __init__(self, pages, embed_title, timeout=None):
                super().__init__()
                self.value   = None
                self.timeout = timeout
                self.page    = 0
                self.pages   = pages
                self.embed_title = embed_title

            # When the confirm button is pressed, set the inner value to `True` and
            # stop the View from listening to more input.
            # We also send the user an ephemeral message that we're confirming their choice.
            @discord.ui.button(label='Previous', style=discord.ButtonStyle.blurple)
            async def previous(self, itx: discord.Interaction, _button: discord.ui.Button):
                # self.value = "previous"
                self.page -= 1
                if self.page < 0:
                    self.page = int(len(self.pages)/2)-1
                result_page = self.pages[self.page*2]
                result_page2 = self.pages[self.page*2+1]
                embed = discord.Embed(color=8481900, title=self.embed_title)
                embed.add_field(name="Column 1",value=result_page)
                embed.add_field(name="Column 2",value=result_page2)
                embed.set_footer(text="page: "+str(self.page+1)+" / "+str(int(len(self.pages)/2)))
                await itx.response.edit_message(embed=embed)

            @discord.ui.button(label='Next', style=discord.ButtonStyle.blurple)
            async def next(self, itx: discord.Interaction, _button: discord.ui.Button):
                self.page += 1
                if self.page >= int(len(self.pages)/2):
                    self.page = 0
                result_page = self.pages[self.page*2]
                result_page2 = self.pages[self.page*2+1]
                embed = discord.Embed(color=8481900, title=self.embed_title)
                embed.add_field(name="Column 1",value=result_page)
                embed.add_field(name="Column 2",value=result_page2)
                embed.set_footer(text="page: "+str(self.page+1)+" / "+str(int(len(self.pages)/2)))
                await itx.response.edit_message(embed=embed)

            @discord.ui.button(label='Find my name', style=discord.ButtonStyle.blurple)
            async def find_name(self, itx: discord.Interaction, _button: discord.ui.Button):
                send_one = Pages.GetName(self.pages, self.embed_title)
                await itx.response.send_modal(send_one)
                await send_one.wait()
                if send_one.value in [None, 9]:
                    pass
                else:
                    self.page = send_one.page

        result_page = pages[page]
        result_page2 = pages[page+1]
        embed_title = f'Most-used {"user" if mode==1 else "nick" if mode==2 else "usernames and nick"}names leaderboard!'
        embed = discord.Embed(color=8481900, title=embed_title)
        embed.add_field(name="Column 1",value=result_page)
        embed.add_field(name="Column 2",value=result_page2)
        embed.set_footer(text="page: "+str(page+1)+" / "+str(int(len(pages)/2)))
        view = Pages(pages, embed_title, timeout=60)
        await itx.followup.send(f"",embed=embed, view=view,ephemeral=True)
        await view.wait()
        if view.value is None:
            await itx.edit_original_response(view=None)

    @nameusage.command(name="name", description="See how often different names occur in this server")
    @app_commands.describe(name="What specific name are you looking for?")
    @app_commands.choices(type=[
        discord.app_commands.Choice(name='usernames', value=1),
        discord.app_commands.Choice(name='nicknames', value=2),
        discord.app_commands.Choice(name='Search both nicknames and usernames', value=3),
    ])
    async def nameusage_name(self, itx: discord.Interaction, name: str, type: int, public: bool = False):
        await itx.response.defer(ephemeral=not public)
        count = 0
        type_string = ""
        if type == 1: # usernames
            for member in itx.guild.members:
                if name.lower() in member.name.lower():
                    count += 1
            type_string = "username"
        elif type == 2: # nicknames
            for member in itx.guild.members:
                if member.nick is not None:
                    if name.lower() in member.nick.lower():
                        count += 1
            type_string = "nickname"
        elif type == 3: # usernames and nicknames
            for member in itx.guild.members:
                if member.nick is not None:
                    if name.lower() in member.nick.lower() or name.lower() in member.name.lower():
                        count += 1
                elif name.lower() in member.name.lower():
                    count += 1
            type_string = "username or nickname"
        await itx.followup.send(f"I found {count} people with '{name.lower()}' in their {type_string}",ephemeral=not public)

    @app_commands.command(name="equaldex", description="Find info about LGBTQ+ laws in different countries!")
    @app_commands.describe(country_id="What country do you want to know more about? (GB, US, AU, etc.)")
    async def equaldex(self, itx: discord.Interaction, country_id: str):
        illegal_characters = ""
        for char in country_id:
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
        jsonizing_table = str.maketrans({
            r"<br \/>\r\n":r"\n",
            "<pre>":"",
            "</pre>":""
        })
        response_api = response_api.translate(jsonizing_table)
        data = json.loads(response_api)
        if "error" in data:
            if country_id.lower() == "uk":
                await itx.response.send_message(f"I'm sorry, I couldn't find '{country_id}'...\nTry 'GB' instead!", ephemeral=True)
            else:
                await itx.response.send_message(f"I'm sorry, I couldn't find '{country_id}'...",ephemeral=True)
            return

        class Region:
            def __init__(self, data):
                self.id = data['region_id']
                self.name = data['name']
                self.continent = data['continent']
                self.url = data['url']
                self.issues = data['issues']

        region = Region(data['regions']['region'])

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
        class MoreInfo(discord.ui.View):
            def __init__(self, url):
                super().__init__()
                link_button = discord.ui.Button(style = discord.ButtonStyle.gray,
                                                label = "More info",
                                                url = url)
                self.add_item(link_button)
        view = MoreInfo(region.url)
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
            await itx.response.send_message("Your query cannot contain an ampersand (&/and symbol)! (it can mess with the URL)", ephemeral=True)
            return
        query = query.replace("+", " plus ") # plusses are interpreted as a spacebar in urls. In LaTeX, that can mean multiply
        api_key = self.client.api_tokens['Wolfram Alpha']
        try:
            data = requests.get(
                f"http://api.wolframalpha.com/v2/query?appid={api_key}&input={query}&output=json").json()
        except requests.exceptions.JSONDecodeError:
            await itx.followup.send("Your input gave a malformed result! Perhaps it took too long to calculate...", ephemeral=True)
            return
        
        class SendPublic(discord.ui.View):
            def __init__(self, client: Bot, timeout=180):
                super().__init__()
                self.value = None
                self.client = client
                self.timeout = timeout

            @discord.ui.button(label='Send Publicly', style=discord.ButtonStyle.gray)
            async def send_publicly(self, itx: discord.Interaction, _button: discord.ui.Button):
                self.value = 1
                await itx.response.edit_message(content="Sent successfully!")
                cmd_mention = self.client.get_command_mention("math")
                await itx.followup.send(f"**{itx.user.mention} shared a {cmd_mention} output:**\n" + itx.message.content, ephemeral=False, allowed_mentions=discord.AllowedMentions.none())


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
                warnings.append(data["warnings"]["text"])
            if len(data.get("timedout", "")) > 0:
                warnings.append("Timed out: " + data["timedout"].replace(",", ", "))
            if len(data.get("timedoutpods", "")) > 0:
                warnings.append("Timed out pods: " + data["timedout"].replace(",", ", "))
            if len(warnings) > 0:
                warnings = "\nWarnings:\n> " + '\n> '.join(warnings)
            else:
                warnings = ""
            view = SendPublic(self.client)
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
        await itx.followup.send("debug; It seems you reached the end of the function without "
                                "actually getting a response! Please report the query to MysticMia#7612", ephemeral=True)

class OtherAddons(commands.Cog):
    def __init__(self, client: Bot):
        global RinaDB
        self.client = client
        RinaDB = client.RinaDB
        self.headpatWait = 0

    @commands.Cog.listener()
    async def on_message(self, message):
        global report_message_reminder_unix
        try: # mention targeted user if added to mod-ticket with /add target:@user
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
        except AttributeError:
            pass

        if message.author.bot:
            return

        #random cool commands
        self.headpatWait += 1
        if self.headpatWait >= 1000:
            ignore = False
            if type(message.channel) is discord.Thread:
                if message.channel.parent == 987358841245151262: # <#welcome-verify>
                    ignore = True
            if message.channel.name.startswith('ticket-') or message.channel.name.startswith('closed-'):
                ignore = True
            if message.channel.category.id in [959584962443632700, 959590295777968128, 959928799309484032, 1041487583475138692,
                                               995330645901455380, 995330667665707108]:
                # <#Bulletin Board>, <#Moderation Logs>, <#Verifier Archive>, <#Events>, <#Open Tickets>, <#Closed Tickets>
                ignore = True
            if message.guild.id in [981730502987898960]: # don't send in Mod server
                ignore = True
            if not ignore:
                self.headpatWait = 0
                try:
                    await message.add_reaction("<:TPF_02_Pat:968285920421875744>") #headpatWait
                except discord.errors.HTTPException:
                    await log_to_guild(self.client, message.guild, f'**:warning: Warning: **Couldn\'t add pat reaction to {message.jump_url}. They might have blocked Rina...')
                    try:
                        await message.add_reaction("☺") # relaxed
                    except discord.errors.Forbidden:
                        pass

        for staff_role_mention in ["<@&981735650971775077>", "<@&1012954384142966807>", "<@&981735525784358962>"]:
            if staff_role_mention in message.content:
                time_now = int(mktime(datetime.now().timetuple())) # get time in unix
                if time_now - report_message_reminder_unix > 900: # 15 minutes
                    await Tags().send_report_info("report", message.channel, self.client, additional_info=[message.author.name, message.author.id])
                    report_message_reminder_unix = time_now
                    break

        if self.client.user.mention in message.content.split():
            msg = message.content.lower()
            if ((("cute" or "cutie" or "adorable" in msg) and "not" in msg) or "uncute" in msg) and "not uncute" not in msg:
                try:
                    await message.add_reaction("<:this:960916817801535528>")
                except:
                    await log_to_guild(self.client, message.guild, f'**:warning: Warning: **Couldn\'t add pat reaction to {message.jump_url}')
                    raise
            elif "cutie" in msg or "cute" in msg:
                responses = [
                    "I'm not cute >_<",
                    "I'm not cute! I'm... Tough! Badass!",
                    "Nyaa~",
                    "Who? Me? No you're mistaken.",
                    "I very much deny the cuteness of someone like myself",
                    "If you think I'm cute, then you must be uber-cute!!",
                    "I don't think so.",
                    "Haha. Good joke. Tell me another tomorrow",
                    "Ehe, cutie what do u need help with?",
                    "No, I'm !cute.",
                    "You too!",
                    "No, you are <3",
                    "[shocked] Wha- w. .. w what?? .. NOo? no im nott?\nwhstre you tslking about?",
                    "Oh you were talking to me? I thought you were talking about everyone else here,",
                    "Nope. I doubt it. There's no way I can be as cute as you",
                    "Maybe.. Maybe I am cute.",
                    "If the sun was dying, would you still think I was cute?",
                    "Awww. Thanks sweety, but you've got the wrong number",
                    ":joy: You *reaaally* think so? You've gotta be kidding me.",
                    "If you're gonna be spamming this, .. maybe #general isn't the best channel for that.",
                    "You gotta praise those around you as well. "+(message.author.nick or message.author.name)+", for example, is very cute.",
                    "Oh by the way, did I say "+(message.author.nick or message.author.name)+" was cute yet? I probably didn't. "+(message.author.nick or message.author.name)+"? You're very cute",
                    "Such nice weather outside, isn't it? What- you asked me a question?\nNo you didn't, you're just talking to youself.",
                    "".join(random.choice("acefgilrsuwnopacefgilrsuwnopacefgilrsuwnop;;  ") for _ in range(random.randint(10,25))), # 3:2 letters to symbols
                    "Oh I heard about that! That's a way to get randomized passwords from a transfem!",
                    "Cuties are not gender-specific. For example, my cat is a cutie!\nOh wait, species aren't the same as genders. Am I still a catgirl then? Trans-species?",
                    "...",
                    "Hey that's not how it works!",
                    "Hey my lie detector said you are lying.",
                    "You know i'm not a mirror, right?",
                    "*And the oscar for cutest responses goes to..  YOU!!*",
                    "No I am not cute",
                    "k",
                    (message.author.nick or message.author.name)+", stop lying >:C",
                    "BAD!",
                    "You're also part of the cuties set",
                    "https://cdn.discordapp.com/emojis/920918513969950750.webp?size=4096&quality=lossless",
                    "[Checks machine]; Huh? Is my lie detector broken? I should fix that..",
                    "Hey, you should be talking about yourself first! After all, how do you keep up with being such a cutie all the time?"]
                respond = random.choice(responses)
                if respond == "BAD!":
                    await message.channel.send("https://cdn.discordapp.com/emojis/902351699182780468.gif?size=56&quality=lossless", allowed_mentions=discord.AllowedMentions.none())
                await message.channel.send(respond, allowed_mentions=discord.AllowedMentions.none())
            else:
                cmd_mention = self.client.get_command_mention("help")
                await message.channel.send(f"I use slash commands! Use /command  and see what cool things might pop up! or try {cmd_mention}\nPS: If you're trying to call me cute: no, I'm not", delete_after=8)

    @app_commands.command(name="say",description="Force Rina to repeat your wise words")
    @app_commands.describe(text="What will you make Rina repeat?",
                           reply_to_interaction="Show who sent the message?")
    async def say(self, itx: discord.Interaction, text: str, reply_to_interaction: bool = False):
        if not is_staff(itx):
            await itx.response.send_message("Hi. sorry.. It would be too powerful to let you very cool person use this command.",ephemeral=True)
            return
        if reply_to_interaction:
            await itx.response.send_message(text, ephemeral=False, allowed_mentions=discord.AllowedMentions.none())
            return
        cmd_mention = self.client.get_command_mention("editguildinfo")
        vc_log = await self.client.get_guild_info(itx.guild, "vcLog", log=[
            itx, "Couldn't send your message. You can't send messages in this server because the bot setup seems incomplete\n"
            f"Use {cmd_mention} `mode:11` to fix this!"])
        try:
            # vcLog      = guild["vcLog"]
            log_channel = itx.guild.get_channel(vc_log)
            await log_channel.send(f"{itx.user.nick or itx.user.name} ({itx.user.id}) said a message using Rina: {text}", allowed_mentions=discord.AllowedMentions.none())
            text = text.replace("[[\\n]]","\n").replace("[[del]]","")
            await itx.channel.send(f"{text}", allowed_mentions=discord.AllowedMentions(everyone=False,users=True,roles=True,replied_user=True))
        except discord.Forbidden:
            await itx.response.send_message("Forbidden! I can't send a message in this channel/thread because I can't see it or because I'm not added to it yet!\n(Add me to the thread by mentioning me, or let Rina see this channel)",ephemeral=True)
            return
        except:
            await itx.response.send_message("Oops. Something went wrong!",ephemeral=True)
            raise
        #No longer necessary: this gets caught by the on_app_command_error() event in the main file.
        await itx.response.send_message("Successfully sent!", ephemeral=True)

    @app_commands.command(name="compliment", description="Complement someone fem/masc/enby")
    @app_commands.describe(user="Who do you want to compliment?")
    async def compliment(self, itx: discord.Interaction, user: discord.User):
        # discord.User because discord.Member gets errors.TransformerError in DMs (dunno why i'm accounting for that..)
        try:
            user: discord.Member # make IDE happy, i guess
            userroles = user.roles[:]
        except AttributeError:
            await itx.response.send_message("Aw man, it seems this person isn't in the server. I wish I could compliment them but they won't be able to see it!", ephemeral=True)
            return

        async def call(itx, user, type):
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
                    "Beep boop :zap: Oh no! my circuits overloaded! Her cuteness was too much for me to handle!",
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
                    "Beep boop :zap: Oh no! my circuits overloaded! His aura was so strong that I couldn't generate a cool compliment!",
                    

                ],
                "they_quotes": [
                    "I can tell that you are a very special and talented person!",
                    "Their, their... ",
                ],
                "it_quotes": [
                    "I bet you do the crossword puzzle in ink!",
                ],
                "unisex_quotes": [ #unisex quotes are added to each of the other quotes later on.
                    "Hey I have some leftover cookies.. \\*wink wink\\*",
                    # "_Let me just hide this here-_ hey wait, are you looking?!", #it were meant to be cookies TwT
                    "Would you like a hug?",
                    "Would you like to walk in the park with me? I gotta walk my catgirls",
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
                    "You have a contagious positive attitude that lifts up those around you.",
                    "Your positive energy is infectious and makes everyone feel welcomed!",
                    "You have a great sense of style and always look so put together <3",
                    "You are a truly unique and wonderful person!",
                ]
            }
            type = {
                "she/her"   : "fem_quotes",
                "he/him"    : "masc_quotes",
                "they/them" : "they_quotes",
                "it/its"    : "it_quotes",
                "unisex"    : "unisex_quotes", #todo
            }[type]

            for x in quotes:
                if x == "unisex_quotes":
                    continue
                else:
                    quotes[x] += quotes["unisex_quotes"]

            collection = RinaDB["complimentblacklist"]
            query = {"user": user.id}
            search = collection.find_one(query)
            if search is None:
                blacklist = []
            else:
                blacklist = search["list"]
            for string in blacklist:
                dec = 0
                for x in range(len(quotes[type])):
                    if string in quotes[type][x-dec]:
                        del quotes[type][x-dec]
                        dec += 1
            if len(quotes[type]) == 0:
                quotes[type].append("No compliment quotes could be given... This person seems to have blacklisted every quote.")

            base = f"{itx.user.mention} complimented {user.mention}!\n"
            if itx.response.is_done():
                # await itx.edit_original_response(content=base+random.choice(quotes[type]), view=None)
                await itx.followup.send(content=base+random.choice(quotes[type]), allowed_mentions=discord.AllowedMentions(everyone=False, users=[user], roles=False, replied_user=False))
            else:
                await itx.response.send_message(base+random.choice(quotes[type]), allowed_mentions=discord.AllowedMentions(everyone=False, users=[user], roles=False, replied_user=False))
        async def confirm_gender():
            # Define a simple View that gives us a confirmation menu
            class Confirm(discord.ui.View):
                def __init__(self, timeout=None):
                    super().__init__()
                    self.value = None
                    self.timeout = timeout

                # When the confirm button is pressed, set the inner value to `True` and
                # stop the View from listening to more input.
                # We also send the user an ephemeral message that we're confirming their choice.
                @discord.ui.button(label='She/Her', style=discord.ButtonStyle.green)
                async def feminine(self, itx: discord.Interaction, _button: discord.ui.Button):
                    self.value = "she/her"
                    await itx.response.edit_message(content='Selected She/Her pronouns for compliment', view=None)
                    self.stop()

                @discord.ui.button(label='He/Him', style=discord.ButtonStyle.green)
                async def masculine(self, itx: discord.Interaction, _button: discord.ui.Button):
                    self.value = "he/him"
                    await itx.response.edit_message(content='Selected He/Him pronouns for the compliment', view=None)
                    self.stop()

                @discord.ui.button(label='They/Them', style=discord.ButtonStyle.green)
                async def enby_them(self, itx: discord.Interaction, _button: discord.ui.Button):
                    self.value = "they/them"
                    await itx.response.edit_message(content='Selected They/Them pronouns for the compliment', view=None)
                    self.stop()

                @discord.ui.button(label='It/Its', style=discord.ButtonStyle.green)
                async def enby_its(self, itx: discord.Interaction, _button: discord.ui.Button):
                    self.value = "it/its"
                    await itx.response.edit_message(content='Selected It/Its pronouns for the compliment', view=None)
                    self.stop()

                @discord.ui.button(label='Unisex/Unknown', style=discord.ButtonStyle.grey)
                async def unisex(self, itx: discord.Interaction, _button: discord.ui.Button):
                    self.value = "unisex"
                    await itx.response.edit_message(content='Selected Unisex/Unknown gender for the compliment', view=None)
                    self.stop()

            view = Confirm(timeout=60)
            await itx.response.send_message(f"{user.mention} doesn't have any pronoun roles! Which pronouns would like to use for the compliment?", view=view,ephemeral=True)
            await view.wait()
            if view.value is None:
                await itx.edit_original_response(content=':x: Timed out...', view=None)
            else:
                await call(itx, user, view.value)

        roles = ["he/him", "she/her", "they/them", "it/its"]
        random.shuffle(userroles) # pick a random order for which pronoun role to pick
        for role in userroles:
            if role.name.lower() in roles:
                await call(itx, user, role.name.lower())
                return
        await confirm_gender()

    @app_commands.command(name="complimentblacklist", description="If you dislike words in certain compliments")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Add a string to your compliments blacklist', value=1),
        discord.app_commands.Choice(name='Remove a string from your compliments blacklist', value=2),
        discord.app_commands.Choice(name='Check your blacklisted strings', value=3)
    ])
    @app_commands.describe(string="What sentence or word do you want to blacklist? (eg: 'good girl' or 'girl')")
    async def complimentblacklist(self, itx: discord.Interaction, mode: int, string: str = None):
        if mode == 1: # add an item to the blacklist
            if string is None:
                await itx.response.send_message("With this command, you can blacklist a section of text in compliments. "
                                                "For example, if you don't like being called 'Good girl', you can "
                                                "blacklist this compliment by blacklisting 'good' or 'girl'. \n"
                                                "Note: it's case sensitive", ephemeral=True)
                return
            if len(string) > 150:
                await itx.response.send_message("Please make strings shorter than 150 characters...",ephemeral=True)
                return
            collection = RinaDB["complimentblacklist"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                blacklist = []
            else:
                blacklist = search['list']
            blacklist.append(string)
            collection.update_one(query, {"$set":{f"list":blacklist}}, upsert=True)
            await itx.response.send_message(f"Successfully added {repr(string)} to your blacklist. ({len(blacklist)} item{'s'*(len(blacklist)!=1)} in your blacklist now)",ephemeral=True)

        elif mode == 2: # Remove item from black list
            if string is None:
                cmd_mention = self.client.get_command_mention("complimentblacklist")
                await itx.response.send_message(f"Type the id of the string you want to remove. To find the id, type {cmd_mention} `mode:Check`.", ephemeral=True)
                return
            try:
                string = int(string)
            except ValueError:
                await itx.response.send_message("To remove a string from your blacklist, you must give the id of the string you want to remove. This should be a number... You didn't give a number...", ephemeral=True)
                return
            collection = RinaDB["complimentblacklist"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                await itx.response.send_message("There are no items on your blacklist, so you can't remove any either...",ephemeral=True)
                return
            blacklist = search["list"]

            try:
                del blacklist[string]
            except IndexError:
                cmd_mention = self.client.get_command_mention("complimentblacklist")
                await itx.response.send_message(f"Couldn't delete that ID, because there isn't any item on your list with that ID.. Use {cmd_mention} `mode:Check` to see the IDs assigned to each item on your list",ephemeral=True)
                return
            collection.update_one(query, {"$set":{f"list":blacklist}}, upsert=True)
            await itx.response.send_message(f"Successfully removed '{string}' from your blacklist. Your blacklist now contains {len(blacklist)} string{'s'*(len(blacklist)!=1)}.", ephemeral=True)
        
        elif mode == 3: # check
            collection = RinaDB["complimentblacklist"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                await itx.response.send_message("There are no strings in your blacklist, so.. nothing to list here....",ephemeral=True)
                return
            blacklist = search["list"]
            length = len(blacklist)

            ans = []
            for id in range(length):
                ans.append(f"`{id}`: {blacklist[id]}")
            ans = '\n'.join(ans)
            await itx.response.send_message(f"Found {length} string{'s'*(length!=1)}:\n{ans}",ephemeral=True)

    @app_commands.command(name="roll", description="Roll a die or dice with random chance!")
    @app_commands.describe(dice="How many dice do you want to roll?",
                           faces="How many sides does every die have?",
                           mod="Do you want to add a modifier? (add 2 after rolling the dice)",
                           advanced="Roll more advanced! example: 1d20+3*2d4. Overwrites dice/faces given; 'help' for more")
    async def roll(self, itx: discord.Interaction, 
                   dice: app_commands.Range[int, 1, 999999],
                   faces: app_commands.Range[int, 1, 999999], 
                   public: bool = False, mod: int = None, advanced: str = None):
        hide = False
        if advanced is None:
            await itx.response.defer(ephemeral=not public)
            rolls = []
            for die in range(dice):
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
            def prod(list: list):
                a = 1
                for x in list:
                    a *= x
                return a

            def generate_roll(query: str):
                # print(query)
                temp = query.split("d")
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
                remainder = temp[1][len(faces):]
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
                out += [' + '.join([str(prod(section)) for section in result])]
            out += [str(sum([prod(section) for section in result]))]
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

    async def print_help_text(self, itx):
        out = f"""\
Hi there! This bot has a whole bunch of commands. Let me introduce you to some:
{self.client.get_command_mention('add_poll_reactions')}: Add an up-/downvote emoji to a message (for voting)
{self.client.get_command_mention('commands')} or {self.client.get_command_mention('help')}: See this help page
{self.client.get_command_mention('compliment')}: Rina can compliment others (matching their pronoun role)
{self.client.get_command_mention('convert_unit')}: Convert a value from one to another! Distance, speed, currency, etc.
{self.client.get_command_mention('dictionary')}: Search for an lgbtq+-related or dictionary term!
{self.client.get_command_mention('equaldex')}: See LGBTQ safety and rights in a country (with API)
{self.client.get_command_mention('math')}: Ask Wolfram|Alpha for math or science help
{self.client.get_command_mention('nameusage gettop')}: See how many people are using the same name
{self.client.get_command_mention('pronouns')}: See someone's pronouns or edit your own
{self.client.get_command_mention('qotw')} and {self.client.get_command_mention('developer_request')}: Suggest a Question Of The Week or Bot Suggestion to staff
{self.client.get_command_mention('reminder reminders')}: Make or see your reminders
{self.client.get_command_mention('roll')}: Roll some dice with a random result
{self.client.get_command_mention('tag')}: Get information about some of the server's extra features
{self.client.get_command_mention('todo')}: Make, add, or remove items from your to-do list
{self.client.get_command_mention('toneindicator')}: Look up which tone tag/indicator matches your input (eg. /srs)

Make a custom voice channel by joining "Join to create VC" (use {self.client.get_command_mention('tag')} `tag:customvc` for more info)
{self.client.get_command_mention('editvc')}: edit the name or user limit of your custom voice channel
{self.client.get_command_mention('vctable about')}: Learn about making your voice chat more on-topic!
"""
# Check out the #join-a-table channel: In this channel, you can claim a channel for roleplaying or tabletop games for you and your group!
# The first person that joins/creates a table gets a Table Owner role, and can lock, unlock, or close their table.
# {self.client.get_command_mention('table lock')}, {self.client.get_command_mention('table unlock')}, {self.client.get_command_mention('table close')}
# You can also transfer your table ownership to another table member, after they joined your table: {self.client.get_command_mention('table newowner')}\
# """
        await itx.response.send_message(out, ephemeral=True)

    @app_commands.command(name="help", description="A help command to learn more about me!")
    async def help(self, itx: discord.Interaction):
        await self.print_help_text(itx)

    @app_commands.command(name="commands", description="A help command to learn more about me!")
    async def commands(self, itx: discord.Interaction):
        await self.print_help_text(itx)

    @app_commands.command(name="delete_week_selfies", description="Remove selfies and messages older than 7 days")
    async def delete_week_selfies(self, itx: discord.Interaction):
        global selfies_delete_week_command_cooldown
        if not is_staff(itx):
            await itx.response.send_message("You don't have permissions to use this command. (for ratelimit reasons)", ephemeral=True)
            return
        time_now = int(mktime(datetime.now().timetuple()))  # get time in unix
        if time_now - selfies_delete_week_command_cooldown < 86400:  # 1 day
            await itx.response.send_message("This command has already been used yesterday! Please give it some time and prevent ratelimiting.", ephemeral=True)
            return
        if 'selfies' != itx.channel.name or not isinstance(itx.channel, discord.channel.TextChannel):
            await itx.response.send_message("You need to send this in a text channel named \"selfies\"", ephemeral=True)
            return
        output = "Attempting deletion...\n"
        await itx.response.send_message(output+"...", ephemeral=True)
        try:
            await log_to_guild(self.client, itx.guild,f"{itx.user} ({itx.user.id}) deleted messages older than 7 days, in {itx.channel.mention} ({itx.channel.id}).")

            message_delete_count = 0
            async for message in itx.channel.history(limit=None, before = datetime.now()-timedelta(days=6,hours=23,minutes=30), oldest_first=True):
                message_date = int(mktime(message.created_at.timetuple()))
                if time_now-message_date > 7*86400: # 7 days ; technically redundant due to loop's "before" kwarg, but better safe than sorry
                    if "[info]" in message.content.lower():
                        class Interaction:
                            def __init__(self, member: discord.Member):
                                self.user = member
                                self.guild = member.guild
                        if is_staff(Interaction(message.author)): # nested to save having to look through function 1000 times
                            continue
                    await message.delete()
                    # print("----Deleted---- ["+str(message.created_at)+f"] {message.author}: {message.content}")
                    message_delete_count += 1
                    if message_delete_count % 50 == 0:
                        try:
                            await itx.edit_original_response(content=output+f"\nRemoved {message_delete_count} messages older than 7 days in {itx.channel.mention} so far...")
                        except discord.errors.HTTPException:
                            pass # ephemeral message timed out or something..
                    continue
                # print("++++Not deleted++++ ["+str(message.created_at)+f"] {message.author}: {message.content}")

            selfies_delete_week_command_cooldown = time_now
            await itx.followup.send(f"Removed {message_delete_count} messages older than 7 days!", ephemeral=False)
        except:
            await itx.followup.send("Something went wrong!")
            raise

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
        #      {"Celcius": [273.15, 1],
        #       "Fahrenheit": [459.67, 1.8]}
        # x = (273.15 + C degrees Celcius) / 1
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
                                 upvote_emoji: str, downvote_emoji: str, neutral_emoji: str = None):
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

        def get_emoji(client: Bot, emoji_str: str):
            if emoji_str is discord.utils.MISSING:
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
                if None:
                    return None
                if not emoji.is_usable():
                    return None
                return emoji

        upvote_emoji = get_emoji(self.client, upvote_emoji)
        if upvote_emoji is None:
            errors.append("- I can't use this upvote emoji! (perhaps it's a nitro emoji)")

        downvote_emoji = get_emoji(self.client, downvote_emoji)
        if downvote_emoji is None:
            errors.append("- I can't use this downvote emoji! (perhaps it's a nitro emoji)")

        if neutral_emoji is not discord.utils.MISSING:
            neutral_emoji = get_emoji(self.client, neutral_emoji)
            if neutral_emoji is None:
                errors.append("- I can't use this neutral emoji! (perhaps it's a nitro emoji)")

        if itx.guild.id != self.client.staff_server_id:
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

async def setup(client):
    await client.add_cog(OtherAddons(client))
    await client.add_cog(SearchAddons(client))

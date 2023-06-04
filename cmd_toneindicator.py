from Uncute_Rina import *
from import_modules import *

class ToneIndicator(commands.Cog):
    @app_commands.command(name="toneindicator",description="Look for the definition of a tone indicator")
    @app_commands.describe(mode="Choose a search method, eg. /p -> platonic; or vice versa",
                           string="This is your search query. What do you want to look for?",
                           public="Do you want to share the search results with the rest of the channel? (True=yes)")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='definition', value=1),
        discord.app_commands.Choice(name='exact acronym', value=2),
        discord.app_commands.Choice(name='rough acronym', value=3),
    ])
    async def toneindicator(self, itx: discord.Interaction, mode: int, string: str, public: bool = False):
        tone_indicators = {
            "excited" : ["/!","/exc"],
            "alterous" : ["/a","/ars"],
            "affectionate" : ["/a","/aff"],
            "asking for a friend" : ["/afaf"],
            "am i the a**hole?" : ["/aita"],
            "an order" : ["/ao"],
            "ask to tag" : ["/att"],
            "a vent" : ["/av"],
            "at you" : ["/ay"],
            "bitter / bitterly" : ["/b"],
            "bragging / flex" : ["/br","/fx"],
            "copypasta" : ["/c","/copy"],
            "calm / calmly" : ["/calm"],
            "clickbait" : ["/cb"],
            "celebratory" : ["/cel"],
            "coping joke" : ["/cj"],
            "comforting" : ["/co","/cf"],
            "concerned" : ["/co"],
            "curious/curiously" : ["/curi"],
            "content warning" : ["/cw"],
            "direct" : ["/dir"],
            "do not comment" : ["/dnc"],
            "do not interract" : ["/dni"],
            "educational" : ["/edu"],
            "exageration" : ["/ex"],
            "fake" : ["/f"],
            "familial (affectionate)" : ["/fam"],
            "fiction / fictional" : ["/fic"],
            "flirting" : ["/fl"],
            "gentle / gently" : ["/gentle"],
            "genuine" : ["/gen","/genq","/g","/gq"],
            "genuine suggestion" : ["/gs","/gens"],
            "half-joking, This tag can be difficult to interpet, and is best thought of as 'not serious': the intent is serious, but "
                "the statement is not literally true. Examples: 'for legal reasons, this is a joke', 'haha im kidding; unless.. :>'" : ["/hj"],
            "half jokingly overreacting" : ["/hjov"],
            "half serious" : ["/hsrs"],
            "hyperbole" : ["/hyp","/hyb","/hy"],
            "hypothetical": ["/hyp"],
            "inside joke" : ["/ij"],
            "irrelevant" : ["/irre"],
            "information or informing" : ["/in","/info"],
            "indirect" : ["/ind"],
            "joke / joking" : ["/j"],
            "just kidding" : ["/jk"],
            "jokingly prideful" : ["/jpr"],
            "half jokingly prideful" : ["/hjpr"],
            "joke question" : ["/jq"],
            "jokingly overreacting" : ["/jov"],
            "just so you know":["jsyk"],
            "just wondering" : ["/jw"],
            "keysmash semhsakakeysmamshma" : ["/key"],
            "lyrics" : ["/l","/ly","/lyr"],
            "lying / not (telling) the truth" : ["/lying"],
            "literally" : ["/li"],
            "light-hearted" : ["/lh"],
            "light-hearted sarcasm" : ["/lhs"],
            "a little upset" : ["/lu"],
            "lovingly" : ["/lv"],
            "metaphorically / metaphor" : ["/m"],
            "mad" : ["/m","/mad"],
            "messing around  or  manifesting" : ["/ma"],
            "major joke" : ["/mj"],
            "not a brag / flex" : ["/nabr","/nafx"],
            "not an order" : ["/nao"],
            "not a question / statement" : ["/naq","/st","/state"],
            "not a vent" : ["/nav"],
            "not at you" : ["/nay"],
            "for when you're vagueposting or venting, but it's directed at nobody here (none of your followers)" : ["/nbh"],
            "not being rude" : ["/nbr"],
            "nobody specific" : ["/nbs"],
            "nobody you know" : ["/nbyk"],
            "negative connotation" : ["/neg","/nc"],
            "neutral connotation" : ["/neu"],
            "not fake" : ["/nf"],
            "not flirting" : ["/nfl"],
            "not forced to answer" : ["/nfta","/nf"],
            "not mad / not upset" : ["/nm"],
            "not mad at you, to specify that someone isnt mad at someone else" : ["/nmay"],
            "not passive aggressive" : ["/npa"],
            "not prideful" : ["/npr"],
            "not subtweeting" : ["/nsb", "/nst"],
            "non-sexual intent" : ["/nsx","/nx","/nsxs"],
            "non-serious / not serious" : ["/nsrs"],
            "not a serious question" : ["/nsrsq"],
            "not yelling" : ["/ny"],
            "observation" : ["/ob"],
            "off topic" : ["/ot"],
            "it's okay to ask for reassurance" : ["/otr"],
            "it's okay to laugh" : ["/otl"],
            "it's okay to interract" : ["/oti"],
            "outraged" : ["/outr"],
            "platonic" : ["/p"],
            "passive aggressive" : ["/pa"],
            "playful" : ["/pf"],
            "playfully mad" : ["/pm"],
            "prideful" : ["/pr"],
            "half prideful" : ["/hpr"],
            "please interract" : ["/pi"],
            "please laugh" : ["/pl"],
            "paraphrase" : ["/para"],
            "positive connotation (eg. \"I don't mean this in a bad way\")" : ["/pos","/pc"],
            "quote" : ["/q"],
            "queerplatonic" : ["/qp"],
            "romantic" : ["/r"],
            "random" : ["/ra"],
            "reference" : ["/ref"],
            "rhetorical question" : ["/rh","/rt","/rtq"],
            "sarcastic / sarcasm / sarcastically" : ["/s","/sarc"],
            "safe" : ["/safe"],
            "for when you're vagueposting or venting, but it's directed at somebody here (x of your followers)" : ["/sbh"],
            "subtweeting" : ["/sbtw"],
            "serious" : ["/srs"],
            "sexual intent" : ["/sx","/x","/xxx"],
            "teasing" : ["/t"],
            "tangent" : ["/tan"],
            "threat" : ["/th"],
            "tic, for when something typed out was unintentional due to being a tic" : ["/tic"],
            "today I F'ed up" : ["/tifu"],
            "to self" : ["/ts"],
            "trigger warning" : ["/tw"],
            "upset" : ["/u"],
            "unintentional" : ["/unin"],
            "unrelated" : ["/unre"],
            "vague" : ["/v","/vague"],
            "very upset" : ["/vu"],
            "warm / warmth" : ["/w"],
        }

        result = False
        results = []
        result_str = ""
        if mode == 1:
            for key in tone_indicators:
                if string.replace("-"," ") in key.replace("-"," ") or string.replace("-","") in key.replace("-",""):
                    overlaps = []
                    overlapper = ""
                    for key1 in tone_indicators:
                        if key == key1:
                            continue
                        for indicator1 in tone_indicators[key1]:
                            if indicator1 in tone_indicators[key]:
                                overlapper = indicator1
                                overlaps.append(key1)
                                break
                    results.append([key,tone_indicators[key],overlapper,overlaps])
                    result = True
            if result:
                result_str += f"I found {len(results)} result{'s'*(len(results)!=1)} with '{string}' in:\n"
            for x in results:
                y = ""
                if len(x[3]) > 0:
                    y = f"\n   + {len(x[3])} overlapper{'s'*(len(x[3])!=1)}:\n    [ {x[2]}: {', '.join(x[3])} ]"
                result_str += f"> \"{x[0]}\": {', '.join(x[1])}"+y+"\n"
        elif mode == 2:
            for key in tone_indicators:
                for indicator in tone_indicators[key]:
                    if string.replace("/","") == indicator.replace("/",""):
                        results.append([indicator,key])
                        result = True
            if result:
                result_str += f"I found {len(results)} result{'s'*(len(results)!=1)}:\n"
            max_length = 0
            for x in results:
                if len(x[0]) > max_length:
                    max_length = len(x[0])
            for x in results:
                result_str += f"> '{x[0]}',{' '*(max_length-len(x[0]))} meaning {x[1]}\n"
        elif mode == 3:
            for key in tone_indicators: # "lyrics" : ["/l","/ly","/lyr"]
                for indicator in tone_indicators[key]: # ["/l","/ly","/lyr"]
                    if len(string.replace("/","")) > len(indicator.replace("/","")):
                        continue
                    last_index = 0
                    for str_index in range(len(string.replace("/",""))): # "/lr" -> "lr" -> "l" "r"
                        res = False
                        for indIndex in range(last_index,len(indicator)): # "/lyr", "/" "l" "y" "r"
                            if string.replace("/","")[str_index] == indicator[indIndex]:
                                res = True
                                last_index = indIndex
                                break
                        if not res:
                            break
                    else:
                        results.append([indicator,key])
                        result = True
            if result:
                result_str += f"I found {len(results)} result{'s'*(len(results)!=1)} for {string}:\n"
            max_length = 0
            for x in results:
                if len(x[0]) > max_length:
                    max_length = len(x[0])
            for x in results:
                result_str += f"> '{x[0]}',{' '*(max_length-len(x[0]))} meaning {x[1]}\n"
        if not result:
            result_str += f"No information found for '{string}'...\nIf you believe this to be a mistake or want to add a new tone indicator, message a staff member (ask for Mia)"

        if len(result_str.split("\n")) > 6 and public:
            public = False
            result_str += "\nDidn't send your message as public cause it would be spammy, having this many results."
        if len(result_str) > 1999    :
            result_str = "Your search returned too many results (discord has a 2000-character message length D:). Please search for something more specific."
        await itx.response.send_message(result_str,ephemeral=not public)

async def setup(client):
    # client.add_command("toneindicator")
    await client.add_cog(ToneIndicator(client))

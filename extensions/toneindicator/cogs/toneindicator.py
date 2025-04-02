import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands


tone_indicators = {
    "excited": ["/!", "/exc"],
    "alterous": ["/a", "/ars"],
    "affectionate": ["/a", "/aff"],
    "asking for a friend": ["/afaf"],
    "am i the a**hole?": ["/aita"],
    "an order": ["/ao"],
    "apathetic": ["/apa"],
    "alterous (not directly romantic (but can become so))": ["/ars"],
    "ask to tag": ["/att"],
    "a vent": ["/av"],
    "at you": ["/ay"],
    "bitter / bitterly": ["/b"],
    "bragging / flex": ["/br", "/fx"],
    "copypasta": ["/c", "/copy"],
    "calm / calmly": ["/calm"],
    "clickbait": ["/cb"],
    "celebratory": ["/cel"],
    "caring intent": ["ci"],
    "coping joke": ["/cj"],
    "comforting": ["/co", "/cf"],
    "concerned": ["/co"],
    "contradicting": ["/con"],
    "curious/curiously": ["/curi"],
    "content warning": ["/cw"],
    "direct": ["/dir"],
    "do not comment": ["/dnc"],
    "do not interract": ["/dni"],
    "do not interract unless close": ["/dniuc"],
    "embarrassed": ["/e"],
    "echolalia (unsolicited repitition/quote)": ["/echo"],
    "educational": ["/edu"],
    "empty threat": ["/eth"],
    "exageration": ["/ex", "/exag"],
    "fake": ["/f"],
    "false": ["/f"],
    "familial (affectionate?)": ["/fam"],
    "for example / example given": ["/fex", "/eg"],
    "fiction / fictional": ["/fic"],
    "flirting": ["/fl"],
    "for the attention": ["/fta"],
    "furious": ["/fu"],
    "gentle / gently": ["/gentle"],
    "genuine": ["/gen", "/genq", "/g", "/gq"],
    "genuine suggestion": ["/gs", "/gens"],
    "headmate (often referring to DID)": ["/hm"],
    "half-joking, This tag can be difficult to interpet, and is best thought of as 'not serious': the intent "
    "is serious, but the statement is not literally true. Examples: 'for legal reasons, this is a joke', "
    "'haha im kidding; unless.. :>'": ["/hj"],
    "half jokingly overreacting": ["/hjov"],
    "half jokingly prideful": ["/hjpr"],
    "headspace / inner world (often referring to DID)": ["/hsp", "/iw"],
    "half serious": ["/hsrs"],
    "half rhetorical": ["/hrh", "/hrt"],
    "hyperbole": ["/hyp", "/hyb", "/hy"],
    "hypothetical": ["/hyp"],
    "inside joke": ["/ij"],
    "information or informing": ["/in", "/info"],
    "in system. Like an inside joke, but usually for people with DID (with a system)": ["/insys"],
    "indirect": ["/ind"],
    "in real life / the outside world": ["/irl", "/ew", "/mp"],
    "irrelevant": ["/irre"],
    "interact with care": ["/iwc"],
    "joke / joking": ["/j"],
    "joking insult": ["/ji"],
    "just kidding": ["/jk"],
    "joking overreaction": ["/jov"],
    "jokingly prideful": ["/jpr"],
    "joke question": ["/jq"],
    "jokingly overreacting": ["/jov"],
    "just so you know": ["jsyk"],
    "just wondering": ["/jw"],
    "keysmash semhsakakeysmamshma": ["/key"],
    "lyrics": ["/l", "/ly", "/lyr", "/lyrics"],
    "lying / not (telling) the truth": ["/lying"],
    "literally": ["/li"],
    "light-hearted": ["/lh"],
    "light-hearted sarcasm": ["/lhs"],
    "a little upset": ["/lu"],
    "lovingly": ["/lv"],
    "metaphorically / metaphor": ["/m"],
    "mad": ["/m", "/mad"],
    "messing around": ["/ma"],
    "manifesting": ["/ma"],
    "melodramatic (drama with strong emotional appeal)": ["/md"],
    "major joke": ["/mj"],
    "not a brag / flex": ["/nabr", "/nafx"],
    "not an order": ["/nao"],
    "not a question / statement": ["/naq", "/st", "/state"],
    "not a vent": ["/nav"],
    "not at you (also see /nmay)": ["/nay"],
    "for when you're vagueposting or venting, but it's directed at nobody here (none of your followers)": [
        "/nbh"],
    "not being rude": ["/nbr"],
    "nobody specific": ["/nbs"],
    "nobody you know": ["/nbyk"],
    "not comparing": ["/ncm"],
    "negative connotation": ["/neg", "/nc"],
    "neutral connotation": ["/neu"],
    "not fake": ["/nf"],
    "not flirting": ["/nfl"],
    "not forced to answer": ["/nfta", "/nf"],
    "not for the attention": ["/nfta"],
    "not mad / not upset": ["/nm"],
    "not mad at you, to specify that someone isnt mad at someone else (also see /nay)": ["/nmay"],
    "no pressure": ["/np"],
    "no problem": ["/np"],
    "not passive aggressive": ["/npa"],
    "not prideful": ["/npr"],
    "not subtweeting": ["/nsb", "/nst"],
    "non-sexual intent": ["/nsx", "/nx", "/nsxs"],
    "non-serious / not serious": ["/nsrs"],
    "not a serious question": ["/nsrsq"],
    "not threatening": ["/nth"],
    "not trying to be rude": ["/nttbr"],
    "not yelling": ["/ny"],
    "observation": ["/ob"],
    "optional": ["/op", "/opt"],
    "oversimplification": ["/osi"],
    "off topic": ["/ot"],
    "it's okay to interract": ["/oti"],
    "it's okay to laugh": ["/otl"],
    "it's okay to ask for reassurance": ["/otr"],
    "outraged": ["/outr"],
    "platonic": ["/p"],
    "passive aggressive": ["/pa"],
    "playful": ["/pf"],
    "playfully mad": ["/pm"],
    "prideful": ["/pr"],
    "half prideful": ["/hpr"],
    "please interract": ["/pi"],
    "please laugh": ["/pl"],
    "paraphrase": ["/para"],
    "positive connotation (eg. \"I don't mean this in a bad way\")": ["/pos", "/pc"],
    "quote": ["/q"],
    "queerplatonic": ["/qp"],
    "romantic": ["/r"],
    "random": ["/ra"],
    "reference": ["/ref"],
    "rhetorical question": ["/rh", "/rt", "/rtq"],
    "sarcastic / sarcasm / sarcastically": ["/s", "/sarc"],
    "safe": ["/safe"],
    "for when you're vagueposting or venting, but it's directed at somebody here (x of your followers)": [
        "/sbh"],
    "subtweeting": ["/sbtw"],
    "source joke (\"a /ref from a headmate's source\") (often related to DID)": ["/sj"],
    "serious": ["/srs"],
    "stimming (an action to stay calm when surrounded by other stimuli)": ["/stim"],
    "sympathetic": ["/sym"],
    "system (often referring to DID) r": ["/sys"],
    "super violent": ["/sv"],
    "sexual intent": ["/sx", "/x", "/xxx"],
    "teasing": ["/t"],
    "tangent": ["/tan"],
    "threat": ["/th"],
    "tic, for when something typed out was unintentional due to being a tic": ["/t", "/ti", "/tic"],
    "today I F'ed up": ["/tifu"],
    "to self": ["/ts"],
    "trigger warning": ["/tw"],
    "upset": ["/u"],
    "unintentional": ["/unin"],
    "unrelated": ["/unre"],
    "vague": ["/v", "/vague"],
    "violent": ["/v", "/vi"],
    "very upset": ["/vu"],
    "warm / warmth": ["/w"],
    "with consent": ["/wc"],
    "wrong proxy": ["/wp"],
}


class ToneIndicator(commands.Cog):
    @app_commands.command(name="toneindicator", description="Look for the definition of a tone indicator")
    @app_commands.describe(mode="Choose a search method, eg. /p -> platonic; or vice versa",
                           string="This is your search query. What do you want to look for?",
                           public="Do you want to share the search results with the rest of the channel? (True=yes)")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='definition', value=1),
        discord.app_commands.Choice(name='exact acronym', value=2),
        discord.app_commands.Choice(name='rough acronym', value=3),
    ])
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, private_channels=True, dms=True)
    async def toneindicator(self, itx: discord.Interaction, mode: int, string: str, public: bool = False):
        # todo: clarify error messages when stuff is not found, typically because people search for the
        #  definition for "p", when they should be looking for "exact acronym" or "rough acronym" instead.
        result = False
        results = []
        result_str = ""
        if mode == 1:
            for key in tone_indicators:
                if string.replace("-", " ") in key.replace("-", " ") or string.replace("-", "") in key.replace("-", ""):
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
                    results.append([key, tone_indicators[key], overlapper, overlaps])
                    result = True
            if result:
                result_str += f"I found {len(results)} result{'s' * (len(results) != 1)} with '{string}' in:\n"
            for x in results:
                y = ""
                if len(x[3]) > 0:
                    y = f"\n   + {len(x[3])} overlapper{'s' * (len(x[3]) != 1)}:\n    [ {x[2]}: {', '.join(x[3])} ]"
                result_str += f"> \"{x[0]}\": {', '.join(x[1])}" + y + "\n"
        elif mode == 2:
            for key in tone_indicators:
                for indicator in tone_indicators[key]:
                    if string.replace("/", "") == indicator.replace("/", ""):
                        results.append([indicator, key])
                        result = True
            if result:
                result_str += f"I found {len(results)} result{'s' * (len(results) != 1)}:\n"
            max_length = 0
            for x in results:
                if len(x[0]) > max_length:
                    max_length = len(x[0])
            for x in results:
                result_str += f"> '{x[0]}',{' ' * (max_length - len(x[0]))} meaning {x[1]}\n"
        elif mode == 3:
            for key in tone_indicators:  # "lyrics" : ["/l","/ly","/lyr"]
                for indicator in tone_indicators[key]:  # ["/l","/ly","/lyr"]
                    if len(string.replace("/", "")) > len(indicator.replace("/", "")):
                        continue
                    last_index = 0
                    for str_index in range(len(string.replace("/", ""))):  # "/lr" -> "lr" -> "l" "r"
                        res = False
                        for indIndex in range(last_index, len(indicator)):  # "/lyr", "/" "l" "y" "r"
                            if string.replace("/", "")[str_index] == indicator[indIndex]:
                                res = True
                                last_index = indIndex
                                break
                        if not res:
                            break
                    else:
                        results.append([indicator, key])
                        result = True
            if result:
                result_str += f"I found {len(results)} result{'s' * (len(results) != 1)} for {string}:\n"
            max_length = 0
            for x in results:
                if len(x[0]) > max_length:
                    max_length = len(x[0])
            for x in results:
                result_str += f"> '{x[0]}',{' ' * (max_length - len(x[0]))} meaning {x[1]}\n"
        if not result:
            result_str += (f"No information found for '{string}'...\n"
                           f"If you believe this to be a mistake or want to add a new tone indicator, message a "
                           f"staff member (ask for Mia)")

        if len(result_str.split("\n")) > 6 and public:
            public = False
            result_str += "\nDidn't send your message as public cause it would be spammy, having this many results."
        if len(result_str) > 1999:
            result_str = ("Your search returned too many results (discord has a 2000-character message length D:). "
                          "Please search for something more specific.")
        await itx.response.send_message(result_str, ephemeral=not public)

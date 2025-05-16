import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.toneindicator.searchmode import SearchMode
from resources.customs import Bot


tone_indicators: dict[str, list[str]] = {
    "excited": ["/!", "/exc"],
    "alterous": ["/a", "/ars"],
    "affectionate": ["/a", "/aff"],
    "asking for a friend": ["/afaf"],
    "am i the a\\*\\*hole?": ["/aita"],
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
    ("half-joking, This tag can be difficult to interpet, and is best "
     "thought of as 'not serious': the intent is serious, but the statement "
     "is not literally true. Examples: 'for legal reasons, this is a joke', "
     "'haha im kidding; unless.. :>'"): ["/hj"],
    "half jokingly overreacting": ["/hjov"],
    "half jokingly prideful": ["/hjpr"],
    "headspace / inner world (often referring to DID)": ["/hsp", "/iw"],
    "half serious": ["/hsrs"],
    "half rhetorical": ["/hrh", "/hrt"],
    "hyperbole": ["/hyp", "/hyb", "/hy"],
    "hypothetical": ["/hyp"],
    "inside joke": ["/ij"],
    "information or informing": ["/in", "/info"],
    ("in system. Like an inside joke, but usually for people with "
     "DID (with a system)"): ["/insys"],
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
    ("for when you're vagueposting or venting, but it's directed at nobody "
     "here (none of your followers)"): ["/nbh"],
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
    ("not mad at you, to specify that someone isnt mad at someone "
     "else (also see /nay)"): ["/nmay"],
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
    ("positive connotation (eg. \"I don't mean this "
     "in a bad way\")"): ["/pos", "/pc"],
    "quote": ["/q"],
    "queerplatonic": ["/qp"],
    "romantic": ["/r"],
    "random": ["/ra"],
    "reference": ["/ref"],
    "rhetorical question": ["/rh", "/rt", "/rtq"],
    "sarcastic / sarcasm / sarcastically": ["/s", "/sarc"],
    "safe": ["/safe"],
    ("for when you're vagueposting or venting, but it's directed at "
     "somebody here (x of your followers)"): ["/sbh"],
    "subtweeting": ["/sbtw"],
    ("source joke (\"a /ref from a headmate's source\") "
     "(often related to DID)"): ["/sj"],
    "serious": ["/srs"],
    ("stimming (an action to stay calm when surrounded "
     "by other stimuli)"): ["/stim"],
    "sympathetic": ["/sym"],
    "system (often referring to DID) r": ["/sys"],
    "super violent": ["/sv"],
    "sexual intent": ["/sx", "/x", "/xxx"],
    "teasing": ["/t"],
    "tangent": ["/tan"],
    "threat": ["/th"],
    ("tic, for when something typed out was unintentional due "
     "to being a tic"): ["/t", "/ti", "/tic"],
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


def _invert_tone_indicator_list() -> dict[str, list[str]]:
    """
    Reverse the tone_indicator list.

    .. code-block:: python

        {
            "/a": ["alterous", "affectionate"],
            "/aff": ["affectionate"],
            "/ars": ["alterous"]
        }

    :return: A dictionary where the keys and values (list) have been reversed.
    """
    # Reverse tone_indicator list:
    inverted_indicators: dict[str, list[str]] = {}
    for definition, acronyms in tone_indicators.items():
        for acronym in acronyms:
            if acronym not in inverted_indicators:
                inverted_indicators[acronym] = []
            inverted_indicators[acronym].append(definition)
    return inverted_indicators


indicator_definitions: dict[str, list[str]] = _invert_tone_indicator_list()


def _get_overlaps_from_acronyms(
        acronyms: list[str]
) -> set[str]:
    """
    Retrieve all acronyms with more than 1 definition.

    :param acronyms: A list of acronyms to check for multiple definitions.
    :return: A set of acronyms with more than 1 definition.
    """
    overlaps = set()
    for acronym in acronyms:
        definitions = indicator_definitions[acronym]
        if len(definitions) > 1:
            overlaps.add(acronym)
    return overlaps


def _handle_tag_definition(
        itx: discord.Interaction[Bot], string: str
) -> tuple[str, bool]:
    """
    A helper function to handle finding acronyms with definitions
    containing the given string.

    :param itx: The interaction with the client, to retrieve a command mention
     to explain searching for tone indicators with multiple definitions.
    :param string: The definition (or section of a definition) to search for.
    :return: A tuple of the formatted return string, and whether any results
     were found for the given string.
    """
    results = []
    any_overlaps = False
    shortened_string = string.replace("-", "")
    for definition, acronyms in tone_indicators.items():
        if shortened_string in definition.replace("-", ""):
            overlaps = _get_overlaps_from_acronyms(acronyms)
            acronyms_or_overlap = set()
            for tag in tone_indicators[definition]:
                if tag in overlaps:
                    tag += " `[!]`"
                acronyms_or_overlap.add(tag)
            if not any_overlaps:
                any_overlaps = bool(overlaps)
            results.append(
                (definition, acronyms_or_overlap))

    result_str = ""
    if results:
        result_str = (f"I found {len(results)} "
                      f"result{'s' * (len(results) != 1)} "
                      f"with '{string}' in:\n")
    for definition, acronyms in results:
        # > definition: /tag1 [!], /tag2, /tag3
        result_str += f"- \"{definition}\": {', '.join(acronyms)}\n"
    if any_overlaps:
        cmd_mention = itx.client.get_command_mention("toneindicator")
        result_str += (
            f"Some acronyms have multiple definitions, marked with "
            f"`[!]`. Use {cmd_mention} `mode:Exact acronym` `tag: `"
            f"to find the other possible definitions for these tags."
        )
    return result_str, bool(results)


def _handle_acronym(string, exact) -> tuple[str, bool]:
    """
    Helper function to retrieve all definitions matching a tone indnicator.

    :param string: The acronym of the tone indicator to find definitions for.
    :param exact: Whether the acronyms must match exactly, or only have to
     contain the given string.
    :return: A tuple of the formatted return string, and whether any results
     were found for the given string.
    """
    found_tags: set[str] = set()
    results: set[str] = set()
    shortened_string = string.replace("/", "")
    for indicator, definitions in indicator_definitions.items():
        if exact:
            if shortened_string == indicator.replace("/", ""):
                found_tags.add(indicator)
                results |= set(definitions)
        else:
            if shortened_string in indicator.replace("/", ""):
                found_tags.add(indicator)
                results |= set(definitions)

    result_str = ""
    if results:
        result_str = (f"I found {len(results)} "
                      f"result{'s' * (len(results) != 1)} "
                      f"for '{string}':\n")
    for definition in results:
        acronyms = tone_indicators[definition]
        # make tag bold if it was the tag that matched the search result.
        tags = [f"**{a}**" if a in found_tags else a for a in acronyms]
        result_str += f"- {definition}: {', '.join(tags)}\n"
    return result_str, bool(results)


class ToneIndicator(commands.Cog):
    @app_commands.command(name="toneindicator", description="Look for the definition of a tone indicator")
    @app_commands.describe(mode="Choose a search method, eg. /p -> platonic; or vice versa",
                           string="This is your search query. What do you want to look for?",
                           public="Do you want to share the search results with the rest of the channel? (True=yes)")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Definition', value=SearchMode.definition.value),
        discord.app_commands.Choice(name='Exact acronym', value=SearchMode.exact_acronym.value),
        discord.app_commands.Choice(name='Rough acronym', value=SearchMode.rough_acronym.value),
    ])
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, private_channels=True, dms=True)
    async def toneindicator(
            self,
            itx: discord.Interaction[Bot],
            mode: int,
            string: str,
            public: bool = False
    ):
        result_str = ""
        has_results = False
        if mode == SearchMode.definition.value:
            result_str, has_results = _handle_tag_definition(itx, string)
        elif mode == SearchMode.exact_acronym.value:
            result_str, has_results = _handle_acronym(string, exact=True)
        elif mode == SearchMode.rough_acronym.value:
            result_str, has_results = _handle_acronym(string, exact=False)

        if not has_results:
            result_str += (
                f"No information found for '{string}'...\n"
                f"Make sure you're looking for the right thing. If you are "
                f"looking for the acronym for \"platonic\", you should set "
                f"`mode: ` to \"definition\". If you are looking for the "
                f"definition of a \"/j\", you should set `mode: ` to"
                f"\"exact acronym\" or \"rough acronym\".\n"
                f"If you believe this tone tag should be added to the "
                f"dictionary, message @mysticmia on discord (bot developer)")

        elif len(result_str.split("\n")) > 6 and public:
            public = False
            result_str += ("\n"
                           "Didn't send your message as public cause it "
                           "would be spammy, having this many results.")
        if len(result_str) > 2000:
            result_str = ("Your search returned too many results (discord "
                          "has a 2000-character message length limit D: ). "
                          "Please search for something more specific.")
        await itx.response.send_message(result_str, ephemeral=not public)

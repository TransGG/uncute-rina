import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *

class TermDictionary(commands.Cog):
    def __init__(self, client):
        self.client = client

    @app_commands.command(name="dictionary",description="Look for the definition of a trans-related term!")
    @app_commands.describe(string="This is your search query. What do you want to look for?",
                           public="Do you want to share the search results with the rest of the channel? (True=yes)")
    # @app_commands.choices(mode=[
    #         discord.app_commands.Choice(name='normal: search by term', value=1),
    #         discord.app_commands.Choice(name='Get a list of terms', value=2),
    #     ])
    async def dictionary(self, itx: discord.Interaction, string: str, public: bool = False):
        termDictionary = {
            "An egg often stands for someone who hasn't realised they're trans yet, or is in denial. \
For example, they 'ironically' crossdress, play game characters of the opposite gender, or writes stories about trans characters. \
Then when they realise, it's referred to the egg \"cracking.\"":["Egg","cracking","crack"],
            "People who are assigned male at birth, but who identify more with femininity than with masculinity. \
The term can among others include trans women, non-binary people and genderfluid people.":["Transfeminine","transfem","transfemme"],
            "People who are assigned female at birth, but who identify more with masculinity than with femininity. \
The term can among others include trans men, non-binary people and genderfluid people.":["Transmasculine","transmasc"],
            "Awesome valid lady who was assigned male at birth. Trans women usually take steps to transition, such as hormones or surgery, \
but you can transition without those things as well. You don’t even have to transition at all if you don’t want!":["Trans woman","trans girl", "trans gal"],
            "Awesome valid guy who was assigned female at birth. Trans men usually take steps to transition, such as hormones or surgery, \
but you can transition without those things as well. You don’t even have to transition at all if you don’t want!":["Trans man","trans guy","trans boy", "trans dude"],
            "There are multiple ways to transition: social transition, medical transition, legal changes. Social transition means telling those around you that you're transgender (and have a new name or pronouns).\
Medical transition often includes HRT and can include surgery. Legal changes refer to changing your passport to have your new name or gender.":["Transitioning","transition"],
            "The gender the doctor wrote on your birth certificate.":["Assigned gender at birth", "agab","afab","amab","assigned male at birth","assigned female at birth"],
            "Psychotherapy, also called talk therapy or usually just \"therapy,\" is a form of treatment aimed at relieving emotional distress and mental health problems. (from psychologytoday.com)":["Therapy"],
            "Conversion therapy is the pseudoscientific practice of trying to change an individual's sexual orientation from homosexual or bisexual to heterosexual \
or an individual's gender from trans to cis using psychological or spiritual interventions. It's seen as brainwashing. (from Wikipedia)":["Conversion therapy"],
            "Intersex people are individuals born with any of several sex characteristics including chromosome patterns, gonads, or genitals that, according to the Office of the United Nations High Commissioner for Human Rights, \"do not fit typical binary notions of male or female bodies\" (from Wikipedia).\
What makes intersex people similar is their experiences of medicalization, not biology. Intersex is not an identity. Most intersex people identify as men or women, just like everybody else.":["Intersex"],
            "HRT in transgender folk is a form of hormone therapy in which sex hormones (androgens or estrogens, and blockers) and other hormonal medications (such as pills or injections) \
are given to replace or boost the body's natural hormones in order to more closely align their secondary sexual characteristics with their gender identity. (from Wikipedia and Urban Dictionary)":["Hormone Replacement Therapy (HRT)", "hormone replacement therapy","hormones","hormone","HRT", "gender-affirming hormone therapy", "GAHT"],
            "An androgen is a male sex hormone naturally made by the testes. Androgens control and stimulate development of male characteristics. The main hormone is testosterone. (from Wikipedia)":["Androgens","androgen","testosteron","testosterone"],
            "Oestrogen (or estrogen) is a group of female hormones. Oestradiol is the most important oestrogen. Oestrogen is mainly made by the ovary, a small amount by the liver, adrenal cortex, and breast. Oestrogen helps women grow during puberty and is part of the menstrual cycle. (from Wikipedia)":["Estrogens","estrogen", "oestrogen", ],
            "SRS is one or more surgeries that are done to change the body's genitals or other sexual characteristrics. Transgender people may get SRS to make their body match their gender identity (Wikipedia). \
There are many different types of surgeries, and aren't limited to a gender. For females (or feminine people): [Phallectomy (removing the penis), Orchiectomy (removing the testicles), Vaginoplasty (where a surgeon creates a vagina), Breast implants, Voice therapy]. \
For males (or masculine people): [Mastectomy (removing the breasts), Hysterectomy (removing the uterus), Phalloplasty (where a surgeon creates a penis).":["Sex Reassignment Surgery (SRS)", "Sex reassignment surgery", "gender reassignment surgery", "surgery", "sex change"],
            "When someone takes it upon themselves to decide who does or does not have access or rights to a community or identity.":["Gatekeeping"],
            "In reproductive biology, a hermaphrodite is an organism that has both kinds of reproductive organs and can produce both gametes associated with male and female sexes. (from Wikipedia)":["Hermaphrodite"]
        }

        result = False
        results = []
        resultStr = ""
        mode = 1
        if mode == 1:
            for term in termDictionary:
                if string.lower().replace(" ","") == term.lower().replace(" ",""):
                    overlaps = []
                    overlapper = ""
                    # for term1 in toneIndicators:
                    #     if term == term1:
                    #         continue
                    #     for def in toneIndicators[term1]:
                    #         if def in toneIndicators[term]:
                    #             overlapper = def
                    #             overlaps.append(term1)
                    #             break
                    results.append([term,termDictionary[term],overlapper,overlaps])
                    result = True
            if result == True:
                resultStr += f"I found {len(results)} result{'s'*(len(results)>1)} with '{string}' in:   (thanks UrbanDictionary)\n"
                for x in results:
                    # y=""
                    # if len(x[3]) > 0:
                    #     y = f"\n   + {len(x[3])} overlapper{'s'*(len(x[3])>1)}:\n    [ {x[2]}: {', '.join(x[3])} ]"
                    resultStr += f"> {x[1][0]}: {x[0]}\n"
            else:
                #public = False
                resultStr += f"No information found for '{string}'...\nIf you would like to add a term, message a staff member (ask for Mia)"
                debug(f"{itx.user.name} ({itx.user.id}) searched for '{string}' in the terminology dictionary, but it yielded no results. Maybe we should add this term to the /dictionary command",color='light red')
        if mode == 2:
            for term in termDictionary:
                results.append(termDictionary[term][0])
                resultStr = "> "+', '.join(results)
        if len(resultStr.split("\n")) > 6 and public:
            public = False
            resultStr += "\nDidn't send your message as public cause it would be spammy, having this many results."
        if len(resultStr) > 1999    :
            resultStr = "Your search returned too many results (discord has a 2000-character message length D:). (Please search for something more specific.)"
        await itx.response.send_message(resultStr,ephemeral=(public==False))

async def setup(client):
    # client.add_command("toneindicator")
    await client.add_cog(TermDictionary(client))

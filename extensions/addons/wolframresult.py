from typing import TypedDict, Required, NotRequired, Literal, Any

# Some values are typically identical, denoted with "var1" etc.


# region Literals
class WolframUserInfoUsed(TypedDict):
    name: Literal[
        "Country",
        "TimeZone"
    ]


class WolframExpressionType(TypedDict):
    name: Literal[
        "Default",
        "Grid"
    ]


type WolframAssumptionType = Literal[
    "Clash",
    "MultiClash",
    "SubCategory",
    "Attribute",
    "Unit",
    "AngleUnit",
    "Function",
    "ListOrTimes",
    "ListOrNumber",
    "CoordinateSystem",
    "I",
    "NumberBase",
    "MixedFraction",
    "TimeAMOrPM",
    "DateOrder",
    "MortalityYearDOB",
    "TideStation",
    "FormulaSelect",
    "FormulaSolve",
    "FormulaVariable",
    "FormulaVariableOption",
    "FormulaVariableInclude",
]


type WolframScannerName = Literal[
    "Identity",
    "Simplification",
    "NumberLine"
]

type WolframTitleName = Literal[
    "Input",
    "Result",
    "Number Line",
    "Number Name",
]

type WolframIdName = Literal[
    "Input",
    "Result",
    "NumberLine",
    "NumberName",
]


type WolframDidyoumeansLevel = Literal[
    "low",
    "medium",
    "high",
]

# endregion Literals


class WolframErrorInfo(TypedDict):
    code: int
    msg: str


class WolframImage(TypedDict, total=False):
    src: str  # url with https:// .gif
    alt: str  # var1
    title: str  # var1
    width: int
    height: int
    type: str  # "Default", "Histogram", "2DMathPlot_1", "2DMathPlot_2",
    themes: str  # "1,2,3,4,5,6,...,11,12"
    colorinvertible: bool
    contenttype: str  # "image/gif"


class WolframPodStateDict(TypedDict):
    name: str
    input: str


class WolframPodState(TypedDict, total=False):
    count: int  # len(states)
    value: str  # "Current week"
    delimiters: str  # ""
    states: list[WolframPodStateDict]


class WolframSubpod(TypedDict, total=False):
    title: str  # ""
    # ^ "usually an empty string because most subpods have no title."
    img: WolframImage
    imagemap: Any  # not encountered yet, typically some clickable image HTML
    plaintext: str  # var1
    mathml: Any
    sound: Any  # A type attribute and a file pointer (link?). Only on request
    minput: Any
    moutput: Any
    cell: Any
    states: list[WolframPodState | WolframPodStateDict]


class WolframPodInfo(TypedDict):
    ...


class WolframPod(TypedDict, total=False):
    title: Required[WolframTitleName]  # "Input", "Result", "Number Line", "Number Name"
    scanner: Required[WolframScannerName]  # "Identity", "Simplification", "NumberLine"
    id: Required[WolframIdName]  # "Input", "Result", "NumberLine", "NumberName"
    position: Required[int]  # 1 or 11, "typically multiples of 100" (that's a lie)
    error: Required[bool | WolframErrorInfo]
    primary: bool
    numsubpods: Required[int]  # len(subpods) presumably.
    subpods: list[WolframSubpod]
    expressiontypes: WolframExpressionType | list[WolframExpressionType]
    states: list[WolframPodState | WolframPodStateDict]
    infos: list[WolframPodInfo]


class WolframRelatedQueries(TypedDict, total=False):
    count: int
    timing: float
    relatedquery: list[str]


class WolframAssumptionValue(TypedDict):
    name: str
    desc: str
    input: str


class WolframAssumption(TypedDict, total=False):
    type: Required[WolframAssumptionType]  # "SubCategory"
    word: Required[str]
    template: str  # "Assuming ${desc1}. Use ${desc2} instead"
    count: int  # len(values)
    values: list[WolframAssumptionValue] | WolframAssumptionValue
    # ^ because of course it can't just be a list of 1 element.


class WolframSource(TypedDict):
    url: str
    text: str


class WolframTip(TypedDict):
    text: str


class WolframDidyoumean(TypedDict):
    score: float
    level: WolframDidyoumeansLevel  # probably dependent of `score`
    val: str


class WolframSpellcheckWarning(TypedDict):
    word: str
    suggestion: str
    text: str


class WolframDelimiterWarning(TypedDict):
    text: Literal[
        "An attempt was made to fix mismatched parentheses, brackets or braces"
    ]


class WolframTranslationWarning(TypedDict):
    phrase: str
    trans: str  # suggested translation
    lang: str  # The assumed original language of `phrase`
    text: str  # "Translating from {lang} to {trans}"


class WolframReinterpretWarning(TypedDict):
    text: Literal["Using closest Wolfram|Alpha interpretation:"]
    alternatives: list[str]


type WolframWarning = (
        WolframSpellcheckWarning
        | WolframDelimiterWarning
        | WolframTranslationWarning
        | WolframReinterpretWarning
)


class WolframLanguageMessage(TypedDict):
    english: str
    other: str


class WolframFutureTopic(TypedDict):
    topic: str
    msg: Literal["Development of this topic is under investigation..."]


class WolframExamplePage(TypedDict):
    category: str
    url: str


class WolframGeneralization(TypedDict):
    topic: str
    desc: Literal["General results for:"]
    idf: str  # randomized string?


class WolframQueryResult(TypedDict, total=False):
    success: bool  # False => no elements in `pods` and numpods == 0
    error: bool | WolframErrorInfo
    numpods: Required[int]  # len(pods)
    datatypes: str  # "Math"
    parsetiming: float
    parsetimedout: bool
    id: str
    kernelId: str  # "213", "79", "115" integer?
    processId: int
    version: str  # "2.6"
    inputstring: str  # the original input
    sbsallowed: bool
    userinfoused: WolframUserInfoUsed
    parentId: str  # can be identical to "requestId"
    requestId: str  # can be identical to "parentId"
    pods: list[WolframPod]
    assumptions: list[WolframAssumption]
    # ^ When given 1 value, it's still in a list: with 1 element.
    examplepage: WolframExamplePage
    relatedqueries: WolframRelatedQueries
    timing: Required[float]  # typically up to 20.001
    timedout: Required[str]  # list of strings separated by comma, or ""
    # ^ think "Data,Percent,Unity,AtmosphericProperties,UnitInformation,Music,Geometry"  # noqa
    timedoutpods: Required[str]  # list of pods that timed out during format
    # ^ think "Weather history & forecast,Weather station information"
    sources: list[WolframSource]
    recalculate: str  # url
    warnings: list[WolframWarning] | WolframWarning
    generalization: Any
    futuretopic: WolframFutureTopic

    tips: WolframTip  # | list[WolframTip]
    didyoumeans: list[WolframDidyoumean] | WolframDidyoumean
    languagemsg: WolframLanguageMessage


class WolframResult(TypedDict):
    queryresult: WolframQueryResult

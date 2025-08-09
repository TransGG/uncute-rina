import logging
from datetime import datetime, timezone
from enum import Enum


class DebugColor(Enum):
    default = "\033[0m"
    black = "\033[30m"
    red = "\033[31m"
    lime = "\033[32m"
    green = "\033[32m"
    yellow = "\033[33m"
    # orange = "\033[33m"  # kinda orange i guess?
    blue = "\033[34m"
    magenta = "\033[35m"
    purple = "\033[35m"
    cyan = "\033[36m"
    gray = "\033[37m"
    lightblack = "\033[90m"
    darkgray = "\033[90m"
    lightred = "\033[91m"
    lightlime = "\033[92m"
    lightgreen = "\033[92m"
    lightyellow = "\033[93m"
    lightblue = "\033[94m"
    lightmagenta = "\033[95m"
    lightpurple = "\033[95m"
    lightcyan = "\033[96m"
    aqua = "\033[96m"
    lightgray = "\033[97m"
    white = "\033[97m"


def debug(
        text: str = "",
        color: DebugColor = DebugColor.default,
        add_time: bool = True,
        end="\n",
        advanced=False
) -> None:
    """
    Log a message to the console.

    :param text: The message you want to send to the console.
    :param color: The color you want to give your message
     ('red' for example).
    :param add_time: If you want to start the message with a
     '[2025-03-31T23:59:59.000001Z] [INFO]:'.
    :param end: What to end the end of the message with (similar
     to print(end='')).
    :param advanced: Whether to interpret `text` as advanced text
     (like minecraft in-chat colors). Replaces "&4" to red, "&l" to
     bold, etc. and "&&4" to a red background.
    """
    if type(text) is not str:
        text = repr(text)

    detail_color = {
        "&0": "40",
        "&8": "40",
        "&1": "44",
        "&b": "46",
        "&2": "42",
        "&a": "42",
        "&4": "41",
        "&c": "41",
        "&5": "45",
        "&d": "45",
        "&6": "43",
        "&e": "43",
        "&f": "47",
        "9": "34",
        "6": "33",
        "5": "35",
        "4": "31",
        "3": "36",
        "2": "32",
        "1": "34",
        "0": "30",
        "f": "37",
        "e": "33",
        "d": "35",
        "c": "31",
        "b": "34",
        "a": "32",
        "l": "1",
        "o": "3",
        "n": "4",
        "u": "4",
        "r": "0",
    }
    if advanced:
        for _detColor in detail_color:
            while "&" + _detColor in text:
                _text = text
                text = text.replace(
                    "m&" + _detColor,
                    ";" + detail_color[_detColor] + "m",
                    1
                )
                if _text == text:
                    # No previous coloring found to replace, so add a
                    #  new one instead. (no m&)
                    text = text.replace(
                        "&" + _detColor,
                        "\033[" + detail_color[_detColor] + "m",
                        1
                    )
        color = DebugColor.default

    if add_time:
        formatted_time_string = (datetime
                                 .now(timezone.utc)
                                 .strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
        time = f"{color.value}[{formatted_time_string}] [INFO]: "
    else:
        time = color.value
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger()
    # print = logger.info
    if end.endswith("\n"):
        end = end[:-2]
    logger.info(f"{time}{text}{DebugColor.default.value}"
                + end.replace('\r', '\033[F'))

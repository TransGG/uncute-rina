from __future__ import annotations

from enum import Enum


class DebugColor(Enum):
    # todo: move to own file
    default = "\033[0m"
    black = "\033[30m"
    red = "\033[31m"
    lime = "\033[32m"
    green = "\033[32m"
    yellow = "\033[33m"
    orange = "\033[33m"  # kinda orange i guess?
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

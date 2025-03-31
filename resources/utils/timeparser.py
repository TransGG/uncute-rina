from datetime import datetime, timedelta
import re
from typing import TypeAlias


DistanceComponents = list[tuple[float, str]]


class MissingUnitException(ValueError):
    pass


class MissingQuantityException(ValueError):
    pass


TIMETERMS = {
    "y": ["y", "year", "years"],
    "M": ["mo", "month", "months"],
    "w": ["w", "week", "weeks"],
    "d": ["d", "day", "days"],
    "h": ["h", "hour", "hours"],
    "m": ["m", "min", "mins", "minute", "minutes"],
    "s": ["s", "sec", "secs", "second", "seconds"]
}


class TimeParser:
    @staticmethod
    def parse_time_string(input_string: str) -> DistanceComponents:
        """
        A helper function to turn a string of 2d4h to a list of tuples:

        :param input_string: The string to split. Example: "4days6seconds"

        :return: A list of easily-comprehensible time components: [(4, "days"), (6, "seconds")].

        :raise ValueError: If the user fills in an invalid digit ("0..3" or "0.30.4" for example)
        :raise MissingQuantityException: If the user starts their input with a non-numeric character (should
         always start with a number :P)
        :raise MissingUnitException: If the user doesn't have a complete parse (typically because it ends with
         a numeric character).
        """
        # This function was partially written by AI, to convert "2d4sec" to [(2, "d"), (4,"sec")]

        if input_string[0] not in "0123456789.":
            raise MissingQuantityException("Time strings should begin with a number: \"10min\"")
        # This regex captures one or more digits followed by one or more alphabetic characters.
        pattern = r"([.\d]+)([a-zA-Z]+)"  # :o i see two capture groups

        # Find all matches in the input string
        matches = re.findall(pattern, input_string)

        # Convert the matches to the desired format: (number, string)
        result = []
        # Not using list comprehension, to send more-detailed error message.
        # result = [(int(num), unit) for num, unit in matches] # :o you can split the capture groups
        output = ""

        for (num, unit) in matches:
            output += num + unit
            try:
                result.append((float(num), unit))
            except ValueError:  # re-raise
                raise ValueError(
                    f"Invalid number '{num}' in '{input_string}'! You can use decimals, but "
                    f"the number should be valid."
                )

        if input_string != output:
            # incomplete parse
            raise MissingUnitException(
                f"Incomplete parse. The input string did not have the correct parsing format:\n"
                f"- Input:  `{input_string}`\n"
                f"- Parsed: `{output}`" if output else "- Parsed: _(Empty)_"
            )

        return result

    @staticmethod
    def shrink_time_terms(time_units: DistanceComponents) -> DistanceComponents:
        """
        Helper function to convert time strings from "year" to "y", etc.

        :param time_units: An output from parse_time_string() containing a list of (4, "days") tuples.

        :returns: A list of tuples with shrunk time strings: (4, "d").

        :raise ValueError: Input contains unrecognised datetime unit(s).
        """
        for unit_index in range(len(time_units)):
            # use index instead of iterating tuples in list because of the tuple component reassignment 3 lines down.
            for timeterm in TIMETERMS:
                if time_units[unit_index][1] in TIMETERMS[timeterm]:
                    time_units[unit_index] = (time_units[unit_index][0], timeterm)
                    # tuple does not support item assignment like (1,2)[0]=2
                    # Also assigning to tuples doesn't save in list, so need list ref too.
                    break
            else:
                raise ValueError(f"Datetime unit '{time_units[unit_index]}' not recognised!")
        return time_units

    @staticmethod
    def parse_date(time_string: str, start_date: datetime = datetime.now().astimezone()) -> datetime:
        """
        Helper function to turn strings like "3d5h10min4seconds" to a datetime in the future.


        :param time_string: A string of a date format like "3d10min". Should not contain spaces (but it
         probably doesn't matter).
        :param start_date: The date to offset from.

        :returns: A datetime with an offset in the future (relative to the given datetime input) matching the
         input string.

        :raise ValueError: If the input is invalid; if the input contains unrecognised datetime units; or
         if the "year" unit exceeds 3999 or if the "day" offset exceeds 1500000.
        """
        # - "next thursday at 3pm"
        # - "tomorrow"
        # + "in 3 days"
        # + "2d"
        # - "2022-07-03"
        # + "2022y4mo3days"
        # - "<t:293847839273>"
        if "-" in time_string:
            raise ValueError("Tried parsing input as timestring when it should be parsed as ISO8601 or Unix instead.")

        time_units = TimeParser.shrink_time_terms(TimeParser.parse_time_string(time_string))  # can raise ValueError
        # raises ValueError if invalid input
        timedict = {
            "y": start_date.year,
            "M": start_date.month,
            "d": start_date.day,
            "h": start_date.hour,
            "m": start_date.minute,
            "s": start_date.second,
            "f": start_date.microsecond,
            # microseconds can only be set with "0.04s", but since start_date will typically be from discord snowflakes,
            #  the microseconds will be 0 by default.
        }

        # add values to each timedict key
        for unit in time_units:
            if unit[1] == "w":
                timedict["d"] += 7 * unit[0]
            else:
                timedict[unit[1]] += unit[0]

        # check non-whole numbers, and shift "0.2m" to 0.2*60 = 12 seconds
        def decimals(time):
            return time - int(time)

        def is_whole(time):
            return time - int(time) == 0

        if not is_whole(timedict["y"]):
            timedict["M"] += decimals(timedict["y"]) * 12
            timedict["y"] = int(timedict["y"])
        if not is_whole(timedict["M"]):
            timedict["d"] += decimals(timedict["M"]) * (365.2425 / 12)
            timedict["M"] = int(timedict["M"])
        if not is_whole(timedict["d"]):
            timedict["h"] += decimals(timedict["d"]) * 24
            timedict["d"] = int(timedict["d"])
        if not is_whole(timedict["h"]):
            timedict["m"] += decimals(timedict["h"]) * 60
            timedict["h"] = int(timedict["h"])
        if not is_whole(timedict["m"]):
            timedict["s"] += decimals(timedict["m"]) * 60
            timedict["m"] = int(timedict["m"])
        if not is_whole(timedict["s"]):
            timedict["f"] += decimals(timedict["s"]) * 1000000
            timedict["s"] = int(timedict["s"])

        # check overflows
        if timedict["s"] >= 60:
            timedict["m"] += timedict["s"] // 60
            timedict["s"] %= 60
        if timedict["m"] >= 60:
            timedict["h"] += timedict["m"] // 60
            timedict["m"] %= 60
        if timedict["h"] >= 24:
            timedict["d"] += timedict["h"] // 24
            timedict["h"] %= 24
        if timedict["M"] > 12:
            timedict["y"] += timedict["M"] // 12
            timedict["M"] %= 12
        if timedict["y"] >= 3999 or timedict["d"] >= 1500000:
            raise ValueError("I don't think I can remind you in that long!")

        timedict = {i: int(timedict[i]) for i in timedict}  # round everything down to the nearest whole number

        distance = datetime(timedict["y"], timedict["M"], 1,
                            timedict["h"], timedict["m"], timedict["s"], timedict["f"],
                            tzinfo=start_date.tzinfo)
        # cause you cant have >31 days in a month, but if overflow is given, then let
        # this timedelta calculate the new months/years
        distance += timedelta(days=timedict["d"] - 1)  # -1 cuz datetime.day has to start at 1 (first day of the month)

        return distance

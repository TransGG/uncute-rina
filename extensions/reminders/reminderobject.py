import asyncio  # to create new reminder task that runs immediately (from a not-async ReminderObject __init__ function)
from datetime import datetime, timedelta
from time import mktime

import discord

from resources.customs.bot import Bot
from resources.utils.timeparser import TimeParser

from extensions.reminders.reminderdict import ReminderDict
from extensions.reminders.views.copyreminder import CopyReminder, get_user_reminders
from extensions.reminders.views.sharereminder import ShareReminder
from extensions.reminders.views.timeofdayselection import TimeOfDaySelection


class ReminderObject:
    def __init__(
            self, client: Bot,
            creationtime: datetime,
            remindertime: datetime,
            user_id: int,
            reminder: str,
            user_reminders: list[ReminderDict],
            continued: bool = False
    ):
        self.client = client
        self.creationtime = creationtime
        self.remindertime = remindertime
        self.userID = user_id
        self.reminder = reminder
        self.alert = ""

        if continued:
            # self.remindertime = self.remindertime+(datetime.now()-datetime.utcnow())
            # self.creationtime = self.creationtime+(datetime.now()-datetime.utcnow())
            if self.remindertime < datetime.now():
                self.alert = ("Your reminder was delayed. Probably because the bot was offline for a while. I "
                              "hope it didn't cause much of an issue!\n")
                try:
                    asyncio.get_event_loop().create_task(self.send_reminder())
                except RuntimeError:
                    pass
                return
            client.sched.add_job(self.send_reminder, "date", run_date=self.remindertime)
        else:
            if self.remindertime < datetime.now():
                self.alert = ("Your reminder date/time has passed already. Perhaps the bot was offline for "
                              "a while; perhaps you just filled in a time in the past!\n")
                try:
                    asyncio.get_event_loop().create_task(self.send_reminder())
                except RuntimeError:
                    pass
                return
            collection = self.client.rina_db["reminders"]
            reminder_data: ReminderDict = {
                "creationtime": int(mktime(creationtime.timetuple())),
                "remindertime": int(mktime(remindertime.timetuple())),
                "reminder": reminder,
            }
            user_reminders.append(reminder_data)
            query = {"userID": user_id}
            collection.update_one(query, {"$set": {"reminders": user_reminders}}, upsert=True)
            # print(f"added job for {self.remindertime} and it's currently {self.creationtime}")
            client.sched.add_job(self.send_reminder, "date", run_date=self.remindertime)

    async def send_reminder(self):
        user = await self.client.fetch_user(self.userID)
        creationtime = int(mktime(self.creationtime.timetuple()))
        try:
            await user.send(f"{self.alert}On <t:{creationtime}:F>, you asked to be reminded of \"{self.reminder}\".")
        except discord.errors.Forbidden:
            pass  # I guess this user has no servers in common with Rina anymore. Sucks for them.
        collection = self.client.rina_db["reminders"]
        query = {"userID": self.userID}
        db_data = collection.find_one(query)
        index_subtraction = 0
        for reminder_index in range(len(db_data['reminders'])):
            if db_data['reminders'][reminder_index - index_subtraction]["remindertime"] <= int(
                    mktime(datetime.now().timetuple())):
                del db_data['reminders'][reminder_index - index_subtraction]
                index_subtraction += 1
                # See... If more than 1 reminder is placed at the same time, we don't want the reminder that is
                # triggered first to remove both reminders from the database... But it may also not be worth
                # figuring out if a reminder index exactly matches the one in the database to remove it.
                # So just remove one of them, and hope the update_one doesn't cause thread-unsafe shenanigans.
                # Any reminder that isn't deleted from the database (or is accidentally added back after) will
                # eventually be recreated and sent when the bot restarts.
                # Todo: I should probably handle this better.
                break
        if len(db_data['reminders']) > 0:
            collection.update_one(query, {"$set": {"reminders": db_data['reminders']}}, upsert=True)
        else:
            collection.delete_one(query)


class UnixTimestampInPastException(Exception):
    def __init__(self, unix_timestamp_string: str, creation_time: datetime):
        self.unix_timestamp_string = unix_timestamp_string
        self.creation_time = creation_time


class MalformedISODateTimeException(Exception):
    def __init__(self, ex: Exception):
        self.inner_exception = ex


class TimestampParseError(Exception):
    def __init__(self, inner_exception):
        self.inner_exception = inner_exception


async def _handle_reminder_timestamp_parsing(
        itx: discord.Interaction, reminder_datetime: str
) -> (datetime, discord.Interaction):
    # validate format
    # note: "t" here is lowercase because the reminder_datetime string gets lowercased...
    has_timezone = False
    if reminder_datetime.count("t") == 1:
        # check input character validity
        for char in reminder_datetime:
            if char not in "0123456789-t:+":
                raise ValueError(f"`{char}` cannot be used for a reminder date/time.")

        date, time = reminder_datetime.split("t")
        if date.count("-") != 2:
            raise ValueError("Incorrect date given! Please format the date as YYYY-MM-DD, like 2023-12-31")

        has_timezone = "+" in time or "-" in time
        if has_timezone:
            # to check if the user gave seconds, I count the amount of : in the message
            # If the timezone is provided you always have ":" extra: 23:04:23+01:00 = 3 colons
            time = time.split("+")[0]
            time = time.split("-")[0]
        if time.count(":") == 1:
            mode = TimestampFormats.DateTimeToMinutes
        elif time.count(":") == 2:
            mode = TimestampFormats.DateTimeToSeconds
        else:
            raise ValueError("Incorrect time given! Please format the time as HH:MM:SS or HH:MM, like 23:59:59")

    elif reminder_datetime.count("t") > 1:
        raise ValueError("You should only use 'T' once! Like so: 2023-12-31T23:59+0100. "
                         "Notice that the date and time are separated by the 'T', and "
                         "the timezone only by the '+' or '-' sign. Not an additional 'T'. :)")
    else:
        if reminder_datetime.count("-") != 2:  # should contain two dashes for YYYY-MM-DD
            raise ValueError("Incorrect date given! Please format the date as YYYY-MM-DD, like 2023-12-31")
        mode = TimestampFormats.DateNoTime

    # error for unimplemented: giving date and time format without a timezone
    if not has_timezone and mode != TimestampFormats.DateNoTime:
        raise ValueError("Because I don't know your timezone, I can't ensure it'll be sent at the right time. "
                         "Please add the timezone like so '-0100' or '+0900'.")

    # convert given time string to valid datetime
    timestamp_format = ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dt%H:%M%z", "%Y-%m-%d"][mode.value]
    try:
        timestamp = datetime.strptime(reminder_datetime, timestamp_format)
    except ValueError:
        raise ValueError(
            f"Incorrect format given! I could not convert {reminder_datetime} to format {timestamp_format}")

    distance = timestamp
    # clarify datetime timezone if necessary
    if mode == TimestampFormats.DateNoTime:
        options = {
            "1": (timestamp - timedelta(hours=12)),
            "2": (timestamp - timedelta(hours=12)),
            "3": timestamp,
            "4": (timestamp + timedelta(hours=6)),
            "5": (timestamp + timedelta(hours=12)),
            "6": (timestamp + timedelta(hours=18)),
            "7": (timestamp + timedelta(hours=24)),
        }
        query = f"Since a date format doesn't tell me what time you want the reminder, you can pick a time yourself:"
        for option in options:
            query += f"\n  `{option}.` <t:{int(mktime(options[option].timetuple()))}:F>"
        view = TimeOfDaySelection(list(options))
        await itx.response.send_message(query, view=view, ephemeral=True)
        await view.wait()
        if view.value is None:
            await itx.edit_original_response(content="Reminder creation menu timed out.", view=None)
            return
        distance = options[view.value]
        itx = view.return_interaction

    distance = datetime.fromtimestamp(mktime(distance.timetuple()))  # weird statement to remove timestamp awareness
    return distance, itx  # New itx is returned in case the response is used by the view


async def _parse_reminder_time(itx: discord.Interaction, reminder_datetime: str, ) -> (datetime, datetime):
    # Parse reminder input to get a datetime for the reminder scheduler
    _now = itx.created_at  # utc
    creation_time = _now.astimezone(tz=datetime.now().tzinfo)
    distance: datetime
    try:
        possible_timestamp_datetime = reminder_datetime.replace("<t:", "").split(":")[0].replace(">", "")
        if reminder_datetime.startswith("<t:") and possible_timestamp_datetime.isdecimal():
            if int(possible_timestamp_datetime) < mktime(datetime.timetuple(creation_time)):
                raise UnixTimestampInPastException(possible_timestamp_datetime, creation_time)
            distance = datetime.fromtimestamp(int(possible_timestamp_datetime))
        else:
            reminder_datetime = ((" " + reminder_datetime)
                                 .replace(",", "")
                                 .replace("and", "")
                                 .replace(" in ", "")
                                 .replace(" ", "")
                                 .strip().lower())
            distance = TimeParser.parse_date(reminder_datetime, creation_time)
    except ValueError as ex:
        if '-' not in reminder_datetime:
            raise MalformedISODateTimeException(ex)

        try:
            distance, itx = await _handle_reminder_timestamp_parsing(itx, reminder_datetime)
            time_passed = distance - creation_time
            if time_passed > timedelta(days=365 * 3999):
                raise ValueError("I don't think I can remind you `{}` years into the future..."
                                 .format(time_passed.days // 365.2425))
        except ValueError as ex:
            raise TimestampParseError(ex)

    return distance, creation_time


async def create_reminder(
        client: Bot,
        itx: discord.Interaction,
        distance: datetime,
        creation_time: datetime, reminder: str,
        db_data: list[ReminderDict],
        from_copy: bool = False
):
    reminder_object = ReminderObject(client, creation_time, distance, itx.user.id, reminder, db_data)
    _distance = int(mktime(distance.timetuple()))
    cmd_mention = client.get_command_mention("reminder reminders")
    view = ShareReminder()
    if from_copy:
        view = None
    creation_msg = await itx.response.send_message(
        f"Successfully created a reminder for you on <t:{_distance}:F> for \"{reminder}\"!\n"
        f"Use {cmd_mention} to see your list of reminders",
        view=view, ephemeral=True)
    await view.wait()
    if view.value == 1:
        msg = f"{itx.user.mention} shared a reminder on <t:{_distance}:F> for \"{reminder}\""
        copy_view = CopyReminder(client, create_reminder, reminder_object, timeout=300)
        try:
            await itx.channel.send(content=msg, view=copy_view, allowed_mentions=discord.AllowedMentions.none())
            await itx.edit_original_response(view=None)
            return
        except discord.errors.Forbidden:
            await view.return_interaction.response(msg, view=copy_view, allowed_mentions=discord.AllowedMentions.none())
    await creation_msg.edit(view=None)


async def parse_and_create_reminder(client: Bot, itx: discord.Interaction, reminder_datetime: str, reminder: str):
    # Check if user has too many reminders (max 50 allowed (internally chosen limit))
    user_reminders = get_user_reminders(client, itx.user)
    if len(user_reminders) > 50:
        cmd_mention = client.get_command_mention("reminder reminders")
        cmd_mention1 = client.get_command_mention("reminder remove")
        await itx.response.send_message(f"Please don't make more than 50 reminders. Use {cmd_mention} to see "
                                        f"your reminders, and use {cmd_mention1} `item: ` to remove a reminder",
                                        ephemeral=True)
        return

    try:
        distance, creation_time = await _parse_reminder_time(itx, reminder_datetime)
    except UnixTimestampInPastException as ex:
        await itx.response.send_message(
            "Couldn't make new reminder: \n"
            "> Your message was interpreted as a unix timestamp, but this timestamp would be before "
            "the current time!\n"
            f"Given timestamp: {int(ex.unix_timestamp_string)}"
            f"(<t:{int(ex.unix_timestamp_string)}:F>).\n"
            f"Current time: {mktime(datetime.timetuple(ex.now))}"
            f"(<t:{mktime(datetime.timetuple(ex.now))}:F>).\n"
            ""
        )
        return
    except MalformedISODateTimeException as ex:
        await itx.response.send_message(
            f"Couldn't make new reminder:\n> {str(ex.inner_exception)}\n"
            "You can only use a format like [number][letter], or yyyy-mm-ddThh:mm:ss+0000. Some examples:\n"
            '    "3mo 0.5d", "in 2 hours, 3.5 mins", "1 year and 3 seconds", "3day4hour", "4d1m", '
            '"2023-12-31T23:59+0100", "<t:12345678>\n'
            "Words like \"in\" and \"and\" are ignored, so you can use those for readability if you'd like.\n"
            '    year = y, year, years\n'
            '    month = mo, month, months\n'
            '    week = w, week, weeks\n'
            '    day = d, day, days\n'
            '    hour = h, hour, hours\n'
            '    minute = m, min, mins, minute, minutes\n'
            '    second = s, sec, secs, second, seconds\n'
            f'For more info, type {self.client.get_command_mention("help")} `page:113`',
            ephemeral=True)
        return
    except TimestampParseError as ex:
        await itx.response.send_message(
            f"Couldn't make new reminder:\n> {str(ex.inner_exception)}\n\n"
            "You can make a reminder for days in advance, like so: \"4d12h\", \"4day 12hours\" or "
            "\"in 3 minutes and 2 seconds\"\n"
            "You can also use ISO8601 format, like '2023-12-31T23:59+0100', or just '2023-12-31'\n"
            "Or you can use Unix Epoch format: the amount of seconds since January 1970: '1735155750"
            "\n"
            "If you give a time but not a timezone, I don't want you to get reminded at the wrong time, "
            "so I'll say something went wrong.",
            ephemeral=True)
        return

    await create_reminder(client, itx, distance, creation_time, reminder, user_reminders, False)

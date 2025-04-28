import asyncio  # to create new reminder task that runs immediately (from a not-async ReminderObject __init__ function)
from datetime import datetime, timedelta, timezone

import discord

from resources.customs import Bot
from resources.utils import (
    TimeParser, MissingQuantityException, MissingUnitException
)

from extensions.reminders.exceptions import (
    UnixTimestampInPastException, TimestampParseException,
    MalformedISODateTimeException
)
from extensions.reminders.objects import (
    ReminderDict, TimestampFormats, DatabaseData
)
from extensions.reminders.utils import get_user_reminders
from extensions.reminders.views import (
    CopyReminder, ShareReminder, TimeOfDaySelection
)


async def relaunch_ongoing_reminders(
        client: Bot,
):
    """
    Helper to start stored reminders after the bot restarts.

    :param client: The client to fetch existing reminders and
     store new scheduler events.
    """
    collection = client.async_rina_db["reminders"]
    query = {}
    db_data = collection.find(query)
    async for entry in db_data:
        entry: DatabaseData
        try:
            for reminder in entry["reminders"]:
                creation_time = datetime.fromtimestamp(
                    reminder['creationtime'], timezone.utc)
                reminder_time = datetime.fromtimestamp(
                    reminder['remindertime'], timezone.utc)
                ReminderObject(
                    client, creation_time, reminder_time,
                    entry['userID'],
                    reminder['reminder'], entry["reminders"],
                    continued=True
                )
        except KeyError:
            pass


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
            # self.remindertime = self.remindertime.astimezone()
            # self.creationtime = self.creationtime.astimezone()
            if self.remindertime < datetime.now().astimezone():
                self.alert = ("Your reminder was delayed. Probably because the bot was offline for a while. I "
                              "hope it didn't cause much of an issue!\n")
                try:
                    asyncio.get_event_loop().create_task(self.send_reminder())
                except RuntimeError:
                    pass
                return
            client.sched.add_job(self.send_reminder, "date", run_date=self.remindertime)
        else:
            if self.remindertime < datetime.now().astimezone():
                self.alert = ("Your reminder date/time has passed already. Perhaps the bot was offline for "
                              "a while; perhaps you just filled in a time in the past!\n")
                try:
                    asyncio.get_event_loop().create_task(self.send_reminder())
                except RuntimeError:
                    pass
                return
            collection = self.client.rina_db["reminders"]
            reminder_data: ReminderDict = {
                "creationtime": int(creationtime.timestamp()),
                "remindertime": int(remindertime.timestamp()),
                "reminder": reminder,
            }
            user_reminders.append(reminder_data)
            query = {"userID": user_id}
            collection.update_one(query, {"$set": {"reminders": user_reminders}}, upsert=True)
            # print(f"added job for {self.remindertime} and it's currently {self.creationtime}")
            client.sched.add_job(self.send_reminder, "date", run_date=self.remindertime)

    async def send_reminder(self):
        user = await self.client.fetch_user(self.userID)
        creationtime = int(self.creationtime.timestamp())
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
                    datetime.now().timestamp()):
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


async def _handle_reminder_timestamp_parsing(
        itx: discord.Interaction,
        reminder_datetime: str
) -> (datetime, discord.Interaction):
    # validate format
    # note: "t" here is lowercase because the reminder_datetime string gets lowercased...
    has_timezone = False
    if reminder_datetime.count("t") == 1:
        # check input character validity
        for char in reminder_datetime:
            if char not in "0123456789-t:+z":  # z for timezone +0000
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
    timestamp_format = ["%Y-%m-%dt%H:%M:%S%z", "%Y-%m-%dt%H:%M%z", "%Y-%m-%d"][mode.value]
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
        query = "Since a date format doesn't tell me what time you want the reminder, you can pick a time yourself:"
        for option in options:
            query += f"\n  `{option}.` <t:{int(options[option].timestamp())}:F>"
        view = TimeOfDaySelection(list(options))
        await itx.response.send_message(query, view=view, ephemeral=True)
        await view.wait()
        if view.value is None:
            await itx.edit_original_response(content="Reminder creation menu timed out.", view=None)
            return
        distance = options[view.value]
        itx = view.return_interaction

    return distance, itx  # New itx is returned in case the response is used by the view


async def _parse_reminder_time(itx: discord.Interaction, reminder_datetime: str) -> tuple[datetime, datetime]:
    """
    Parse a datetime string: relative to today (2d 11h); a ISO8601 timestamp; or a unix timestamp. It outputs
    the reminder's datetime and interaction's creation time with timezone awareness. If the ISO timestamp gives
    a date but no time, it will prompt the user to select a time of day, and then returns the respective datetime.

    :param itx: The interaction to interpret as creation time, and with which to send a TimeOfDaySelection view.
    :param reminder_datetime: The string to interpret and convert into the datetime for the reminder.

    :return: A tuple of (reminder datetime, interaction creation time)

    :raise UnixTimestampInPastException:
    :raise MalformedISODateTimeException:
    :raise TimestampParseException:
    :raise MissingQuantityException:
    :raise MissingUnitException:
    """
    # Parse reminder input to get a datetime for the reminder scheduler
    creation_time = itx.created_at  # utc
    assert creation_time.tzinfo == timezone.utc  # it is timezone aware, in utc
    distance: datetime
    try:
        possible_timestamp_datetime = reminder_datetime.replace("<t:", "").split(":")[0]
        if possible_timestamp_datetime.isdecimal() and len(possible_timestamp_datetime) > 6:  # 1000000 = 20 Jan 1970
            distance = datetime.fromtimestamp(int(possible_timestamp_datetime), timezone.utc)
            if distance < creation_time:
                raise UnixTimestampInPastException(distance, creation_time)
        else:
            reminder_datetime = ((" " + reminder_datetime)
                                 .replace(",", "")
                                 .replace("and", "")
                                 .replace(" in ", "")
                                 .replace(" ", "")
                                 .strip().lower())
            distance = TimeParser.parse_date(reminder_datetime, creation_time)
    except ValueError:

        try:
            distance, itx = await _handle_reminder_timestamp_parsing(itx, reminder_datetime)
            time_passed = distance - creation_time
            if time_passed > timedelta(days=365 * 3999):
                raise ValueError("I don't think I can remind you `{}` years into the future..."
                                 .format(time_passed.days // 365.2425))
        except ValueError as ex:
            raise TimestampParseException(ex)

    return distance, creation_time


async def _create_reminder(
        itx: discord.Interaction,
        distance: datetime,
        creation_time: datetime, reminder: str,
        db_data: list[ReminderDict],
        from_copy: bool = False
):
    reminder_object = ReminderObject(itx.client, creation_time, distance, itx.user.id, reminder, db_data)
    _distance = int(distance.timestamp())
    cmd_mention = itx.client.get_command_mention("reminder reminders")
    view = ShareReminder()
    if from_copy:
        # send message without view.
        await itx.response.send_message(
            f"Successfully created a reminder for you on <t:{_distance}:F> for \"{reminder}\"!\n"
            f"Use {cmd_mention} to see your list of reminders",
            ephemeral=True
        )
        return
    else:
        await itx.response.send_message(
            f"Successfully created a reminder for you on <t:{_distance}:F> for \"{reminder}\"!\n"
            f"Use {cmd_mention} to see your list of reminders",
            view=view, ephemeral=True
        )

    await view.wait()
    if view.value == 1:
        msg = f"{itx.user.mention} shared a reminder on <t:{_distance}:F> for \"{reminder}\""
        copy_view = CopyReminder(_create_reminder, reminder_object, timeout=300)
        try:
            await itx.channel.send(content=msg, view=copy_view, allowed_mentions=discord.AllowedMentions.none())
        except discord.errors.Forbidden:
            await view.return_interaction.response.send_message(
                msg, view=copy_view,
                allowed_mentions=discord.AllowedMentions.none()
            )
    await itx.edit_original_response(view=None)


async def parse_and_create_reminder(
        itx: discord.Interaction,
        reminder_datetime: str,
        reminder: str
):
    # Can't put this function reminders.utils because it calls
    #  _create_reminder, which creates a ReminderObject, so it would be
    #  better-fitting in this same file.

    # Check if user has too many reminders (max 50 allowed
    #  (internally chosen limit))
    user_reminders = get_user_reminders(itx.client, itx.user)
    if len(user_reminders) > 50:
        cmd_mention = itx.client.get_command_mention("reminder reminders")
        cmd_mention1 = itx.client.get_command_mention("reminder remove")
        await itx.response.send_message(f"Please don't make more than 50 reminders. Use {cmd_mention} to see "
                                        f"your reminders, and use {cmd_mention1} `item: ` to remove a reminder",
                                        ephemeral=True)
        return

    cmd_mention_help = itx.client.get_command_mention("help")
    try:
        distance, creation_time = await _parse_reminder_time(itx, reminder_datetime)
    except UnixTimestampInPastException as ex:
        timestamp_unix = int(ex.distance.timestamp())
        await itx.response.send_message(
            "Couldn't make new reminder: \n"
            "> Your message was interpreted as a unix timestamp, but this timestamp would be before "
            "the current time!\n"
            f"Interpreted timestamp: {timestamp_unix} "
            f"(<t:{timestamp_unix}:F>, <t:{timestamp_unix}:R>).\n"
            f"Current time: {int(ex.creation_time.timestamp() + 0.5)} "  # round up to ensure t=0.99 > t=0.80
            f"(<t:{int(ex.creation_time.timestamp() + 0.5)}:F>, <t:{int(ex.creation_time.timestamp() + 0.5)}:R>).\n"
            f"For more info, use {cmd_mention_help} `page:113`.",
            ephemeral=True
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
            f'For more info, use {cmd_mention_help} `page:113`.',
            ephemeral=True)
        return
    except TimestampParseException as ex:
        await itx.response.send_message(
            f"Couldn't make new reminder:\n> {str(ex.inner_exception)}\n\n"
            "You can make a reminder for days in advance, like so: \"4d12h\", \"4day 12hours\" or "
            "\"in 3 minutes and 2 seconds\"\n"
            "You can also use ISO8601 format, like '2023-12-31T23:59+0100', or just '2023-12-31'\n"
            "Or you can use Unix Epoch format: the amount of seconds since January 1970: '1735155750"
            "\n"
            "If you give a time but not a timezone, I don't want you to get reminded at the wrong time, "
            "so I'll say something went wrong.\n"
            f"For more info, use {cmd_mention_help} `page:113`.",
            ephemeral=True
        )
        return
    except MissingQuantityException as ex:
        await itx.response.send_message(
            f"Couldn't make new reminder:\n> {str(ex)}\n\n"
            f"Be sure you start the reminder time with a number like \"4 days\".\n"
            f"For more info, use {cmd_mention_help} `page:113`.",
            ephemeral=True
        )
        return
    except MissingUnitException as ex:
        await itx.response.send_message(
            f"Couldn't make new reminder:\n> {str(ex)}\n\n"
            f"Be sure you end the reminder time with a unit like \"4 days\".\n"
            f"If you intended to use a unix timestamp instead, make sure your timestamp is correct. Any number"
            f"below 1000000 is parsed in the \"1 day 2 hours\" format, which means not providing a unit will"
            f"give this error. Note: a unix timestamp of 1000000 is 20 Jan 1970 (<t\\:1000000:D> = <t:1000000:D>)\n"
            f"For more info, use {cmd_mention_help} `page:113`.",
            ephemeral=True
        )
        return

    await _create_reminder(itx, distance, creation_time, reminder, user_reminders, False)

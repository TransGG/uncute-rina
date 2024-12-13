import discord, discord.ext.commands as commands, discord.app_commands as app_commands
from time import mktime  # for reminder times
from datetime import datetime, timedelta
from resources.customs.bot import Bot
from resources.customs.reminders import ReminderObject, BumpReminderObject
from resources.utils.timeparser import TimeParser
from resources.views.reminders import TimeOfDaySelection
import enum


class TimestampFormats(enum.Enum):
    DateTimeToSeconds = 0  # YYYY-MM-DDtHH:MM:SS
    DateTimeToMinutes = 1  # YYYY-MM-DDtHH:MM
    DateNoTime = 2  # YYYY-MM-DD


async def handle_reminder_timestamp_parsing(itx: discord.Interaction, reminder_datetime: str) -> (
        datetime, discord.Interaction):
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


class RemindersCog(commands.GroupCog, name="reminder"):
    def __init__(self, client: Bot):
        self.client: Bot = client

    @app_commands.command(name="remindme", description="Add a reminder for yourself!")
    @app_commands.describe(reminder_datetime="When would you like me to remind you? (1d2h, 5 weeks, 1mo10d)",
                           reminder="What would you like me to remind you of?")
    @app_commands.rename(reminder_datetime='time')
    async def remindme(self, itx: discord.Interaction, reminder_datetime: str, reminder: str):
        # Supported formats:
        # - "next thursday at 3pm"
        # - "tomorrow"
        # + "in 3 days"
        # + "2d"
        # - "2022-07-03"
        # + "2022y4mo3days"
        # - "<t:293847839273>"
        if len(reminder) > 1500:
            await itx.response.send_message(
                "Please keep reminder text below 1500 characters... Otherwise I can't send you a message about it!",
                ephemeral=True)
            return
        # Check if user has an entry in database yet.
        collection = self.client.rina_db["reminders"]
        query = {"userID": itx.user.id}
        db_data = collection.find_one(query)
        if db_data is None:
            collection.insert_one(query)
            db_data = collection.find_one(query)

        # Check if user has too many reminders (max 50 allowed (internally chosen limit))
        try:
            if len(db_data['reminders']) > 50:
                cmd_mention = self.client.get_command_mention("reminder reminders")
                cmd_mention1 = self.client.get_command_mention("reminder remove")
                await itx.response.send_message(f"Please don't make more than 50 reminders. Use {cmd_mention} to see "
                                                f"your reminders, and use {cmd_mention1} `item: ` to remove a reminder",
                                                ephemeral=True)
                return
        except KeyError:
            pass

        # Parse reminder input to get a datetime for the reminder scheduler
        _now = itx.created_at  # utc
        now = _now.astimezone(tz=datetime.now().tzinfo)
        try:
            possible_timestamp_datetime = reminder_datetime.replace("<t:", "").split(":")[0].replace(">", "")
            if reminder_datetime.startswith("<t:") and possible_timestamp_datetime.isdecimal():
                if int(possible_timestamp_datetime) < mktime(datetime.timetuple(now)):
                    await itx.response.send_message(
                        "Couldn't make new reminder: \n"
                        "> Your message was interpreted as a unix timestamp, but this timestamp would be before "
                        "the current time!\n"
                        f"Given timestamp: {int(possible_timestamp_datetime)}"
                        f"(<t:{int(possible_timestamp_datetime)}:F>).\n"
                        f"Current time: {mktime(datetime.timetuple(now))}"
                        f"(<t:{mktime(datetime.timetuple(now))}:F>).\n"
                        ""
                    )
                    return
                distance = datetime.fromtimestamp(int(possible_timestamp_datetime))
            else:
                reminder_datetime = (" " + reminder_datetime).replace(",", "").replace("and", "").replace(" in ",
                                                                                                          "").replace(
                    " ", "").strip().lower()
                distance = TimeParser.parse_date(reminder_datetime, now)
        except ValueError as ex:
            if '-' not in reminder_datetime:
                await itx.response.send_message(
                    f"Couldn't make new reminder:\n> {str(ex)}\n"
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

            try:
                distance, itx = await handle_reminder_timestamp_parsing(itx, reminder_datetime)
                time_passed: timedelta = distance - now
                # apparently `distance - now` does not get typed as timedelta :P silly
                if time_passed > timedelta(days=365 * 3999):
                    raise ValueError(
                        f"I don't think I can remind you `{time_passed.days // 365.2425}` years into the future...")
            except ValueError as ex:
                await itx.response.send_message(
                    f"Couldn't make new reminder:\n> {str(ex)}\n\n"
                    "You can make a reminder for days in advance, like so: \"4d12h\", \"4day 12hours\" or "
                    "\"in 3 minutes and 2 seconds\"\n"
                    "You can also use ISO8601 format, like '2023-12-31T23:59+0100', or just '2023-12-31'\n"
                    "Or you can use Unix Epoch format: the amount of seconds since January 1970: '1735155750"
                    "\n"
                    "If you give a time but not a timezone, I don't want you to get reminded at the wrong time, "
                    "so I'll say something went wrong.",
                    ephemeral=True)
                return

        ReminderObject(self.client, now, distance, itx.user.id, reminder, db_data)
        _distance = int(mktime(distance.timetuple()))
        cmd_mention = self.client.get_command_mention("reminder reminders")
        await itx.response.send_message(
            f"Successfully created a reminder for you on <t:{_distance}:F> for \"{reminder}\"!\n"
            f"Use {cmd_mention} to see your list of reminders",
            ephemeral=True)

    @app_commands.command(name="reminders", description="Check your list of reminders!")
    @app_commands.describe(item="Which reminder would you like to know more about? (use reminder-ID)")
    async def reminders(self, itx: discord.Interaction, item: int = None):
        collection = self.client.rina_db["reminders"]
        query = {"userID": itx.user.id}
        db_data = collection.find_one(query)
        if db_data is None:
            cmd_mention = self.client.get_command_mention("reminder remindme")
            await itx.response.send_message(
                f"You don't have any reminders running at the moment!\nUse {cmd_mention} to make a reminder!",
                ephemeral=True)
            return

        try:
            out = []
            index = 0
            if item is None:
                for reminder in db_data['reminders']:
                    out.append(f"ID: `{index}` | Created at: <t:{reminder['remindertime']}:F> | "
                               f"Remind you about: {discord.utils.escape_markdown(reminder['reminder'])}")
                    index += 1
                out_msg = "Your reminders:\n" + '\n'.join(out)
                if len(out_msg) >= 1995:
                    out = []
                    index = 0
                    for reminder in db_data['reminders']:
                        out.append(f"`{index}` | <t:{reminder['remindertime']}:F>")
                        index += 1
                    cmd_mention = self.client.get_command_mention("reminder reminders")
                    out_msg = ((f"You have {len(db_data['reminders'])} reminders "
                               f"(use {cmd_mention} `item: ` to get more info about a reminder):\n") +
                               '\n'.join(out)[:1996])
                await itx.response.send_message(out_msg, ephemeral=True)
            else:
                reminder = db_data['reminders'][item]
                await itx.response.send_message(
                    f"Showing reminder `{index}` out of `{len(db_data['reminders'])}`:\n" +
                    f"  ID: `{index}`\n" +
                    f"  Created at:             <t:{reminder['creationtime']}:F> (<t:{reminder['creationtime']}>)\n" +
                    f"  Reminding you at: <t:{reminder['remindertime']}:F> (<t:{reminder['remindertime']}:R>)\n" +
                    f"  Remind you about: {discord.utils.escape_markdown(reminder['reminder'])}",
                    ephemeral=True)
        except IndexError:
            cmd_mention = self.client.get_command_mention("reminder reminders")
            await itx.response.send_message(
                f"I couldn't find any reminder with that ID!\n"
                f"Look for the \"ID: `0`\" at the beginning of your reminder on the reminder list ({cmd_mention})",
                ephemeral=True)
            return
        except KeyError:
            cmd_mention = self.client.get_command_mention("reminder remindme")
            await itx.response.send_message(
                f"You don't have any reminders running at the moment.\nUse {cmd_mention} to make a reminder!",
                ephemeral=True)
            return

    @app_commands.command(name="remove", description="Remove of your reminders")
    @app_commands.describe(item="Which reminder would you like to know more about? (use reminder-ID)")
    async def remove(self, itx: discord.Interaction, item: int):
        collection = self.client.rina_db["reminders"]
        query = {"userID": itx.user.id}
        db_data = collection.find_one(query)
        if db_data is None:
            cmd_mention = self.client.get_command_mention("reminder remindme")
            await itx.response.send_message(
                f"You don't have any reminders running at the moment! (so I can't remove any either..)\n"
                f"Use {cmd_mention} to make a reminder!",
                ephemeral=True)
            return

        try:
            del db_data['reminders'][item]
        except IndexError:
            cmd_mention = self.client.get_command_mention("reminder reminders")
            await itx.response.send_message(
                f"I couldn't find any reminder with that ID!\n"
                f"Look for the \"ID: `0`\" at the beginning of your reminder on the reminder list ({cmd_mention})",
                ephemeral=True)
            return
        except KeyError:
            cmd_mention = self.client.get_command_mention("reminder remindme")
            await itx.response.send_message(
                f"You don't have any reminders running at the moment. (so I can't remove any either..)\n"
                f"Use {cmd_mention} to make a reminder!",
                ephemeral=True)
            return
        query = {"userID": itx.user.id}
        if len(db_data['reminders']) > 0:
            collection.update_one(query, {"$set": {"reminders": db_data['reminders']}}, upsert=True)
        else:
            collection.delete_one(query)
        await itx.response.send_message(
            f"Successfully removed this reminder! You have {len(db_data['reminders'])} other reminders going.",
            ephemeral=True)


class BumpReminder(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if len(message.embeds) > 0:
            if message.embeds[0].description is not None:
                if message.embeds[0].description.startswith("Bump done!"):
                    # collection = self.client.rina_db["guildInfo"]
                    # query = {"guild_id": message.guild.id}
                    # guild_data = collection.find_one(query)
                    # bump_bot_id = guild_data["bumpBot"]
                    bump_bot_id = await self.client.get_guild_info(message.guild, "bumpBot")

                    if message.author.id == bump_bot_id:
                        remindertime = datetime.now() + timedelta(hours=2)
                        BumpReminderObject(self.client, message.guild, remindertime)


async def setup(client):
    await client.add_cog(RemindersCog(client))
    await client.add_cog(BumpReminder(client))

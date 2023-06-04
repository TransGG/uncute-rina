from Uncute_Rina import *
from import_modules import *

logger = logging.getLogger("apscheduler")
logger.setLevel(logging.WARNING)
# remove annoying 'Scheduler started' message on sched.start()
sched = AsyncIOScheduler(logger=logger)
sched.start()


def parse_date(time_string, now: datetime):
    # - "next thursday at 3pm"
    # - "tomorrow"
    # + "in 3 days"
    # + "2d"
    # - "2022-07-03"
    # + "2022y4mo3days"
    # - "<t:293847839273>"
    timeterms = {
        "y":["y","year","years"],
        "M":["mo","month","months"],
        "w":["w","week","weeks"],
        "d":["d","day","days"],
        "h":["h","hour","hours"],
        "m":["m","min","mins","minute","minutes"],
        "s":["s","sec", "secs","second","seconds"]
    }

    time_units = []
    low_index = 0
    number_index = 0
    is_number = True
    def magic_date_split(index, low_index, number_index):
        try:
            time = [float(time_string[low_index:number_index + 1])]
        except ValueError:
            raise ValueError(f"The value for your date/time has to be a number (0, 1, 2) not '{time_string[low_index:number_index + 1]}'")
        date = time_string[number_index + 1:index]
        for unit in timeterms:
            if date in timeterms[unit]:
                time.append(unit)
                break
        else:
            raise ValueError(f"You can't use '{date}' as unit for your date/time")
        return time
    index = 0 #for making my IDE happy
    for index in range(len(time_string)):
        # for index in "14days7hours": get index of the first number, the last number, and the last letter before the next number:
        #    "1" to "<d" (until but not including "d") and "<7" -> so "1" to "4" and "d" to "s"
        # then it converts "14" to a number and "days" to the timedict of "d", so you get [[14,'d'], [7,'h']]
        if time_string[index] in "0123456789.":
            if not is_number:
                time_units.append(magic_date_split(index, low_index, number_index))
                low_index = index
            number_index = index
            is_number = True
        else:
            is_number = False
    time_units.append(magic_date_split(index + 1, low_index, number_index))

    timedict = {
        "y":now.year,
        "M":now.month,
        "d":now.day-1,
        "h":now.hour,
        "m":now.minute,
        "s":now.second,
        "f":0, # microseconds can only be set with "0.04s" eg.
        # now.day-1 for _timedict["d"] because later, datetime(day=...) starts with 1, and adds this value with
        # timedelta. This is required cause the datetime() doesn't let you set "0" for days. (cuz a month starts
        # at day 1)
    }
    
    # add values to each timedict key
    for unit in time_units:
        if unit[1] == "w":
            timedict["d"] += 7*unit[0]
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
    while timedict["s"] >= 60:
        timedict["s"] -= 60
        timedict["m"] += 1
    while timedict["m"] >= 60:
        timedict["m"] -= 60
        timedict["h"] += 1
    while timedict["h"] >= 24:
        timedict["h"] -= 24
        timedict["d"] += 1
    while timedict["M"] > 12:
        timedict["M"] -= 12
        timedict["y"] += 1
    if timedict["y"] >= 3999 or timedict["d"] >= 1500000:
        raise ValueError("I don't think I can remind you in that long!")
    
    timedict = {i:int(timedict[i]) for i in timedict}
    
    distance = datetime(timedict["y"],timedict["M"],1,timedict["h"],timedict["m"],timedict["s"])
    # cause you cant have >31 days in a month, but if overflow is given, then let this timedelta calculate the new months/years
    distance += timedelta(days=timedict["d"])

    return distance


class Reminders(commands.GroupCog,name="reminder"):
    def __init__(self, client: Bot):
        global RinaDB
        RinaDB = client.RinaDB
        self.client = client

    class Reminder:
        def __init__(self, client: Bot, creationtime, remindertime, userID, reminder, db_data, continued=False):
            self.client = client
            self.creationtime = creationtime
            self.remindertime = remindertime
            self.userID = userID
            self.reminder = reminder
            self.alert = ""
            if continued:
                # self.remindertime = self.remindertime+(datetime.now()-datetime.utcnow())
                # self.creationtime = self.creationtime+(datetime.now()-datetime.utcnow())
                if self.remindertime < datetime.now():
                    self.alert = "Your reminder was delayed. Probably because the bot was offline for a while. I hope it didn't cause much of an issue!\n"
                    try:
                        asyncio.get_event_loop().create_task(self.send_reminder())
                    except RuntimeError:
                        pass
                    return
                sched.add_job(self.send_reminder, "date", run_date=self.remindertime)
            else:
                if self.remindertime < datetime.now():
                    self.alert = "Your reminder date/time has passed already. Perhaps the bot was offline for a while; perhaps you just filled in a time in the past!\n"
                    try:
                        asyncio.get_event_loop().create_task(self.send_reminder())
                    except RuntimeError:
                        pass
                    return
                collection = RinaDB["reminders"]
                reminderData = {
                    "creationtime":int(mktime(creationtime.timetuple())),
                    "remindertime":int(mktime(remindertime.timetuple())),
                    "reminder":reminder,
                }
                try:
                    userReminders = db_data['reminders']
                except KeyError:
                    userReminders = []
                userReminders.append(reminderData)
                query = {"userID": userID}
                collection.update_one(query, {"$set":{"reminders":userReminders}}, upsert=True)
                # print(f"added job for {self.remindertime} and it's currently {self.creationtime}")
                sched.add_job(self.send_reminder, "date", run_date=self.remindertime)

        async def send_reminder(self):
            user = await self.client.fetch_user(self.userID)
            creationtime = int(mktime(self.creationtime.timetuple()))
            try:
                await user.send(f"{self.alert}On <t:{creationtime}:F>, you asked to be reminded of \"{self.reminder}.\"")
            except discord.errors.Forbidden:
                pass # I guess this user has no servers in common with Rina anymore. Sucks for them.
            collection = self.client.RinaDB["reminders"]
            query = {"userID": self.userID}
            db_data = collection.find_one(query)
            indexSubtraction = 0
            for reminderIndex in range(len(db_data['reminders'])):
                if db_data['reminders'][reminderIndex-indexSubtraction]["remindertime"] <= int(mktime(datetime.now().timetuple())):
                    del db_data['reminders'][reminderIndex-indexSubtraction]
                    indexSubtraction += 1
            if len(db_data['reminders']) > 0:
                collection.update_one(query, {"$set":{"reminders":db_data['reminders']}}, upsert=True)
            else:
                collection.delete_one(query)

    @app_commands.command(name="remindme",description="Add a reminder for yourself!")
    @app_commands.describe(reminder_datetime="When would you like me to remind you? (1d2h, 5 weeks, 1mo10d)",
                           reminder="What would you like me to remind you of")
    @app_commands.rename(reminder_datetime='time')
    async def remindme(self, itx: discord.Interaction, reminder_datetime: str, reminder: str):
        if len(reminder) > 1500:
            await itx.response.send_message("Please keep reminder text below 1500 characters... Otherwise I can't send you a message about it!",ephemeral=True)
            return
        collection = RinaDB["reminders"]
        query = {"userID": itx.user.id}
        db_data = collection.find_one(query)
        if db_data is None:
            collection.insert_one(query)
            db_data = collection.find_one(query)
        try:
            if len(db_data['reminders']) > 50:
                cmd_mention = self.client.get_command_mention("reminder reminders")
                cmd_mention1 = self.client.get_command_mention("reminder remove")
                await itx.response.send_message(f"Please don't make more than 50 reminders. Use {cmd_mention} to see "
                                                f"your reminders, and use {cmd_mention1} `item: ` to remove a reminder",ephemeral=True)
                return
        except KeyError:
            pass

        _now = itx.created_at # utc
        now = _now.astimezone(tz=datetime.now().tzinfo)
        try:
            reminder_datetime = (" "+reminder_datetime).replace(",","").replace("and","").replace(" in ", "").replace(" ","").strip().lower()
            distance = parse_date(reminder_datetime, now)
        except ValueError as ex:
            if '-' not in reminder_datetime:
                await itx.response.send_message(
                    f"Couldn't make new reminder:\n> {str(ex)}\n"
                    "You can only use a format like [number][letter], or yyyy-mm-ddThh:mm:ss+0000. Some examples:\n"
                    '    "3mo 0.5d", "in 2 hours, 3.5 mins", "1 year and 3 seconds", "3day4hour", "4d1m", "2023-12-31T23:59+0100"\n'
                    "Words like \"in\" and \"and\" are ignored, so you can use those for readability if you'd like.\n"
                    '    year = y, year, years\n'
                    '    month = mo, month, months\n'
                    '    week = w, week, weeks\n'
                    '    day = d, day, days\n'
                    '    hour = h, hour, hours\n'
                    '    minute = m, min, mins, minute, minutes\n'
                    '    second = s, sec, secs, second, seconds\n',
                    ephemeral=True)
                return
            
            class TimeOfDaySelection(discord.ui.View):
                class TimeOfDayButton(discord.ui.Button):
                    def __init__(self, view: discord.ui.View, label: str, **kwargs):
                        self.value = None
                        self._label = label
                        self._view = view
                        self.return_interaction = None
                        super().__init__(label=label, **kwargs)
                    
                    async def callback(self, interaction: discord.Interaction):
                        self._view.value = self._label
                        self._view.return_interaction = interaction
                        self._view.stop()

                def __init__(self, options, timeout=180):
                    super().__init__()
                    self.value: str = None
                    self.return_interaction: discord.Interaction = None
                    self.timeout = timeout

                    for option in options:
                        self.add_item(self.TimeOfDayButton(self, style=discord.ButtonStyle.green, label=option))

            mode = 0
            try:
                # note: "t" here is lowercase because the reminder_datetime string gets lowercased..
                if "t" in reminder_datetime:
                    for char in reminder_datetime:
                        if char not in "0123456789-t:+":
                            raise ValueError(f"`{char}` cannot be used for a reminder date/time.")
                    
                    if reminder_datetime.count("t") > 1:
                        raise ValueError(
                            "You should only use 'T' once! Like so: 2023-12-31T23:59+0100. "
                            "Notice that the date and time are separated by the 'T', and the timezone only by the '+' or '-' sign. Not an additional 'T'. :)")
                    date, time = reminder_datetime.split("t")
                    if time.count(":") not in [1,2]:
                        raise ValueError("Incorrect time given! Please format the time as HH:MM:SS or HH:MM, like 23:59:59")
                    if date.count("-") != 2:
                        raise ValueError("Incorrect date given! Please format the date as YYYY-MM-DD, like 2023-12-31")
                else:
                    if reminder_datetime.count("-") != 2:
                        raise ValueError("Incorrect date given! Please format the date as YYYY-MM-DD, like 2023-12-31")
                try:
                    if "t" not in reminder_datetime:
                        mode = 2
                    elif "-" in time or "+" in time:
                        if time.count(":") == 2:
                            mode = 0
                        else:
                            mode = 3
                    else:
                        # mode = 1
                        raise ValueError("Because I don't know your timezone, I can't ensure it'll be sent at the right time. Please add the timezone like so '-0100' or '+0900'.")
                    timestamp = datetime.strptime(reminder_datetime, 
                        ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m-%dt%H:%M%z"][mode]
                    )
                except ValueError:
                    raise ValueError("Incorrect format given! Make sure you only fill in only numbers")
                if mode == 0:
                    distance = timestamp
                if mode == 2:
                    options = {
                        "1":(timestamp-timedelta(hours=12)),
                        "2":(timestamp-timedelta(hours=6)),
                        "3":(timestamp),
                        "4":(timestamp+timedelta(hours=6)),
                        "5":(timestamp+timedelta(hours=12)),
                        "6":(timestamp+timedelta(hours=18)),
                        "7":(timestamp+timedelta(hours=24)),
                    }
                    query = f"Since I don't know what timezone you have, you can choose what time of day you want the reminder:"
                    for option in options:
                        query += f"\n  `{option}.` <t:{int(mktime(options[option].timetuple()))}:F>"
                    view = TimeOfDaySelection(list(options))
                    await itx.response.send_message(query, view = view, ephemeral=True)
                    await view.wait()
                    if view.value is None:
                        await itx.edit_original_response(content="Reminder creation menu timed out.", view=None)
                        return
                    distance = options[view.value]
                    itx = view.return_interaction
                
                # mode 0 is the datetime with timezone
                # mode 2 is the date, without time or timezone
                # mode 1 is time without timezone, which gets blocked: Without timezone, I don't know what time you want it

            except ValueError as ex:
                await itx.response.send_message(
                    f"Couldn't make new reminder:\n> {str(ex)}\n\n"
                    "You can make a reminder for days in advance, like so: \"4d12h\" or \"4day 12hours\" or \"in 3 minutes and 2 seconds\"\n" 
                    "You can also use ISO8601 format, like '2023-12-31T23:59+0100', or just '2023-12-31'\n"
                    "\n"
                    "If you give a time but not a timezone, I don't want you to get reminded at the wrong time, so I'll say something went wrong.",
                    ephemeral=True)
                return

        # if distance < now:
        #     itx.response.send_message("")
        # #todo

        self.Reminder(self.client, now, distance, itx.user.id, reminder, db_data)
        # await itx.user.send(f"On <t:{now}:f> (in <t:{int(mktime(distance.timetuple()))}:R>), you asked to be reminded of \"{reminder}.\"")
        # distance = distance+(datetime.now()-datetime.utcnow())
        _distance = int(mktime(distance.timetuple()))
        cmd_mention = self.client.get_command_mention("reminder reminders")
        await itx.response.send_message(f"Sucessfully created a reminder for you on <t:{_distance}:F> for \"{reminder}\"!\nUse {cmd_mention} to see your list of reminders",ephemeral=True)

    @app_commands.command(name="reminders",description="Check your list of reminders!")
    @app_commands.describe(item="Which reminder would you like to know more about? (use reminder-ID)")
    async def reminders(self, itx: discord.Interaction, item: int = None):
        collection = RinaDB["reminders"]
        query = {"userID": itx.user.id}
        db_data = collection.find_one(query)
        if db_data is None:
            cmd_mention = self.client.get_command_mention("reminder remindme")
            await itx.response.send_message(f"You don't have any reminders running at the moment!\nUse {cmd_mention} to make a reminder!", ephemeral=True)
            return

        try:
            out = []
            index = 0
            if item is None:
                for reminder in db_data['reminders']:
                    out.append(f"ID: `{index}` | Created at: <t:{reminder['remindertime']}:F> | Remind you about: {discord.utils.escape_markdown(reminder['reminder'])}")
                    index += 1
                outMsg = "Your reminders:\n"+'\n'.join(out)
                if len(outMsg) >= 1995:
                    out = []
                    index = 0
                    for reminder in db_data['reminders']:
                        out.append(f"`{index}` | <t:{reminder['remindertime']}:F>")
                        index += 1
                    cmd_mention = self.client.get_command_mention("reminder reminders")
                    outMsg = f"You have {len(db_data['reminders'])} reminders (use {cmd_mention} `item: ` to get more info about a reminder):\n"+'\n'.join(out)[:1996]
                await itx.response.send_message(outMsg,ephemeral=True)
            else:
                reminder = db_data['reminders'][item]
                await itx.response.send_message(f"Showing reminder `{index}` out of `{len(db_data['reminders'])}`:\n" +
                                                f"  ID: `{index}`\n" +
                                                f"  Created at:             <t:{reminder['creationtime']}:F> (<t:{reminder['creationtime']}>)\n" +
                                                f"  Reminding you at: <t:{reminder['remindertime']}:F> (<t:{reminder['remindertime']}:R>)\n" +
                                                f"  Remind you about: {discord.utils.escape_markdown(reminder['reminder'])}",ephemeral=True)
        except IndexError:
            cmd_mention = self.client.get_command_mention("reminder reminders")
            await itx.response.send_message(f"I couldn't find any reminder with that ID!\nLook for the \"ID: `0`\" at the beginning of your reminder on the reminder list ({cmd_mention})",ephemeral=True)
            return
        except KeyError:
            cmd_mention = self.client.get_command_mention("reminder remindme")
            await itx.response.send_message(f"You don't have any reminders running at the moment.\nUse {cmd_mention} to make a reminder!",ephemeral=True)
            return

    @app_commands.command(name="remove",description="Remove of your reminders")
    @app_commands.describe(item="Which reminder would you like to know more about? (use reminder-ID)")
    async def remove(self, itx: discord.Interaction, item: int):
        collection = RinaDB["reminders"]
        query = {"userID": itx.user.id}
        db_data = collection.find_one(query)
        if db_data is None:
            cmd_mention = self.client.get_command_mention("reminder remindme")
            await itx.response.send_message(f"You don't have any reminders running at the moment! (so I can't remove any either..)\nUse {cmd_mention} to make a reminder!", ephemeral=True)
            return

        try:
            del db_data['reminders'][item]
        except IndexError:
            cmd_mention = self.client.get_command_mention("reminder reminders")
            await itx.response.send_message(f"I couldn't find any reminder with that ID!\nLook for the \"ID: `0`\" at the beginning of your reminder on the reminder list ({cmd_mention})",ephemeral=True)
            return
        except KeyError:
            cmd_mention = self.client.get_command_mention("reminder remindme")
            await itx.response.send_message(f"You don't have any reminders running at the moment. (so I can't remove any either..)\nUse {cmd_mention} to make a reminder!",ephemeral=True)
            return
        query = {"userID": itx.user.id}
        if len(db_data['reminders']) > 0:
            collection.update_one(query, {"$set":{"reminders":db_data['reminders']}}, upsert=True)
        else:
            collection.delete_one(query)
        await itx.response.send_message(f"Successfully removed this reminder! You have {len(db_data['reminders'])} other reminders going.",ephemeral=True)

class BumpReminder(commands.Cog):
    def __init__(self, client: Bot):
        global RinaDB
        RinaDB = client.RinaDB
        self.client = client

    class Reminder:
        def __init__(self, client: Bot, guild: discord.Guild, remindertime):
            self.client = client
            self.guild = guild
            self.remindertime = remindertime - timedelta(seconds=1.5)
            sched.add_job(self.send_reminder, "date", run_date=self.remindertime)

        async def send_reminder(self):
            bump_channel_id, bump_role_id = await self.client.get_guild_info(self.guild, "bumpChannel", "bumpRole")
            bump_channel = await self.guild.fetch_channel(bump_channel_id)
            bump_role = self.guild.get_role(bump_role_id)

            await bump_channel.send(f"{bump_role.mention} The next bump is ready!", allowed_mentions=discord.AllowedMentions(roles=[bump_role]))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if len(message.embeds) > 0:
            if message.embeds[0].description is not None:
                if message.embeds[0].description.startswith("Bump done!"):
                    # collection = RinaDB["guildInfo"]
                    # query = {"guild_id": message.guild.id}
                    # guild_data = collection.find_one(query)
                    # bump_bot_id = guild_data["bumpBot"]
                    bump_bot_id = await self.client.get_guild_info(message.guild, "bumpBot")

                    if message.author.id == bump_bot_id:
                        remindertime = datetime.now() + timedelta(hours=2)
                        self.Reminder(self.client, message.guild, remindertime)


async def setup(client):
    await client.add_cog(Reminders(client))
    await client.add_cog(BumpReminder(client))

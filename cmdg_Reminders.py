from Uncute_Rina import *

sched = AsyncIOScheduler()
sched.start()


def parse_date(time_string, now):
    # - "next thursday at 3pm"
    # - "tomorrow"
    # - "in 3 days"
    # - "2d"
    # - "2022-07-03"
    # - "2022y4mo3days"
    # - "<t:293847839273>"
    numbers = ["0","1","2","3","4","5","6","7","8","9","."]
    timedict = {
        "y":["y","year","years"],
        "M":["mo","month","months"],
        "w":["w","week","weeks"],
        "d":["d","day","days"],
        "h":["h","hour","hours"],
        "m":["m","min","mins","minute","minutes"],
        "s":["s","sec","second","seconds"]
    }

    time_units = []
    low_index = 0
    number_index = 0
    is_number = True
    def magic_date_split(index, low_index, number_index):
        try:
            time = [int(time_string[low_index:number_index + 1])]
        except ValueError:
            raise ValueError(f"The value for your date/time has to be a number (0, 1, 2) not '{time_string[low_index:number_index + 1]}'")
        date = time_string[number_index + 1:index]
        # print(time,date)
        # print("          [",temp,"|",time,"]")
        for unit in timedict:
            # print(unit)
            if date in timedict[unit]:
                time.append(unit)
                break
        else:
            raise ValueError(f"You can't use '{date}' as unit for your date/time")
        return time
    index = 0 #for making my IDE happy
    for index in range(len(time_string)):
        if time_string[index] in numbers:
            if not is_number:
                time_units.append(magic_date_split(index, low_index, number_index))
                low_index = index
            number_index = index
            is_number = True
        else:
            is_number = False
    # temp = [timeString[low_index:number_index+1]]
    # time = timeString[number_index+1:index+1]
    # # print("          [",temp,"|",time,"]")
    # for unit in timedict:
    #     if time in timedict[unit]:
    #         temp.append(unit)
    #         break
    time_units.append(magic_date_split(index + 1, low_index, number_index))

    _timedict = {
        "y":now.year,
        "M":now.month,
        "d":now.day-1,
        "h":now.hour,
        "m":now.minute,
        "s":now.second,
        # now.day-1 for _timedict["d"] because later, datetime(day=...) starts with 1, and adds this value with
        # timedelta. This is required cause the datetime() doesn't let you set "0" for days. (cuz a month starts
        # at day 1)
    }
    for unit in time_units:
        if unit[1] == "w":
            _timedict["d"] += 7
        else:
            _timedict[unit[1]] += unit[0]
    while _timedict["s"] >= 60:
        _timedict["s"] -= 60
        _timedict["m"] += 1
    while _timedict["m"] >= 60:
        _timedict["m"] -= 60
        _timedict["h"] += 1
    while _timedict["h"] >= 24:
        _timedict["h"] -= 24
        _timedict["d"] += 1
    while _timedict["M"] > 12:
        _timedict["M"] -= 12
        _timedict["y"] += 1
    if _timedict["y"] >= 3999 or _timedict["d"] >= 1500000:
        raise ValueError("I don't think I can remind you in that long!")
    distance = datetime(_timedict["y"],_timedict["M"],1,_timedict["h"],_timedict["m"],_timedict["s"], tzinfo=datetime.now().tzinfo)
    # cause you cant have >31 days in a month, but if overflow is given, then let this timedelta calculate the new months/years
    distance += timedelta(days=_timedict["d"])

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
                    sched.add_job(self.send_reminder, "date", run_date=datetime.now())
                    return
                sched.add_job(self.send_reminder, "date", run_date=self.remindertime)
            else:
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
            await user.send(f"{self.alert}On <t:{creationtime}:F>, you asked to be reminded of \"{self.reminder}.\"")
            collection = RinaDB["reminders"]
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
    @app_commands.describe(time="When would you like me to remind you? (1d2h, 5 weeks, 1mo10d)",
                           reminder="What would you like me to remind you of")
    async def remindme(self, itx: discord.Interaction, time: str, reminder: str):
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
                await itx.response.send_message("please don't make more than 50 reminders. # todo, there is no way to erase reminders or see your current reminders",ephemeral=True)
                return
        except KeyError:
            pass

        now = datetime.now()
        try:
            time = (" "+time).replace(",","").replace("and","").replace(" in ", "").replace(" ","").strip().lower()
            distance = parse_date(time, now)
        except ValueError as ex:
            await itx.response.send_message(f"Couldn't make new reminder:\n  {str(ex)}\nFor now, you can only use a format like \"3mo5d\",\"2 hours, 3 mins\", \"3day4hour\", or \"4d 1m\"",ephemeral=True)
            return
        # if distance < now:
        #     itx.response.send_message("")
        # #todo

        self.Reminder(self.client, now, distance, itx.user.id, reminder, db_data)
        # await itx.user.send(f"On <t:{now}:f> (in <t:{int(mktime(distance.timetuple()))}:R>), you asked to be reminded of \"{reminder}.\"")
        # distance = distance+(datetime.now()-datetime.utcnow())
        _distance = int(mktime(distance.timetuple()))
        cmd_mention = self.client.getCommandMention("reminder reminders")
        await itx.response.send_message(f"Sucessfully created a reminder for you on <t:{_distance}:F> for \"{reminder}\"!\nUse {cmd_mention} to see your list of reminders",ephemeral=True)

    @app_commands.command(name="reminders",description="Check your list of reminders!")
    @app_commands.describe(item="Which reminder would you like to know more about? (use reminder-ID)")
    async def reminders(self, itx: discord.Interaction, item: int = None):
        collection = RinaDB["reminders"]
        query = {"userID": itx.user.id}
        db_data = collection.find_one(query)
        if db_data is None:
            cmd_mention = self.client.getCommandMention("reminder remindme")
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
                    outMsg = f"You have {len(db_data['reminders'])} reminders (use /reminder reminders item:[] to get more info about a reminder):\n"+'\n'.join(out)[:1996]
                await itx.response.send_message(outMsg,ephemeral=True)
            else:
                reminder = db_data['reminders'][item]
                await itx.response.send_message(f"Showing reminder `{index}` out of `{len(db_data['reminders'])}`:\n" +
                                                f"  ID: `{index}`\n" +
                                                f"  Created at:       <t:{reminder['creationtime']}:F> (<t:{reminder['creationtime']}>)\n" +
                                                f"  Reminding you at: <t:{reminder['remindertime']}:F> (<t:{reminder['remindertime']}:R>)\n" +
                                                f"  Remind you about: {discord.utils.escape_markdown(reminder['reminder'])}",ephemeral=True)
        except IndexError:
            cmd_mention = self.client.getCommandMention("reminder reminders")
            await itx.response.send_message(f"I couldn't find any reminder with that ID!\nLook for the \"ID: `0`\" at the beginning of your reminder on the reminder list ({cmd_mention})",ephemeral=True)
            return
        except KeyError:
            cmd_mention = self.client.getCommandMention("reminder remindme")
            await itx.response.send_message(f"You don't have any reminders running at the moment.\nUse {cmd_mention} to make a reminder!",ephemeral=True)
            return

    @app_commands.command(name="remove",description="Remove of your reminders")
    @app_commands.describe(item="Which reminder would you like to know more about? (use reminder-ID)")
    async def remove(self, itx: discord.Interaction, item: int):
        collection = RinaDB["reminders"]
        query = {"userID": itx.user.id}
        db_data = collection.find_one(query)
        if db_data is None:
            cmd_mention = self.client.getCommandMention("reminder remindme")
            await itx.response.send_message(f"You don't have any reminders running at the moment! (so I can't remove any either..)\nUse {cmd_mention} to make a reminder!", ephemeral=True)
            return

        try:
            del db_data['reminders'][item]
        except IndexError:
            cmd_mention = self.client.getCommandMention("reminder reminders")
            await itx.response.send_message(f"I couldn't find any reminder with that ID!\nLook for the \"ID: `0`\" at the beginning of your reminder on the reminder list ({cmd_mention})",ephemeral=True)
            return
        except KeyError:
            cmd_mention = self.client.getCommandMention("reminder remindme")
            await itx.response.send_message(f"You don't have any reminders running at the moment. (so I can't remove any either..)\nUse {cmd_mention} to make a reminder!",ephemeral=True)
            return
        query = {"userID": itx.user.id}
        if len(db_data['reminders']) > 0:
            collection.update_one(query, {"$set":{"reminders":db_data['reminders']}}, upsert=True)
        else:
            collection.delete_one(query)
        await itx.response.send_message("Successfully removed this reminder!",ephemeral=True)


async def setup(client):
    await client.add_cog(Reminders(client))

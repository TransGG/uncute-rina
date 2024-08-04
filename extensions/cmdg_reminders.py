import discord, discord.ext.commands as commands, discord.app_commands as app_commands
from time import mktime # for reminder times
from datetime import datetime, timedelta
from resources.customs.bot import Bot
from resources.customs.reminders import ReminderObject, BumpReminderObject
from resources.utils.utils import parse_date
from resources.views.reminders import TimeOfDaySelection


class RemindersCog(commands.GroupCog,name="reminder"):
    def __init__(self, client: Bot):
        self.client = client

    @app_commands.command(name="remindme",description="Add a reminder for yourself!")
    @app_commands.describe(reminder_datetime="When would you like me to remind you? (1d2h, 5 weeks, 1mo10d)",
                           reminder="What would you like me to remind you of")
    @app_commands.rename(reminder_datetime='time')
    async def remindme(self, itx: discord.Interaction, reminder_datetime: str, reminder: str):
        if len(reminder) > 1500:
            await itx.response.send_message("Please keep reminder text below 1500 characters... Otherwise I can't send you a message about it!",ephemeral=True)
            return
        collection = self.client.RinaDB["reminders"]
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
                if mode in [0,3]:
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

                # mode 0 is the date with time up to seconds and timezone
                # mode 2 is the date, without time or timezone
                # mode 3 is the date with time up to minutes and timezone
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

        ReminderObject(self.client, now, distance, itx.user.id, reminder, db_data)
        # await itx.user.send(f"On <t:{now}:f> (in <t:{int(mktime(distance.timetuple()))}:R>), you asked to be reminded of \"{reminder}.\"")
        # distance = distance+(datetime.now()-datetime.utcnow())
        _distance = int(mktime(distance.timetuple()))
        cmd_mention = self.client.get_command_mention("reminder reminders")
        await itx.response.send_message(f"Sucessfully created a reminder for you on <t:{_distance}:F> for \"{reminder}\"!\nUse {cmd_mention} to see your list of reminders",ephemeral=True)

    @app_commands.command(name="reminders",description="Check your list of reminders!")
    @app_commands.describe(item="Which reminder would you like to know more about? (use reminder-ID)")
    async def reminders(self, itx: discord.Interaction, item: int = None):
        collection = self.client.RinaDB["reminders"]
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
        collection = self.client.RinaDB["reminders"]
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
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if len(message.embeds) > 0:
            if message.embeds[0].description is not None:
                if message.embeds[0].description.startswith("Bump done!"):
                    # collection = self.client.RinaDB["guildInfo"]
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

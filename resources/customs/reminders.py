import asyncio # to create new reminder task that runs immediately (from a not-async ReminderObject __init__ function)
from datetime import datetime, timedelta
from resources.customs.bot import Bot
from time import mktime
import discord


class ReminderObject:
    def __init__(self, client: Bot,
                 creationtime: datetime,
                 remindertime: datetime,
                 user_id: int,
                 reminder: str,
                 db_data,
                 continued: bool = False):
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
                self.alert = "Your reminder was delayed. Probably because the bot was offline for a while. I hope it didn't cause much of an issue!\n"
                try:
                    asyncio.get_event_loop().create_task(self.send_reminder())
                except RuntimeError:
                    pass
                return
            client.sched.add_job(self.send_reminder, "date", run_date=self.remindertime)
        else:
            if self.remindertime < datetime.now():
                self.alert = "Your reminder date/time has passed already. Perhaps the bot was offline for a while; perhaps you just filled in a time in the past!\n"
                try:
                    asyncio.get_event_loop().create_task(self.send_reminder())
                except RuntimeError:
                    pass
                return
            collection = self.client.rina_db["reminders"]
            reminder_data = {
                "creationtime":int(mktime(creationtime.timetuple())),
                "remindertime":int(mktime(remindertime.timetuple())),
                "reminder":reminder,
            }
            try:
                user_reminders = db_data['reminders']
            except KeyError:
                user_reminders = []
            user_reminders.append(reminder_data)
            query = {"userID": user_id}
            collection.update_one(query, {"$set":{"reminders":user_reminders}}, upsert=True)
            # print(f"added job for {self.remindertime} and it's currently {self.creationtime}")
            client.sched.add_job(self.send_reminder, "date", run_date=self.remindertime)

    async def send_reminder(self):
        user = await self.client.fetch_user(self.userID)
        creationtime = int(mktime(self.creationtime.timetuple()))
        try:
            await user.send(f"{self.alert}On <t:{creationtime}:F>, you asked to be reminded of \"{self.reminder}\".")
        except discord.errors.Forbidden:
            pass # I guess this user has no servers in common with Rina anymore. Sucks for them.
        collection = self.client.rina_db["reminders"]
        query = {"userID": self.userID}
        db_data = collection.find_one(query)
        index_subtraction = 0
        for reminderIndex in range(len(db_data['reminders'])):
            if db_data['reminders'][reminderIndex-index_subtraction]["remindertime"] <= int(mktime(datetime.now().timetuple())):
                del db_data['reminders'][reminderIndex-index_subtraction]
                index_subtraction += 1
        if len(db_data['reminders']) > 0:
            collection.update_one(query, {"$set":{"reminders":db_data['reminders']}}, upsert=True)
        else:
            collection.delete_one(query)

class BumpReminderObject:
    def __init__(self, client: Bot, guild: discord.Guild, remindertime):
        self.client = client
        self.guild = guild
        self.remindertime = remindertime - timedelta(seconds=1.5)
        client.sched.add_job(self.send_reminder, "date", run_date=self.remindertime)

    async def send_reminder(self):
        bump_channel_id, bump_role_id = await self.client.get_guild_info(self.guild, "bumpChannel", "bumpRole")
        bump_channel = await self.guild.fetch_channel(bump_channel_id)
        bump_role = self.guild.get_role(bump_role_id)

        await bump_channel.send(f"{bump_role.mention} The next bump is ready!", allowed_mentions=discord.AllowedMentions(roles=[bump_role]))

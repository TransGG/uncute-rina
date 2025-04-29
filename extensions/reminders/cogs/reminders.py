import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.reminders.objects import parse_and_create_reminder


class RemindersCog(commands.GroupCog, name="reminder"):
    def __init__(self):
        pass

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
        await parse_and_create_reminder(itx, reminder_datetime, reminder)

    @app_commands.command(name="reminders", description="Check your list of reminders!")
    @app_commands.describe(item="Which reminder would you like to know more about? (use reminder-ID)")
    async def reminders(self, itx: discord.Interaction, item: int = None):
        collection = itx.client.rina_db["reminders"]
        query = {"userID": itx.user.id}
        db_data = collection.find_one(query)
        if db_data is None:
            cmd_mention = itx.client.get_command_mention("reminder remindme")
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
                    cmd_mention = itx.client.get_command_mention("reminder reminders")
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
            cmd_mention = itx.client.get_command_mention("reminder reminders")
            await itx.response.send_message(
                f"I couldn't find any reminder with that ID!\n"
                f"Look for the \"ID: `0`\" at the beginning of your reminder on the reminder list ({cmd_mention})",
                ephemeral=True)
            return
        except KeyError:
            cmd_mention = itx.client.get_command_mention("reminder remindme")
            await itx.response.send_message(
                f"You don't have any reminders running at the moment.\nUse {cmd_mention} to make a reminder!",
                ephemeral=True)
            return

    @app_commands.command(name="remove", description="Remove of your reminders")
    @app_commands.describe(item="Which reminder would you like to know more about? (use reminder-ID)")
    async def remove(self, itx: discord.Interaction, item: int):
        collection = itx.client.rina_db["reminders"]
        query = {"userID": itx.user.id}
        db_data = collection.find_one(query)
        if db_data is None:
            cmd_mention = itx.client.get_command_mention("reminder remindme")
            await itx.response.send_message(
                f"You don't have any reminders running at the moment! (so I can't remove any either..)\n"
                f"Use {cmd_mention} to make a reminder!",
                ephemeral=True)
            return

        try:
            del db_data['reminders'][item]
        except IndexError:
            cmd_mention = itx.client.get_command_mention("reminder reminders")
            await itx.response.send_message(
                f"I couldn't find any reminder with that ID!\n"
                f"Look for the \"ID: `0`\" at the beginning of your reminder on the reminder list ({cmd_mention})",
                ephemeral=True)
            return
        except KeyError:
            cmd_mention = itx.client.get_command_mention("reminder remindme")
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

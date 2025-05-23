import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.reminders.exceptions import UnixTimestampInPastException, \
    MalformedISODateTimeException, TimestampParseException, \
    ReminderTimeSelectionMenuTimeOut
from extensions.reminders.objects import parse_and_create_reminder
from resources.customs import Bot
from resources.utils import MissingQuantityException, MissingUnitException


class RemindersCog(commands.GroupCog, name="reminder"):
    def __init__(self):
        pass

    @app_commands.command(name="remindme",
                          description="Add a reminder for yourself!")
    @app_commands.describe(
        reminder_datetime="When would you like me to remind you? "
                          "(1d2h, 5 weeks, 1mo10d)",
        reminder="What would you like me to remind you of?"
    )
    @app_commands.rename(reminder_datetime='time')
    async def remindme(
            self,
            itx: discord.Interaction[Bot],
            reminder_datetime: str,
            reminder: str
    ):
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
                "Please keep reminder text below 1500 characters... Otherwise "
                "I can't send you a message about it!",
                ephemeral=True)
            return

        cmd_help = itx.client.get_command_mention_with_args(
            "help", page="113")
        try:
            await parse_and_create_reminder(itx, reminder_datetime, reminder)
        except OverflowError as ex:
            await itx.response.send_message(str(ex), ephemeral=True)
        except UnixTimestampInPastException as ex:
            timestamp_unix = int(ex.distance.timestamp())
            await itx.response.send_message(
                "Couldn't make new reminder: \n"
                "> Your message was interpreted as a unix timestamp, but this "
                "timestamp would be before the current time!\n"
                f"Interpreted timestamp: {timestamp_unix} "
                f"(<t:{timestamp_unix}:F>, <t:{timestamp_unix}:R>).\n"
                # round up (+ 0.5) to ensure t=0.99 > t=0.80
                f"Current time: {int(ex.creation_time.timestamp() + 0.5)} "
                f"(<t:{int(ex.creation_time.timestamp() + 0.5)}:F>, "
                f"<t:{int(ex.creation_time.timestamp() + 0.5)}:R>).\n"
                f"For more info, use {cmd_help}.",
                ephemeral=True
            )
            return
        except MalformedISODateTimeException as ex:
            await itx.response.send_message(
                f"Couldn't make new reminder:\n> {str(ex.inner_exception)}\n"
                "You can only use a format like [number][letter], or "
                "yyyy-mm-ddThh:mm:ss+0000. Some examples:\n"
                '    "3mo 0.5d", "in 2 hours, 3.5 mins", '
                '"1 year and 3 seconds", "3day4hour", "4d1m", '
                '"2023-12-31T23:59+0100", "<t:12345678>\n'
                "Words like \"in\" and \"and\" are ignored, so you can use "
                "those for readability if you'd like.\n"
                '    year = y, year, years\n'
                '    month = mo, month, months\n'
                '    week = w, week, weeks\n'
                '    day = d, day, days\n'
                '    hour = h, hour, hours\n'
                '    minute = m, min, mins, minute, minutes\n'
                '    second = s, sec, secs, second, seconds\n'
                f'For more info, use {cmd_help}.',
                ephemeral=True)
            return
        except TimestampParseException as ex:
            await itx.response.send_message(
                f"Couldn't make new reminder:\n> {str(ex.inner_exception)}\n\n"
                "You can make a reminder for days in advance, like so: "
                "\"4d12h\", \"4day 12hours\" or \"in 3 minutes and "
                "2 seconds\"\n"
                "You can also use ISO8601 format, like "
                "'2023-12-31T23:59+0100', or just '2023-12-31'\n"
                "Or you can use Unix Epoch format: the amount of seconds "
                "since January 1970: '1735155750"
                "\n"
                "If you give a time but not a timezone, I don't want you to "
                "get reminded at the wrong time, "
                "so I'll say something went wrong.\n"
                f"For more info, use {cmd_help}.",
                ephemeral=True
            )
            return
        except MissingQuantityException as ex:
            await itx.response.send_message(
                f"Couldn't make new reminder:\n> {str(ex)}\n\n"
                f"Be sure you start the reminder time with a number "
                f"like \"4 days\".\n"
                f"For more info, use {cmd_help}.",
                ephemeral=True
            )
            return
        except MissingUnitException as ex:
            await itx.response.send_message(
                f"Couldn't make new reminder:\n> {str(ex)}\n\n"
                f"Be sure you end the reminder time with a unit like "
                f"\"4 days\".\n"
                f"If you intended to use a unix timestamp instead, make "
                f"sure your timestamp is correct. Any number below 1000000 "
                f"is parsed in the \"1 day 2 hours\" format, which means not "
                f"providing a unit will give this error. Note: a unix "
                f"timestamp of 1000000 is 20 Jan 1970 "
                f"(<t\\:1000000:D> = <t:1000000:D>)\n"
                f"For more info, use {cmd_help}.",
                ephemeral=True
            )
            return
        except ReminderTimeSelectionMenuTimeOut:
            return

    @app_commands.command(name="reminders",
                          description="Check your list of reminders!")
    @app_commands.describe(
        item="Which reminder would you like to know more about? "
             "(use reminder-ID)"
    )
    async def reminders(
            self,
            itx: discord.Interaction[Bot],
            item: int = None
    ):
        collection = itx.client.rina_db["reminders"]
        query = {"userID": itx.user.id}
        db_data = collection.find_one(query)
        if db_data is None:
            cmd_reminders = itx.client.get_command_mention("reminder remindme")
            await itx.response.send_message(
                f"You don't have any reminders running at the moment!\n"
                f"Use {cmd_reminders} to make a reminder!",
                ephemeral=True)
            return

        try:
            out = []
            index = 0
            if item is None:
                for reminder in db_data['reminders']:
                    reminder_text = discord.utils.escape_markdown(
                        reminder['reminder'])
                    out.append(
                        f"ID: `{index}` | Created at: "
                        f"<t:{reminder['remindertime']}:F> | "
                        f"Remind you about: {reminder_text}"
                    )
                    index += 1
                out_msg = "Your reminders:\n" + '\n'.join(out)
                if len(out_msg) >= 1995:
                    out = []
                    index = 0
                    for reminder in db_data['reminders']:
                        out.append(f"`{index}` | "
                                   f"<t:{reminder['remindertime']}:F>")
                        index += 1
                    cmd_reminders = itx.client.get_command_mention_with_args(
                        "reminder reminders", item=" ")
                    out_msg = (
                        (f"You have {len(db_data['reminders'])} reminders "
                         f"(use {cmd_reminders} to get more info about a "
                         f"reminder):\n")
                        + '\n'.join(out)[:1996]
                    )
                await itx.response.send_message(out_msg, ephemeral=True)
            else:
                reminder = db_data['reminders'][item]
                create_time_str = (f"<t:{reminder['creationtime']}:F> "
                                   f"(<t:{reminder['creationtime']}>)")
                remind_time_str = (f"<t:{reminder['remindertime']}:F> "
                                   f"(<t:{reminder['remindertime']}:R>)")
                text = discord.utils.escape_markdown(reminder['reminder'])
                await itx.response.send_message(
                    f"Showing reminder `{index}` out of "
                    f"`{len(db_data['reminders'])}`:\n"
                    f"  ID: `{index}`\n"
                    f"  Created at:             {create_time_str}\n"
                    f"  Reminding you at: {remind_time_str}\n"
                    f"  Remind you about: {text}",
                    ephemeral=True,
                )
                return
        except IndexError:
            cmd_reminders = itx.client.get_command_mention("reminder reminders")
            await itx.response.send_message(
                f"I couldn't find any reminder with that ID!\n"
                f"Look for the \"ID: `0`\" at the beginning of your reminder "
                f"on the reminder list ({cmd_reminders})",
                ephemeral=True,
            )
            return
        except KeyError:
            cmd_reminders = itx.client.get_command_mention("reminder remindme")
            await itx.response.send_message(
                f"You don't have any reminders running at the moment.\n"
                f"Use {cmd_reminders} to make a reminder!",
                ephemeral=True,
            )
            return

    @app_commands.command(name="remove",
                          description="Remove of your reminders")
    @app_commands.describe(
        item="Which reminder would you like to know more about? "
             "(use reminder-ID)"
    )
    async def remove(self, itx: discord.Interaction[Bot], item: int):
        collection = itx.client.rina_db["reminders"]
        query = {"userID": itx.user.id}
        db_data = collection.find_one(query)
        if db_data is None:
            cmd_remindme = itx.client.get_command_mention("reminder remindme")
            await itx.response.send_message(
                f"You don't have any reminders running at the moment! (so "
                f"I can't remove any either..)\n"
                f"Use {cmd_remindme} to make a reminder!",
                ephemeral=True)
            return

        try:
            del db_data['reminders'][item]
        except IndexError:
            cmd_remindme = itx.client.get_command_mention("reminder reminders")
            await itx.response.send_message(
                f"I couldn't find any reminder with that ID!\n"
                f"Look for the \"ID: `0`\" at the beginning of your reminder "
                f"on the reminder list ({cmd_remindme})",
                ephemeral=True)
            return
        except KeyError:
            cmd_remindme = itx.client.get_command_mention("reminder remindme")
            await itx.response.send_message(
                f"You don't have any reminders running at the moment. (so "
                f"I can't remove any either..)\n"
                f"Use {cmd_remindme} to make a reminder!",
                ephemeral=True)
            return
        query = {"userID": itx.user.id}
        if len(db_data['reminders']) > 0:
            collection.update_one(
                query,
                {"$set": {"reminders": db_data['reminders']}},
                upsert=True
            )
        else:
            collection.delete_one(query)
        await itx.response.send_message(
            f"Successfully removed this reminder! You have "
            f"{len(db_data['reminders'])} other reminders going.",
            ephemeral=True
        )

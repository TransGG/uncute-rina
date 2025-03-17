from __future__ import annotations
from typing import TYPE_CHECKING

import discord

from resources.views.generics import create_simple_button
from resources.customs.bot import Bot

from extensions.reminders.utils import get_user_reminders

if TYPE_CHECKING:
    from extensions.reminders.objects import ReminderObject


class CopyReminder(discord.ui.View):
    def __init__(self, client: Bot, create_reminder_callback, reminder: ReminderObject, timeout=300):
        super().__init__()
        self.timeout = timeout
        self.return_interaction: discord.Interaction | None = None
        self.reminder = reminder
        self.client = client

        # required to prevent circular imports ;-;
        # AI suggested this to me lol. It's probably the easiest way to fix it.
        self.create_reminder_callback = create_reminder_callback

        self.add_item(create_simple_button("I also want to be reminded!",
                                           discord.ButtonStyle.gray,
                                           self.button_callback))

    async def button_callback(self, itx: discord.Interaction):
        # Check if user has too many reminders (max 50 allowed (internally chosen limit))
        user_reminders = get_user_reminders(self.client, itx.user)
        if len(user_reminders) > 50:
            cmd_mention = self.client.get_command_mention("reminder reminders")
            cmd_mention1 = self.client.get_command_mention("reminder remove")
            await itx.response.send_message(f"You already have more than 50 reminders! Use {cmd_mention} to see "
                                            f"your reminders, and use {cmd_mention1} `item: ` to remove a reminder",
                                            ephemeral=True)
            return
        await self.create_reminder_callback(self.client, itx, self.reminder.remindertime, self.reminder.creationtime,
                                            self.reminder.reminder, user_reminders, True)

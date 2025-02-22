import discord
from resources.buttons.reminders import TimeOfDayButton, ShareReminderButton


class TimeOfDaySelection(discord.ui.View):
    def __init__(self, options, timeout=180):
        super().__init__()
        self.value: str | None = None
        self.return_interaction: discord.Interaction | None = None
        self.timeout = timeout

        for option in options:
            self.add_item(TimeOfDayButton(self, style=discord.ButtonStyle.green, label=option))


class ShareReminder(discord.ui.View):
    def __init__(self, timeout=300):
        super().__init__()
        self.timeout = timeout
        self.return_interaction: discord.Interaction | None = None
        self.add_item(ShareReminderButton(self, style=discord.ButtonStyle.gray, label="Share reminder in chat"))


class CopyReminder(discord.ui.View):
    def __init__(self, timeout=300):
        super().__init__()
        self.timeout = timeout
        self.return_interaction: discord.Interaction | None = None
        self.add_item(CopyReminderButton(self, style=discord.ButtonStyle.gray, label="Share reminder in chat"))

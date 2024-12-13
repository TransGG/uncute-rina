import discord
from resources.buttons.reminders import TimeOfDayButton


class TimeOfDaySelection(discord.ui.View):
    def __init__(self, options, timeout=180):
        super().__init__()
        self.value: str | None = None
        self.return_interaction: discord.Interaction | None = None
        self.timeout = timeout

        for option in options:
            self.add_item(TimeOfDayButton(self, style=discord.ButtonStyle.green, label=option))

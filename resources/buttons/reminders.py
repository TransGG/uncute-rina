import discord


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

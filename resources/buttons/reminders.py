from typing import Any

import discord
from discord import Interaction


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


class ShareReminderButton(discord.ui.Button):
    def __init__(self, view: discord.ui.View, label: str, **kwargs):
        self.value = None
        self._label = label
        self._view = view
        self.return_interaction = None
        super().__init__(label=label, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        self.value = 1
        self.return_interaction = interaction
        self._view.stop()


class CopyReminderButton(discord.ui.Button):
    def __init__(self, view: discord.ui.View, label: str, **kwargs):
        self.value = 0
        self._label = label
        self._view = view
        super().__init__(label=label, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        self.value += 1

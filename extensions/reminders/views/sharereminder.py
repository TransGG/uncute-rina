import discord

from resources.customs import Bot
from resources.views.generics import create_simple_button


class ShareReminder(discord.ui.View):
    timeout: float
    return_interaction: discord.Interaction[Bot] | None

    def __init__(self, timeout: float = 300) -> None:
        super().__init__()
        self.timeout = timeout
        self.return_interaction: discord.Interaction[Bot] | None = None
        self.add_item(create_simple_button(
            "Share reminder in chat",
            discord.ButtonStyle.gray,
            self.callback)
        )

    async def callback(self, interaction: discord.Interaction[Bot]) -> None:
        self.return_interaction = interaction
        self.stop()

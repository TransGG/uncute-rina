import discord

from resources.customs import Bot
from resources.views.generics import create_simple_button


class ShareReminder(discord.ui.View):
    timeout: int|float
    return_interaction: discord.Interaction[Bot] | None

    # This can be entirely synthesized from the value of return_interaction, given that the API guarantees that the given interaction is not None
    @property
    def value(self) -> int:
        return int(self.return_interaction is not None)

    def __init__(self, timeout:float=300):
        super().__init__()
        self.timeout = timeout
        self.return_interaction: discord.Interaction[Bot] | None = None
        self.add_item(create_simple_button(
            "Share reminder in chat",
            discord.ButtonStyle.gray,
            self.callback)
        )

    async def callback(self, interaction: discord.Interaction[Bot]):
        self.return_interaction = interaction
        self.stop()

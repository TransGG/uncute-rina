import discord

from resources.views.generics import create_simple_button


class ShareReminder(discord.ui.View):
    def __init__(self, timeout=300):
        super().__init__()
        self.value = 0
        self.timeout = timeout
        self.return_interaction: discord.Interaction | None = None
        self.add_item(create_simple_button("Share reminder in chat", discord.ButtonStyle.gray, self.callback))

    async def callback(self, interaction: discord.Interaction):
        self.value = 1
        self.return_interaction = interaction
        self.stop()

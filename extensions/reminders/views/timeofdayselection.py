import discord

from resources.views.generics import create_simple_button


class TimeOfDaySelection(discord.ui.View):
    def __init__(self, options: list[str], timeout=180):
        super().__init__()
        self.value: str | None = None
        self.return_interaction: discord.Interaction | None = None
        self.timeout = timeout

        for option in options:
            def callback(itx):  # pass the button label to the callback
                return self.callback(itx, option)

            self.add_item(create_simple_button(option, discord.ButtonStyle.green, callback))

    async def callback(self, interaction: discord.Interaction, label: str):
        self.value = label
        self.return_interaction = interaction
        self.stop()

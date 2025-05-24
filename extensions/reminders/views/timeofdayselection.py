import discord

from resources.views.generics import create_simple_button
from resources.customs import Bot


class TimeOfDaySelection(discord.ui.View):
    def __init__(self, options: list[str], timeout=180):
        super().__init__()
        self.value: str | None = None
        self.return_interaction: discord.Interaction[Bot] | None = None
        self.timeout = timeout

        for option in options:
            def callback(itx, label=option):
                """Helper to pass the button label to the callback"""
                # Needs label= to create a copy of the `option` value,
                #  otherwise the parameter is overwritten. (always
                #  returns 7).
                return self.callback(itx, label)

            button = create_simple_button(
                label=option,
                style=discord.ButtonStyle.green,
                callback=callback,
            )
            self.add_item(button)

    async def callback(
            self,
            interaction: discord.Interaction[Bot],
            label: str,
    ):
        self.value = label
        self.return_interaction = interaction
        self.stop()

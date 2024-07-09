import discord


class ConfirmationView_VcTable_AutorizedMode(discord.ui.View):
    def __init__(self, timeout=None):
        super().__init__()
        self.value = None
        self.timeout = timeout

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, _itx: discord.Interaction, _button: discord.ui.Button):
        self.value = 1
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel(self, _itx: discord.Interaction, _button: discord.ui.Button):
        self.value = 0
        self.stop()

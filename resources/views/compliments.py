import discord

class ConfirmPronounsView(discord.ui.View):
    def __init__(self, timeout=None):
        super().__init__()
        self.value = None
        self.timeout = timeout

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='She/Her', style=discord.ButtonStyle.green)
    async def feminine(self, itx: discord.Interaction, _button: discord.ui.Button):
        self.value = "she/her"
        await itx.response.edit_message(content='Selected She/Her pronouns for compliment', view=None)
        self.stop()

    @discord.ui.button(label='He/Him', style=discord.ButtonStyle.green)
    async def masculine(self, itx: discord.Interaction, _button: discord.ui.Button):
        self.value = "he/him"
        await itx.response.edit_message(content='Selected He/Him pronouns for the compliment', view=None)
        self.stop()

    @discord.ui.button(label='They/Them', style=discord.ButtonStyle.green)
    async def enby_them(self, itx: discord.Interaction, _button: discord.ui.Button):
        self.value = "they/them"
        await itx.response.edit_message(content='Selected They/Them pronouns for the compliment', view=None)
        self.stop()

    @discord.ui.button(label='It/Its', style=discord.ButtonStyle.green)
    async def enby_its(self, itx: discord.Interaction, _button: discord.ui.Button):
        self.value = "it/its"
        await itx.response.edit_message(content='Selected It/Its pronouns for the compliment', view=None)
        self.stop()

    @discord.ui.button(label='Unisex/Unknown', style=discord.ButtonStyle.grey)
    async def unisex(self, itx: discord.Interaction, _button: discord.ui.Button):
        self.value = "unisex"
        await itx.response.edit_message(content='Selected Unisex/Unknown gender for the compliment', view=None)
        self.stop()

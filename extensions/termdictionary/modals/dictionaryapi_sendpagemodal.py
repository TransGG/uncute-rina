import discord


class DictionaryAPISendPageModal(discord.ui.Modal, title="Share single dictionary entry?"):
    def __init__(self, entries, timeout=None):
        super().__init__()
        self.value = None
        self.timeout = timeout
        self.entries = entries
        self.id = None
        self.question_text = discord.ui.TextInput(label='Entry index',
                                                  placeholder=f"[A number from 0 to {len(entries) - 1} ]",
                                                  # style=discord.TextStyle.short,
                                                  # required=True
                                                  )
        self.add_item(self.question_text)

    async def on_submit(self, itx: discord.Interaction):
        self.value = 9  # failed; placeholder
        try:
            self.id = int(self.question_text.value)
        except ValueError:
            await itx.response.send_message(
                content=f"Couldn't send entry: '{self.question_text.value}' is not an integer. "
                        "It has to be an index number from an entry in the /dictionary response.",
                ephemeral=True)
            return
        if self.id < 0 or self.id >= len(self.entries):
            await itx.response.send_message(
                content=f"Couldn't send intry: '{self.id}' is not a possible index value for your dictionary entry. "
                        "It has to be an index number from an entry in the /dictionary response.",
                ephemeral=True)
            return
        self.value = 1  # succeeded
        await itx.response.send_message("Sending item...", ephemeral=True, delete_after=8)
        self.stop()

import discord


class SingleLineModal(discord.ui.Modal):
    def __init__(self, title: str, label: str, placeholder: str = ""):
        super().__init__(title=title)
        self.question_text = discord.ui.TextInput(label=label,
                                                  placeholder=placeholder,
                                                  # style=discord.TextStyle.short, required=True
                                                  )
        self.add_item(self.question_text)
        self.itx = None

    async def on_submit(self, itx: discord.Interaction) -> None:
        self.itx = itx
        self.stop()
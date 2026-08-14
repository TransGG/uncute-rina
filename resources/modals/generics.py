import discord

from resources.customs import Bot


class SingleLineModal(discord.ui.Modal):
    def __init__(self, title: str, label: str, placeholder: str = "") -> None:
        super().__init__(title=title)
        self.question_text: discord.ui.TextInput = discord.ui.TextInput(
            label=label,
            placeholder=placeholder,
            # style=discord.TextStyle.short, required=True
        )
        self.add_item(self.question_text)
        self.itx: discord.Interaction[Bot] | None = None

    async def on_submit(
            self,
            itx: discord.Interaction[Bot]  # type: ignore
            # (Interaction vs. Interaction[Bot])
    ) -> None:
        self.itx = itx
        self.stop()

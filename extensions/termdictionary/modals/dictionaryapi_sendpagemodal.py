import discord

from resources.customs import Bot


class DictionaryAPISendPageModal(discord.ui.Modal, title="Share single dictionary entry?"):
    def __init__(self, max_page, timeout=None):
        super().__init__()
        self.succeeded: bool = False
        self.timeout = timeout
        self.max_page = max_page
        self.line: int | None = None
        self.question_text = discord.ui.TextInput(label='Entry index',
                                                  placeholder=f"[A number from 0 to {max_page} ]",
                                                  # style=discord.TextStyle.short,
                                                  # required=True
                                                  )
        self.add_item(self.question_text)

    async def on_submit(self, itx: discord.Interaction[Bot]):
        try:
            self.line = int(self.question_text.value)
        except ValueError:
            await itx.response.send_message(
                content=f"Couldn't send entry: '{self.question_text.value}' "
                        f"is not an integer. It has to be an index number "
                        f"from an entry in the /dictionary response.",
                ephemeral=True
            )
            return
        if self.line < 0 or self.line > self.max_page:
            await itx.response.send_message(
                content=f"Couldn't send intry: '{self.id}' is not a possible "
                        f"index value for your dictionary entry. It has to "
                        f"be an index number from an entry in the /dictionary "
                        f"response.",
                ephemeral=True
            )
            return
        self.succeeded = True
        await itx.response.send_message("Sending item...", ephemeral=True, delete_after=8)
        self.stop()

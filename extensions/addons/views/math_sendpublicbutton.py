import discord


class SendPublicButtonMath(discord.ui.View):
    def __init__(self, timeout=180):
        super().__init__()
        self.value = None
        self.timeout = timeout

    @discord.ui.button(label='Send Publicly', style=discord.ButtonStyle.gray)
    async def send_publicly(self, itx: discord.Interaction, _button: discord.ui.Button):
        self.value = 1
        await itx.response.edit_message(content="Sent successfully!")
        cmd_mention = itx.client.get_command_mention("math")
        await itx.followup.send(f"**{itx.user.mention} shared a {cmd_mention} output:**\n" + itx.message.content,
                                ephemeral=False, allowed_mentions=discord.AllowedMentions.none())

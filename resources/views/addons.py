from __future__ import annotations
from discord.ui import (
    View as dView, 
    Button as dButton, 
    button as dbutton
)
from discord import (
    Interaction, 
    ButtonStyle as dButtonStyle, 
    AllowedMentions as dAllowedMentions
)
from resources.customs.bot import Bot


class EqualDex_AdditionalInfo(dView):
    def __init__(self, url):
        super().__init__()
        link_button = dButton(style = dButtonStyle.gray,
                              label = "More info",
                              url = url)
        self.add_item(link_button)

class SendPublicButton_Math(dView):
    def __init__(self, client: Bot, timeout=180):
        super().__init__()
        self.value = None
        self.client = client
        self.timeout = timeout

    @dbutton(label='Send Publicly', style=dButtonStyle.gray)
    async def send_publicly(self, itx: Interaction, _button: dButton):
        self.value = 1
        await itx.response.edit_message(content="Sent successfully!")
        cmd_mention = self.client.get_command_mention("math")
        await itx.followup.send(f"**{itx.user.mention} shared a {cmd_mention} output:**\n" + itx.message.content, ephemeral=False, allowed_mentions=dAllowedMentions.none())

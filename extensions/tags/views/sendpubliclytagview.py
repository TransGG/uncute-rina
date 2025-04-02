import discord

from resources.utils.utils import log_to_guild
from resources.customs import Bot
from extensions.settings.objects import AttributeKeys


class SendPubliclyTagView(discord.ui.View):
    def __init__(
            self,
            embed: discord.Embed,
            timeout=None,
            public_footer=None,
            log_msg=None,
            tag_name=None
    ):
        super().__init__()
        if embed.footer.text is None:
            self.footer = ""
        else:
            self.footer = embed.footer.text + "\n"

        self.value = None
        self.timeout = timeout
        self.public_footer = public_footer
        self.embed = embed
        self.log_msg = log_msg
        self.tag_name = tag_name

    @discord.ui.button(label='Send publicly', style=discord.ButtonStyle.primary)
    async def send_publicly(self, itx: discord.Interaction[Bot], _button: discord.ui.Button):
        self.value = 1
        if self.public_footer is None:
            self.public_footer = f"Triggered by {itx.user.name} ({itx.user.id})"
        else:
            self.public_footer = "Note: If you believe that this command was misused or abused, " + \
                                 "please do not argue in this channel. Instead, open a mod ticket " + \
                                 "and explain the situation there. Thank you."
            self.value = 2
        self.embed.set_footer(text=self.footer + self.public_footer)
        await itx.response.edit_message(content="Sent successfully!", embed=None, view=None)
        try:
            # try sending the message without replying to the previous ephemeral
            msg = await itx.channel.send("", embed=self.embed, allowed_mentions=discord.AllowedMentions.none())
        except discord.Forbidden:
            msg = await itx.followup.send("", embed=self.embed, ephemeral=False,
                                          allowed_mentions=discord.AllowedMentions.none())
        if self.log_msg:
            self.log_msg += f", in {itx.channel.mention} (`{itx.channel.id}`)\n" + \
                            f"[Jump to the tag message]({msg.jump_url})"
            if self.value == 2:
                await log_to_guild(itx.client, itx.guild, self.log_msg)
                staff_message_reports_channel = itx.client.get_guild_attribute(AttributeKeys.staff_reports_channel)
                if staff_message_reports_channel is not None:
                    await staff_message_reports_channel.send(self.log_msg)
        self.stop()

    async def on_timeout(self):
        self.send_publicly.disabled = True
        self.send_publicly.style = discord.ButtonStyle.gray

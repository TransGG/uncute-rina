from __future__ import annotations
import discord

from resources.utils.utils import log_to_guild
from resources.customs import Bot
from extensions.settings.objects import AttributeKeys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from extensions.tags.tags import CustomTag


class SendPubliclyTagView(discord.ui.View):
    def __init__(
            self,
            tag: CustomTag,
            report_to_staff: bool,
            timeout: int = None,
            log_msg=None,
    ):
        super().__init__()

        self.value = None
        self.timeout = timeout
        self.report_to_staff = report_to_staff
        self.tag = tag
        self.log_msg = log_msg

    @discord.ui.button(label='Send publicly',
                       style=discord.ButtonStyle.primary)
    async def send_publicly(
            self, itx: discord.Interaction[Bot], _button: discord.ui.Button
    ):
        itx.followup: discord.Webhook  # noqa

        if self.tag.report_to_staff:
            public_footer = (
                "Note: If you believe that this command was misused or "
                "abused, please do not argue in this channel. Instead, open "
                "a mod ticket and explain the situation there. Thank you."
            )
        else:
            public_footer = (f"Triggered by {itx.user.name} "
                             f"({itx.user.id})")
        embed = self.tag.embed
        if embed.footer.text is None:
            footer = ""
        else:
            footer = embed.footer.text + "\n"

        embed.set_footer(text=footer + public_footer)
        await itx.response.edit_message(
            content="Sending...", embed=None, view=None)
        try:
            # try sending the message without replying to the
            #  previous ephemeral
            msg = await itx.channel.send(
                "",
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none()
            )
        except discord.Forbidden:
            msg = await itx.followup.send(
                "",
                embed=embed,
                ephemeral=False,
                allowed_mentions=discord.AllowedMentions.none()
            )
        if self.log_msg:
            self.log_msg += (f", in {itx.channel.mention} "
                             f"(`{itx.channel.id}`)\n"
                             f"[Jump to the tag message]({msg.jump_url})")
            if self.report_to_staff:
                await log_to_guild(itx.client, itx.guild, self.log_msg)
                staff_message_reports_channel = itx.client.get_guild_attribute(
                    AttributeKeys.staff_reports_channel)
                if staff_message_reports_channel is not None:
                    await staff_message_reports_channel.send(self.log_msg)
        self.stop()

    async def on_timeout(self):
        self.send_publicly.disabled = True
        self.send_publicly.style = discord.ButtonStyle.gray

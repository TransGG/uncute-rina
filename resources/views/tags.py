import discord
from resources.customs.bot import Bot
from resources.utils.utils import log_to_guild, EnabledServers


class SendPublicly_TagView(discord.ui.View):
    def __init__(self, client: Bot, embed: discord.Embed, timeout=None, public_footer=None, logmsg=None, tag_name=None):
        super().__init__()
        if embed.footer.text is None:
            self.footer = ""
        else:
            self.footer = embed.footer.text + "\n"

        self.value = None
        self.client = client
        self.timeout = timeout
        self.public_footer = public_footer
        self.embed = embed
        self.logmsg = logmsg
        self.tag_name = tag_name

    @discord.ui.button(label='Send publicly', style=discord.ButtonStyle.primary)
    async def send_publicly(self, itx: discord.Interaction, _button: discord.ui.Button):
        self.value = 1
        if self.public_footer is None:
            self.public_footer = f"Triggered by {itx.user.name} ({itx.user.id})"
        else:
            self.public_footer = f"Note: If you believe that this command was misused or abused, " + \
                                 f"please do not argue in this channel. Instead, open a mod ticket " + \
                                 f"and explain the situation there. Thank you."
            self.value = 2
        self.embed.set_footer(text=self.footer + self.public_footer)
        await itx.response.edit_message(content="Sent successfully!", embed=None, view=None)
        try:
            # try sending the message without replying to the previous ephemeral
            msg = await itx.channel.send("", embed=self.embed, allowed_mentions=discord.AllowedMentions.none(), wait=True)
        except discord.Forbidden:
            msg = await itx.followup.send("", embed=self.embed, ephemeral=False, allowed_mentions=discord.AllowedMentions.none(), wait=True)
        if self.value == 2 and self.logmsg is not None:
            await log_to_guild(self.client, itx.guild, self.logmsg)
            cmd_mention = self.client.get_command_mention("tag")
            if itx.guild_id not in EnabledServers.dev_server_ids():
                staff_message_reports_channel = self.client.get_channel(self.client.custom_ids["staff_reports_channel"])
                await staff_message_reports_channel.send(f"{itx.user.name} (`{itx.user.id}`) used {cmd_mention} `tag:{self.tag_name}` anonymously, in {itx.channel.mention} (`{itx.channel.id}`)\n"
                                                         f"[Jump to the tag message]({msg.jump_url})")
        self.stop()

    async def on_timeout(self):
        self.send_publicly.disabled = True
        self.send_publicly.style = discord.ButtonStyle.gray

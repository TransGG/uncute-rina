from typing import Callable

import discord

from extensions.settings.objects import AttributeKeys, ModuleKeys
from resources.checks import MissingAttributesCheckFailure
from resources.customs import Bot
from resources.utils.utils import get_mod_ticket_channel  # for ticket channel id in Report tag
from resources.utils.utils import log_to_guild
# ^ for logging when people send tags anonymously (in case someone abuses the anonymity)

from extensions.tags.views import SendPubliclyTagView


class CustomTag:
    def __init__(
        self,
        tag_id: str,
        title: str,
        description: str,
        color: tuple[int, int, int],
        report_to_staff: bool
    ):
        color = discord.Color.from_rgb(*color)
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
        )

        self.id = tag_id
        self.embed = embed
        self.report_to_staff = report_to_staff

        self.command_mention: str | None = None
        self.send_user: discord.User | discord.Member | None = None
        self.public_message: discord.Message | None = None
        self.send_channel: discord.TextChannel | None = None

    @property
    def log_message(self) -> str:
        """
        Generates a log message from the tag's usage.

        Relies on functions setting the values for
        :py:attr:`command_mention`, :py:attr:`send_user`,
        :py:attr:`send_message`, and :py:attr:`send_channel`.

        :return: The generated log message.
        """
        username: str = getattr(self.send_user, "name", "unknown user")
        user_id: str = getattr(self.send_user, "id", "unknown id")

        return (
            f"{username} (`{user_id}`) "
            f"used {self.command_mention} `tag:{self.id}` "
            f"anonymously"
            + (f", in {self.send_channel.mention} (`{self.send_channel.id}`)\n"
               if self.send_channel is not None
               else "")
            + (f"[Jump to the tag message]({self.public_message.jump_url})"
               if self.public_message is not None
               else "")
        )

    async def send(
            self,
            itx: discord.Interaction[Bot],
            public: bool,
            anonymous: bool,
            report_to_staff: bool = False,
    ) -> None:
        """
        Send this tag to the guild.

        :param itx: The interaction to reply to (or its channel to send
          it in).
        :param public: Whether to send the tag publicly or not.
        :param anonymous: Whether to make public tags show the
         executor's username or not (automatically adds a log msg).
        :param report_to_staff: Whether the guild wants to log when
         sensitive tags are sent.
        """
        self.send_user = itx.user
        self.command_mention = itx.client.get_command_mention("tag")

        if public:
            await self._handle_send_publicly(
                itx, anonymous, report_to_staff)
        else:
            await self._handle_send_privately(
                itx, anonymous, report_to_staff)

    async def _handle_send_publicly(
            self,
            itx: discord.Interaction,
            anonymous: bool,
            report_to_staff: bool
    ) -> None:
        self.send_channel = itx.channel
        if not anonymous:
            await itx.response.send_message(embed=self.embed)
            return

        # send anonymously
        if report_to_staff:
            self.embed.set_footer(
                text="Note: If you believe that this command was "
                     "misused or abused, please do not argue in this "
                     "channel. Instead, open a mod ticket and explain "
                     "the situation there. Thank you."
            )

        await itx.response.send_message("Sending...", ephemeral=True)
        try:
            # Try to send the tag without replying to the
            #  previous response / ephemeral.
            self.public_message = await itx.channel.send(embed=self.embed)
        except discord.Forbidden:
            self.public_message = await itx.followup.send(
                embed=self.embed, ephemeral=False, wait=True)

        await log_to_guild(itx.client, itx.guild, self.log_message)

        if itx.client.is_module_enabled(
                itx.guild, ModuleKeys.report_tags_to_staff):
            log_channel = itx.client.get_guild_attribute(
                itx.guild, AttributeKeys.staff_reports_channel)
            if log_channel is None:
                raise MissingAttributesCheckFailure(
                    ModuleKeys.tags,
                    AttributeKeys.staff_reports_channel
                )
            await log_channel.send(self.log_message)

    async def _handle_send_privately(
            self,
            itx: discord.Interaction,
            anonymous: bool,
            report_to_staff: bool
    ) -> None:
        """
        Helper to send this tag message as ephemeral.

        :param itx: The interaction to respond to.
        :param anonymous: The way to share the tag after the user
         decides to click the "Send publicly" button.
        :param report_to_staff: Whether the guild wants to log when
         sensitive tags are sent.
        """
        itx.response: discord.InteractionResponse  # noqa
        if anonymous:
            view = SendPubliclyTagView(
                self, False, timeout=60)
        else:
            view = SendPubliclyTagView(
                self, report_to_staff, timeout=60, log_msg=self.log_message)

        await itx.response.send_message(
            "", embed=self.embed, view=view, ephemeral=True)
        return


# region Tags
def create_report_info_tag(
        mod_ticket_channel: discord.abc.Messageable | None
) -> CustomTag:
    ticket_string = f"create a mod ticket in <#{mod_ticket_channel.id}> or " \
        if mod_ticket_channel else ""

    tag = CustomTag(
        tag_id="report",
        title='Reporting a message or scenario',
        description=(f"Hi there! If anyone is making you uncomfortable, or "
                     f"you want to report or prevent a rule-breaking "
                     f"situation, you can `Right Click Message > Apps > "
                     f"Report Message` to notify our staff confidentially. "
                     f"You can also {ticket_string}DM a staff member."),
        color=(255, 0, 0),
        report_to_staff=True,
    )
    tag.embed.set_image(url="https://i.imgur.com/jxEcGvl.gif")
    return tag


async def send_report_info(
        itx: discord.Interaction, public: bool, anonymous: bool,
) -> None:
    """Helper to send report tag."""
    ticket_channel: discord.abc.Messageable | None = get_mod_ticket_channel(
        itx.client, itx.guild)
    tag = create_report_info_tag(ticket_channel)
    await tag.send(itx, public, anonymous, False)


async def send_enabling_embeds_info(
        itx: discord.Interaction[Bot], public: bool, anonymous: bool,
) -> None:
    """Helper to send enabling embeds tag."""
    itx.followup: discord.Webhook  # noqa
    txt = ("**Enabling Embeds**\n"
           "Embeds are a neat feature in discord that let you preview "
           "websites and show certain messages in a nicer format. Many bots "
           "make use of embeds to lay out information, as do I.\n"
           "Users can enable and disable this setting manually. Simply go to "
           "`Discord > App Settings > Chat > Embeds and Link Previews > Show "
           "embeds and previews website links pasted into chat` and toggle "
           "that setting.")
    # no embeds here because... there aren't any
    if anonymous and public:
        await itx.response.send_message("sending...", ephemeral=True)
        try:
            await itx.channel.send(txt)
        except discord.Forbidden:
            await itx.followup.send(txt, wait=True, ephemeral=False)
        await _send_tag_log_message(itx, "enabling embeds")
    else:
        # Not anonymous: Can just send it as response.
        # Anonymous but not public... Well that would be solved by
        #  sending it as ephemeral.
        await itx.response.send_message(txt, ephemeral=not public)

# endregion Tags


async def _send_tag_log_message(itx, tag_name) -> None:
    cmd_mention = itx.client.get_command_mention("tag")
    log_msg = (f"{itx.user.name} ({itx.user.id}) "
               f"used {cmd_mention} `tag:{tag_name}` anonymously")
    await log_to_guild(itx.client, itx.guild, log_msg)


tag_info_dict: dict[str, Callable] = {
    # sorted alphabetically
    "enabling embeds": send_enabling_embeds_info,
    "report": send_report_info,
}

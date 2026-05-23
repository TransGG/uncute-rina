import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.qotw.utils import create_thread
from extensions.settings.objects import (
    ModuleKeys,
    AttributeKeys,
    MessageableGuildChannel,
)
from resources.checks import (
    module_enabled_check,
    MissingAttributesCheckFailure
)
from resources.utils.utils import get_mod_ticket_channel
from resources.customs import Bot, GuildInteraction


class QOTW(commands.Cog):
    def __init__(self) -> None:
        pass

    @app_commands.command(
        name="qotw",
        description="Suggest a question for the weekly queue!"
    )
    @app_commands.describe(question="What question would you like to add?")
    @module_enabled_check(ModuleKeys.qotw)
    async def qotw(self, itx: GuildInteraction[Bot], question: str) -> None:
        # get channel of where this message has to be sent
        qotw_channel: discord.TextChannel | None
        qotw_channel = itx.client.get_guild_attribute(
            itx.guild,
            AttributeKeys.qotw_suggestions_channel
        )
        if qotw_channel is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.qotw,
                [AttributeKeys.qotw_suggestions_channel]
            )

        if len(question) > 400:
            ticket_channel: MessageableGuildChannel | None \
                = get_mod_ticket_channel(itx.client, guild_id=itx.guild.id)
            if ticket_channel is not None:
                special_request_string = (f"make a ticket (in "
                                          f"<#{ticket_channel.id}>).")
            else:
                special_request_string = "contact staff directly."
            await itx.response.send_message(
                "Please make your question shorter! (400 characters). "
                "If you have a special request, please "
                + special_request_string, ephemeral=True)
            await itx.followup.send("-# " + question, ephemeral=True)
            return

        await itx.response.defer(ephemeral=True)

        await create_thread(
            itx.client,
            (itx.user, qotw_channel, question),
            f"QOTW-{question[:50]}",
            AttributeKeys.qotw_suggestions_channel,
            emojis=[discord.PartialEmoji.from_str(emoji)
                    for emoji in ("⬆️", "⬇️")]
        )
        await itx.followup.send(
            "Successfully added your question to the queue! (must first "
            "be accepted by the staff team)",
            ephemeral=True
        )

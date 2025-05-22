from datetime import datetime
# to get embed send time for embed because cool (serves no real purpose)

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from extensions.settings.objects import ModuleKeys, AttributeKeys
from resources.checks import (
    not_in_dms_check,
    module_enabled_check,
    MissingAttributesCheckFailure
)
from resources.utils.utils import get_mod_ticket_channel
from resources.customs import Bot


class QOTW(commands.Cog):
    def __init__(self):
        pass

    @app_commands.command(
        name="qotw",
        description="Suggest a question for the weekly queue!"
    )
    @app_commands.describe(question="What question would you like to add?")
    @app_commands.check(not_in_dms_check)
    @module_enabled_check(ModuleKeys.qotw)
    async def qotw(self, itx: discord.Interaction[Bot], question: str):
        if len(question) > 400:
            ticket_channel: discord.abc.Messageable | None \
                = get_mod_ticket_channel(itx.client, guild_id=itx.guild.id)
            if ticket_channel:
                special_request_string = (f"make a ticket (in "
                                          f"<#{ticket_channel.id}>).")
            else:
                special_request_string = "contact staff directly."
            await itx.response.send_message(
                "Please make your question shorter! (400 characters). "
                "If you have a special request, please " +
                special_request_string, ephemeral=True)
            await itx.followup.send("-# " + question, ephemeral=True)
            return

        # get channel of where this message has to be sent
        qotw_channel = itx.client.get_guild_attribute(
            itx.guild,
            AttributeKeys.qotw_suggestions_channel
        )
        if qotw_channel is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.qotw,
                [AttributeKeys.qotw_suggestions_channel]
            )

        await itx.response.defer(ephemeral=True)

        # make uncool embed for the loading period while it sends
        #  the copyable version
        embed = discord.Embed(
            color=discord.Colour.from_rgb(r=33, g=33, b=33),
            description="Loading question...",
        )
        # send the uncool embed
        msg = await qotw_channel.send(
            "",
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        # make and join a thread under the question
        thread = await msg.create_thread(name=f"QOTW-{question[:50]}")
        await thread.join()
        # send a plaintext version of the question, and copy a link to it
        copyable_version = await thread.send(
            f"{question}",
            allowed_mentions=discord.AllowedMentions.none()
        )
        # edit the uncool embed to make it cool: Show question,
        #  link to plaintext, and upvotes/downvotes
        embed = discord.Embed(
            color=discord.Colour.from_rgb(r=255, g=255, b=172),
            title='',
            description=f"{question}\n"
                        f"[Jump to plain version]"
                        f"({copyable_version.jump_url})",
            timestamp=datetime.now()
        )
        username = getattr(itx.user, 'nick', None) or itx.user.name
        embed.set_author(
            name=f"{username}",
            url=f"https://original.poster/{itx.user.id}/",
            icon_url=itx.user.display_avatar.url
        )
        embed.set_footer(text="")

        await msg.edit(embed=embed)
        await msg.add_reaction("⬆️")
        await msg.add_reaction("⬇️")
        await itx.followup.send(
            "Successfully added your question to the queue! (must first "
            "be accepted by the staff team)",
            ephemeral=True
        )

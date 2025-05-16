import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from resources.checks import module_enabled_check
from resources.customs import Bot

from extensions.settings.objects import ModuleKeys


class ChangeChannel(commands.Cog):
    @app_commands.command(name="changechannel",
                          description="Direct conversation to another channel")
    @app_commands.describe(destination="Choose the channel to which to "
                                       "direct conversation")
    @module_enabled_check(ModuleKeys.change_channel)
    async def changechannel(
            self,
            itx: discord.Interaction[Bot],
            destination: discord.TextChannel
    ):
        itx.response: discord.InteractionResponse  # noqa
        itx.followup: discord.Webhook  # noqa

        if destination.id == itx.channel.id:
            await itx.response.send_message(
                "You cannot redirect conversation to the current channel.",
                ephemeral=True
            )
            return

        if not destination.permissions_for(itx.user).send_messages:
            await itx.response.send_message(
                "You must have permission to send messages in the "
                "destination channel.",
                ephemeral=True
            )
            return

        if not destination.permissions_for(itx.guild.me).send_messages:
            await itx.response.send_message(
                "I cannot send messages in the destination channel.",
                ephemeral=True
            )
            return

        response = await itx.response.defer(ephemeral=False)

        target = await destination.send(
            f"Conversation was moved from {response.resource.jump_url} "
            f"by {itx.user.mention}.",
            allowed_mentions=discord.AllowedMentions.none()
        )

        await itx.followup.send(
            f"{itx.user.mention} has requested to move the "
            f"conversation to {target.jump_url}.",
            allowed_mentions=discord.AllowedMentions.none()
        )

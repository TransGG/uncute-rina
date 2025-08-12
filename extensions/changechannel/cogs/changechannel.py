import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from resources.checks import module_enabled_check
from resources.customs import Bot, GuildInteraction

from extensions.settings.objects import ModuleKeys


class ChangeChannel(commands.Cog):
    @app_commands.command(name="changechannel",
                          description="Direct conversation to another channel")
    @app_commands.describe(destination="Choose the channel to which to "
                                       "direct conversation")
    @module_enabled_check(ModuleKeys.change_channel)
    async def changechannel(
            self,
            itx: GuildInteraction[Bot],
            destination: discord.TextChannel
    ):
        itx.response: discord.InteractionResponse[Bot]  # type: ignore
        itx.followup: discord.Webhook  # type: ignore

        if itx.channel is None:
            await itx.response.send_message(
                "I don't know what channel you're currently in, so I "
                "also can't send any forwarding message!",
                ephemeral=True
            )
            return

        if destination.id == itx.channel.id:
            await itx.response.send_message(
                "You cannot redirect conversation to the current channel.",
                ephemeral=True
            )
            return

        if isinstance(itx.user, discord.User):
            await itx.response.send_message(
                "I don't know if you are member of this guild, so I "
                "also can't check if you have permissions to send messages in "
                "any channels. Try again later or contact staff if you think "
                "this is a mistake.",
                ephemeral=True
            )
            return

        for channel, channel_string in [(itx.channel, "current"),
                                        (destination, "destination")]:
            for user, user_string in [(itx.user, "You must"),
                                      (itx.guild.me, "I do not")]:
                if not channel.permissions_for(user).send_messages:
                    await itx.response.send_message(
                        f"{user_string} have permission to send "
                        f"messages in the {channel_string} channel.",
                        ephemeral=True,
                    )
                    return

        response = await itx.response.defer(ephemeral=False)
        if response is None or response.resource is None:
            await itx.followup.send(
                "Something went wrong! I couldn't retrieve the jump url "
                "for this message!\n"
                + ("`response` was None!" if response is None
                   else "response.resource was None!")
            )
            return

        assert isinstance(response.resource, discord.InteractionMessage), (
            "The response resource wasn't an InteractionMessage (but instead "
            "an InteractionCallbackActivityInstance, probably)!"
        )

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

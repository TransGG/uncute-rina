import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from resources.customs.bot import Bot


class ChangeChannel(commands.Cog):
    @app_commands.command(name="changechannel", description="Direct conversation to another channel")
    @app_commands.describe(destination="Choose the channel to which to direct conversation")
    async def changechannel(self, itx: discord.Interaction, destination: discord.TextChannel):
        if destination.id == itx.channel.id:
            await itx.response.send_message("You cannot redirect conversation to the current channel.", ephemeral=True)
            return

        if not destination.permissions_for(itx.user).send_messages:
            await itx.response.send_message("You must have permission to send messages in the destination channel.", ephemeral=True)
            return
        
        if not destination.permissions_for(itx.guild.me).send_messages:
            await itx.response.send_message("I cannot send messages in the destination channel.", ephemeral=True)
            return

        response = await itx.response.send_message(destination.mention, ephemeral=False)

        source = response.resource
        target = await destination.send(f"[{source.jump_url} =>]")
        await source.edit(content=f"[=> {target.jump_url}]")
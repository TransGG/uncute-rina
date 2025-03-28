from datetime import datetime  # to get embed send time for embed because cool (serves no real purpose)

import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from resources.customs.bot import Bot
from resources.utils.utils import get_mod_ticket_channel_id


class QOTW(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client

    @app_commands.command(name="qotw", description="Suggest a question for the weekly queue!")
    @app_commands.describe(question="What question would you like to add?")
    async def qotw(self, itx: discord.Interaction, question: str):
        if len(question) > 400:
            channel_id = get_mod_ticket_channel_id(self.client, guild_id=itx.guild.id)
            await itx.response.send_message(
                f"Please make your question shorter! (400 characters) If you have a special request, "
                f"please make a ticket (in <#{channel_id}>)",
                ephemeral=True)
            await itx.followup.send("-# " + question, ephemeral=True)
            return
        await itx.response.defer(ephemeral=True)
        try:
            # get channel of where this message has to be sent
            confirm_channel = itx.client.get_channel(self.client.custom_ids["staff_qotw_channel"])
            # make uncool embed for the loading period while it sends the copyable version
            embed = discord.Embed(
                color=discord.Colour.from_rgb(r=33, g=33, b=33),
                description=f"Loading question...",
            )
            # send the uncool embed
            msg = await confirm_channel.send(
                "",
                embed=embed,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            # make and join a thread under the question
            thread = await msg.create_thread(name=f"QOTW-{question[:50]}")
            await thread.join()
            # send a plaintext version of the question, and copy a link to it
            copyable_version = await thread.send(f"{question}", allowed_mentions=discord.AllowedMentions.none())
            # edit the uncool embed to make it cool: Show question, link to plaintext, and upvotes/downvotes
            embed = discord.Embed(
                color=discord.Colour.from_rgb(r=255, g=255, b=172),
                title=f'',
                description=f"{question}\n[Jump to plain version]({copyable_version.jump_url})",
                timestamp=datetime.now()
            )
            embed.set_author(
                name=f"{itx.user.nick or itx.user.name}",
                url=f"https://original.poster/{itx.user.id}/",
                icon_url=itx.user.display_avatar.url
            )
            embed.set_footer(text=f"")

            await msg.edit(embed=embed)
            await msg.add_reaction("⬆️")
            await msg.add_reaction("⬇️")
            await itx.followup.send(
                "Successfully added your question to the queue! (must first be accepted by the staff team)",
                ephemeral=True)
        except:  # something went wrong before so i want to see if it happens again
            await itx.followup.send("Something went wrong!")
            raise

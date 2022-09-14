import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *

import pymongo # for online database
from pymongo import MongoClient



class QOTW(commands.Cog):
    def __init__(self, client):
        global RinaDB
        self.client = client
        RinaDB = client.RinaDB

    @app_commands.command(name="qotw",description="Suggest a question for the weekly queue!")
    @app_commands.describe(question="What question would you like to add?")
    async def qotw(self, itx: discord.Interaction, question: str):
        if len(question) > 250:
            await itx.response.send_message("Please make your question shorter! If you have a special request, please make a ticket (in #contact-staff)",ephemeral=True)
        # get channel id of where this message has to be sent
        confirmChannel = itx.channel
        confirmChannel.id = 985931648094834801
        # make cool embed
        embed = discord.Embed(
                color = discord.Colour.from_rgb(r=33, g=33, b=33),
                description = f"Loading question...", #{message.content}
            )
        # yeah. Now send the embed here
        msg = await confirmChannel.send(
                "",
                embed = embed,
                allowed_mentions = discord.AllowedMentions.none(),
            )
        await msg.add_reaction("⬆️")
        await msg.add_reaction("⬇️")
        thread = await msg.create_thread(name=f"QOTW-{question[:50]}")
        await thread.join()
        copyableVersion = await thread.send(f"{question}",allowed_mentions=discord.AllowedMentions.none())

        embed = discord.Embed(
                color = discord.Colour.from_rgb(r=255, g=255, b=172),
                title = f'',
                description = f"{question}\n[Jump to plain version]({copyableVersion.jump_url})",
                timestamp = datetime.now()
            )
        embed.set_author(
                name = f"{itx.user.nick or itx.user.name}",
                url = f"", #todo
                icon_url = itx.user.display_avatar.url
        )
        embed.set_footer(text = f"")

        await msg.edit(embed=embed)
        await itx.response.send_message("Successfully added your question to the queue! (must first be accepted by the staff team)",ephemeral=True)

async def setup(client):
    await client.add_cog(QOTW(client))

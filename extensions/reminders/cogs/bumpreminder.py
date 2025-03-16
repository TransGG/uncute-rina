from datetime import datetime, timedelta

import discord
import discord.ext.commands as commands

from resources.customs.bot import Bot

from extensions.reminders.objects import BumpReminderObject


class BumpReminder(commands.Cog):
    def __init__(self, client: Bot):
        self.client: Bot = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if len(message.embeds) > 0:
            if message.embeds[0].description is not None:
                if message.embeds[0].description.startswith("Bump done!"):
                    # collection = self.client.rina_db["guildInfo"]
                    # query = {"guild_id": message.guild.id}
                    # guild_data = collection.find_one(query)
                    # bump_bot_id = guild_data["bumpBot"]
                    bump_bot_id = await self.client.get_guild_info(message.guild, "bumpBot")

                    if message.author.id == bump_bot_id:
                        remindertime = datetime.now() + timedelta(hours=2)
                        BumpReminderObject(self.client, message.guild, remindertime)

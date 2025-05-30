from datetime import datetime, timedelta

import discord
import discord.ext.commands as commands

from extensions.settings.objects import ModuleKeys, AttributeKeys
from resources.checks import MissingAttributesCheckFailure
from resources.customs import Bot

from extensions.reminders.objects import BumpReminderObject


class BumpReminder(commands.Cog):
    def __init__(self, client: Bot):
        self.client: Bot = client

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not self.client.is_module_enabled(
                message.guild, ModuleKeys.bump_reminder):
            return

        bump_bot: discord.User | None = self.client.get_guild_attribute(
            message.guild, AttributeKeys.bump_reminder_bot)
        if bump_bot is None:
            raise MissingAttributesCheckFailure(
                ModuleKeys.bump_reminder, [AttributeKeys.bump_reminder_bot])

        if message.author.id != bump_bot.id:
            return
        if len(message.embeds) > 0:
            if message.embeds[0].description is None:
                return
            if message.embeds[0].description.startswith("Bump done!"):
                remindertime = datetime.now().astimezone() + timedelta(hours=2)
                BumpReminderObject(self.client, message.guild, remindertime)

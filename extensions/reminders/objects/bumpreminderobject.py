import discord
from datetime import datetime, timedelta

from extensions.settings.objects import AttributeKeys
from resources.customs import Bot


class BumpReminderObject:
    def __init__(self, client: Bot, guild: discord.Guild, remindertime: datetime):
        self.client = client
        self.guild = guild
        self.remindertime = remindertime - timedelta(seconds=1.5)
        client.sched.add_job(self.send_reminder, "date", run_date=self.remindertime)

    async def send_reminder(self):
        bump_channel: discord.abc.Messageable | None
        bump_role: discord.Role | None
        bump_channel, bump_role = self.client.get_guild_attribute(
            self.guild, AttributeKeys.bump_reminder_channel,
            AttributeKeys.bump_reminder_role)

        if bump_channel is None or bump_role is None:
            return

        await bump_channel.send(f"{bump_role.mention} The next bump is ready!",
                                allowed_mentions=discord.AllowedMentions(roles=[bump_role]))

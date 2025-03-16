import discord
from datetime import datetime, timedelta

from resources.customs.bot import Bot


class BumpReminderObject:
    def __init__(self, client: Bot, guild: discord.Guild, remindertime: datetime):
        self.client = client
        self.guild = guild
        self.remindertime = remindertime - timedelta(seconds=1.5)
        client.sched.add_job(self.send_reminder, "date", run_date=self.remindertime)

    async def send_reminder(self):
        bump_channel_id, bump_role_id = await self.client.get_guild_info(self.guild, "bumpChannel", "bumpRole")
        bump_channel = await self.guild.fetch_channel(bump_channel_id)
        bump_role = self.guild.get_role(bump_role_id)

        await bump_channel.send(f"{bump_role.mention} The next bump is ready!",
                                allowed_mentions=discord.AllowedMentions(roles=[bump_role]))

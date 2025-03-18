from resources.customs.bot import Bot

from extensions.reminders.cogs import RemindersCog, BumpReminder


async def setup(client: Bot):
    await client.add_cog(RemindersCog(client))
    await client.add_cog(BumpReminder(client))

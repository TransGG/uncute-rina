from extensions.reminders.cogs import BumpReminder, RemindersCog
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(RemindersCog())
    await client.add_cog(BumpReminder(client))

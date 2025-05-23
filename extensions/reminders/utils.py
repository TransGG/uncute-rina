import discord

from resources.customs import Bot

from extensions.reminders.objects import (
    ReminderDict, DatabaseData  # for typechecking only
)


def get_user_reminders(
        client: Bot, user: discord.Member | discord.User
) -> list[ReminderDict]:
    """Fetch a user's reminders."""
    # Check if user has an entry in database yet.
    collection = client.rina_db["reminders"]
    query = {"userID": user.id}
    db_data: DatabaseData = collection.find_one(query)
    if db_data is None:
        collection.insert_one(query)
        db_data = collection.find_one(query)
    return db_data.get('reminders', [])

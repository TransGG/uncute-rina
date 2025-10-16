import discord
from typing import cast

from resources.customs import Bot

from extensions.reminders.objects import (
    ReminderDict, DatabaseData  # for typechecking only
)


async def get_user_reminders(
        client: Bot, user: discord.Member | discord.User
) -> list[ReminderDict]:
    """Fetch a user's reminders."""
    # Check if user has an entry in database yet.
    collection = client.async_rina_db["reminders"]
    query = {"userID": user.id}
    # We're getting this straight from the DB, so it should be fine
    api_response = cast(DatabaseData | None, await collection.find_one(query))
    db_data: DatabaseData
    if api_response is None:
        await collection.insert_one(query)
        db_data = DatabaseData(**query)
    else:
        db_data = api_response
    return db_data.get('reminders', [])

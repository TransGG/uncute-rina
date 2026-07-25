from extensions.todolist.cogs import TodoList
from resources.customs.bot import Bot


async def setup(client: Bot) -> None:
    await client.add_cog(TodoList())

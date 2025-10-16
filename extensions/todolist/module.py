from resources.customs.bot import Bot

from extensions.todolist.cogs import TodoList


async def setup(client: Bot) -> None:
    await client.add_cog(TodoList())

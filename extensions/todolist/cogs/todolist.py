import discord
import discord.app_commands as app_commands
import discord.ext.commands as commands

from resources.customs import Bot


class TodoList(commands.Cog):
    def __init__(self):
        pass

    @app_commands.command(name="todo", description="Add or remove a to-do!")
    @app_commands.describe(mode="Do you want to add, remove a to-do item, "
                                "or check your current items?",
                           todo="Add/remove a todo-list item. Does nothing "
                                "if u wanna check it")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(
            name='Add something to your to-do list', value=1),
        discord.app_commands.Choice(
            name='Remove to-do', value=2),
        discord.app_commands.Choice(
            name='Check', value=3)
    ])
    async def todo(
            self,
            itx: discord.Interaction[Bot],
            mode: int,
            todo: str = None
    ):
        # todo: use Enum for mode
        if mode == 1:  # Add item to to-do list
            if todo is None:
                cmd_todo = itx.client.get_command_mention_with_args(
                    "todo", mode="Check")
                await itx.response.send_message(
                    f"This command lets you add items to your to-do list!\n"
                    f"Type whatever you still plan to do in the `todo: `"
                    f" argument, and then you can see your current to-do list "
                    f"with {cmd_todo}!",
                    ephemeral=True,
                )
                return
            if len(todo) > 500:
                itx.response.send_message(
                    "I.. don't think having such a big to-do message is gonna "
                    "be very helpful..",
                    ephemeral=True,
                )
                return
            collection = itx.client.rina_db["todoList"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                todo_list = []
            else:
                todo_list = search["list"]
            todo_list.append(todo)
            collection.update_one(
                query,
                {"$set": {"list": todo_list}},
                upsert=True
            )
            await itx.response.send_message(
                f"Successfully added an item to your to-do list! "
                f"({len(todo_list)} item{'s' * (len(todo_list) != 1)} in "
                f"your to-do list now)",
                ephemeral=True,
            )

        elif mode == 2:  # Remove item from to-do list
            if todo is None:
                cmd_todo = itx.client.get_command_mention_with_args(
                    "todo", mode="Check")
                await itx.response.send_message(
                    f"Removing todo's with this command is done with IDs. "
                    f"You can see your current list of todo's using "
                    f"{cmd_todo}.\n"
                    f"This list will start every todo-list item with a "
                    f"number. This is the ID you're looking for. This number "
                    f"can be filled into the `todo: ` argument to remove it.",
                    ephemeral=True,
                )
                return
            try:
                todo = int(todo)
            except ValueError:
                await itx.response.send_message(
                    "To remove an item from your to-do list, you must "
                    "give the id of the item you want to remove. This "
                    "should be a number... You didn't give a number...",
                    ephemeral=True,
                )
                return
            collection = itx.client.rina_db["todoList"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                await itx.response.send_message(
                    "There are no items on your to-do list, so you can't "
                    "remove any either...",
                    ephemeral=True,
                )
                return
            todo_list = search["list"]

            try:
                del todo_list[todo]
            except IndexError:
                cmd_todo = itx.client.get_command_mention("todo")
                await itx.response.send_message(
                    f"Couldn't delete that ID, because there isn't any item "
                    f"on your list with that ID. Use {cmd_todo} "
                    f"`mode:Check` to see the IDs assigned to each item on "
                    f"your list",
                    ephemeral=True,
                )
                return
            collection.update_one(
                query,
                {"$set": {"list": todo_list}},
                upsert=True
            )
            await itx.response.send_message(
                f"Successfully removed '{todo}' from your to-do list. "
                f"Your list now contains {len(todo_list)} "
                f"item{'s' * (len(todo_list) != 1)}.",
                ephemeral=True,
            )
        elif mode == 3:
            collection = itx.client.rina_db["todoList"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                await itx.response.send_message(
                    "There are no items on your to-do list, so.. Good job! "
                    "nothing to list here....",
                    ephemeral=True,
                )
                return
            todo_list = search["list"]
            length = len(todo_list)

            ans = []
            for item_id in range(length):
                ans.append(f"`{item_id}`: {todo_list[item_id]}")
            ans = '\n'.join(ans)
            await itx.response.send_message(
                f"Found {length} to-do item{'s' * (length != 1)}:\n{ans}",
                ephemeral=True
            )

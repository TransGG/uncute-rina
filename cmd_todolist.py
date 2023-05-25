from Uncute_Rina import *
from import_modules import *

class TodoList(commands.Cog):
    def __init__(self, client: Bot):
        global RinaDB
        RinaDB = client.RinaDB
        self.client = client

    @app_commands.command(name="todo",description="Add or remove a to-do!")
    @app_commands.describe(mode="Do you want to add, remove a to-do item, or check your current items?",
                           todo="Add/remove a todo-list item. Does nothing if u wanna check it")
    @app_commands.choices(mode=[
        discord.app_commands.Choice(name='Add something to your to-do list', value=1),
        discord.app_commands.Choice(name='Remove to-do', value=2),
        discord.app_commands.Choice(name='Check', value=3)
    ])
    async def todo(self, itx: discord.Interaction, mode: int, todo: str = None):
        if mode == 1: # Add item to to-do list
            if todo is None:
                cmd_mention = self.client.get_command_mention("todo")
                await itx.response.send_message(f"This command lets you add items to your to-do list!\n"
                                                f"Type whatever you still plan to do in the `todo: ` argument, "
                                                f"and then you can see your current to-do list with {cmd_mention} "
                                                f"`mode:Check`!", ephemeral=True)
                return
            if len(todo) > 500:
                itx.response.send_message("I.. don't think having such a big to-do message is gonna be very helpful..",ephemeral=True)
                return
            collection = RinaDB["todoList"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                list = []
            else:
                list = search["list"]
            list.append(todo)
            collection.update_one(query, {"$set":{f"list":list}}, upsert=True)
            await itx.response.send_message(f"Successfully added an item to your to-do list! ({len(list)} item{'s'*(len(list)!=1)} in your to-do list now)",ephemeral=True)

        elif mode == 2: # Remove item from to-do list
            if todo is None:
                cmd_mention = self.client.get_command_mention("todo")
                await itx.response.send_message(f"Removing todo's with this command is done with IDs. You can see your current list "
                                                f"of todo's using {cmd_mention} `mode:Check`. \n"
                                                f"This list will start every todo-list item with a number. This is the ID you're "
                                                f"looking for. This number can be filled into the `todo: ` argument to remove it.", ephemeral=True)
                return
            try:
                todo = int(todo)
            except ValueError:
                await itx.response.send_message("To remove an item from your to-do list, you must give the id of the item you want to remove. This should be a number... You didn't give a number...", ephemeral=True)
                return
            collection = RinaDB["todoList"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                await itx.response.send_message("There are no items on your to-do list, so you can't remove any either...",ephemeral=True)
                return
            list = search["list"]

            try:
                del list[todo]
            except IndexError:
                cmd_mention = self.client.get_command_mention("todo")
                await itx.response.send_message(f"Couldn't delete that ID, because there isn't any item on your list with that ID.. Use {cmd_mention} `mode:Check` to see the IDs assigned to each item on your list",ephemeral=True)
                return
            collection.update_one(query, {"$set":{f"list":list}}, upsert=True)
            await itx.response.send_message(f"Successfully removed '{todo}' from your to-do list. Your list now contains {len(list)} item{'s'*(len(list)!=1)}.", ephemeral=True)
        elif mode == 3:
            collection = RinaDB["todoList"]
            query = {"user": itx.user.id}
            search = collection.find_one(query)
            if search is None:
                await itx.response.send_message("There are no items on your to-do list, so.. Good job! nothing to list here....",ephemeral=True)
                return
            list = search["list"]
            length = len(list)

            ans = []
            for id in range(length):
                ans.append(f"`{id}`: {list[id]}")
            ans = '\n'.join(ans)
            await itx.response.send_message(f"Found {length} to-do item{'s'*(length!=1)}:\n{ans}",ephemeral=True)



async def setup(client):
    await client.add_cog(TodoList(client))

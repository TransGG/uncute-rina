from utils import * #imports 'discord import' and 'mongodb' things too

def getTableStatus(table):
    status = {
        "msg":{
            "new":"new",
            "open":"join",
            "locked":"lock"
        },
        "label":{
            "new":" Create ",
            "open":" Join ",
            "locked":" Locked "
        }
    }
    msg = status["msg"][table["status"]]
    label = status["label"][table["status"]]
    if table["status"] == "locked":
        disabled = True
    else:
        disabled = False
    return disabled,msg,label

class Table(commands.GroupCog, name="table"):
    def __init__(self, client):
        global RinaDB
        RinaDB = client.RinaDB
        self.client = client

    class TableButton(discord.ui.Button):
        async def callback(self, itx: discord.Interaction):
            await itx.response.defer(ephemeral=True)
            query = {"guild_id": itx.guild_id}
            collection = RinaDB["tableInfo"]
            tableInfo = collection.find_one(query)
            if tableInfo is None:
                cmd_mention = self.client.getCommandMention("table admin built")
                await itx.followup.send(f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention}!",ephemeral=True)
                return
            if itx.message.id == tableInfo["message"]:
                # check if user has a table role
                # if user has no roles:
                #   if table is new, add owner role, open table
                #   if table is open, add member role
                # if user has owner role, say they have to close the table instead of losing their role
                # if user has member role, remove their role
                #   if table is locked, announce it too
                for tableId in tableInfo:
                    if type(tableInfo[tableId]) is not dict: continue
                    table = tableInfo[tableId]
                    for role in itx.user.roles:
                        #if you have a role of this table
                        if self.custom_id == tableId:
                            if role.id == table["owner"]:
                                cmd_mentionClose = self.client.getCommandMention("table close")
                                cmd_mentionNewOwner = self.client.getCommandMention("table newowner")
                                await itx.followup.send(f"You can't leave this table because you are the owner. As owner,\n - close table {table['id']} ({cmd_mentionClose}), or\n - transfer the ownership to someone else ({cmd_mentionNewOwner}).",ephemeral=True)
                                return
                            elif role.id == table["member"]:
                                await itx.user.remove_roles(role,reason="Removed from table role after clicking on button.")
                                # send message in table chat
                                category = discord.utils.find(lambda r: r.id == table["category"], itx.guild.categories)
                                channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
                                await channel.send(f"{itx.user.nick or itx.user.name} ({itx.user.id}) left the table!", allowed_mentions=discord.AllowedMentions.none())
                                # send message to clicker
                                await itx.followup.send(f"Successfully removed you from table {table['id']}",ephemeral=True)
                                return
                        #if you already have another table's role
                        if role.id == table["owner"] or role.id == table["member"]:
                            await itx.followup.send(f"You can currently only join one table at a time. Leave Table {table['id']} first before you can join another!",ephemeral=True)
                            return #todo; let them join multiple tables
                # doesn't have the role yet
                table, tableId = [tableInfo[self.custom_id], self.custom_id]
                if table["status"] == "new":
                    # give Member the table owner role; open table
                    collection.update_one(query, {"$set":{f"{tableId}.status":"open"}}, upsert=True)
                    await Table.tablemsgupdate(Table, itx)
                    role = discord.utils.find(lambda r: r.id == table["owner"], itx.guild.roles)
                    await itx.user.add_roles(role)
                    # send message in table chat
                    category = discord.utils.find(lambda r: r.id == table["category"], itx.guild.categories)
                    channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
                    await channel.send(f"This table was opened by {itx.user.nick or itx.user.name} ({itx.user.id}).", allowed_mentions=discord.AllowedMentions.none())
                    await channel.send(f"{itx.user.nick or itx.user.name} ({itx.user.id}) joined the table as Table Owner", allowed_mentions=discord.AllowedMentions.none())
                    # send message to clicker
                    await itx.followup.send(f"Successfully created and joined table {table['id']}",ephemeral=True)
                    return
                elif table["status"] == "open":
                    # give Member the table member role
                    role = discord.utils.find(lambda r: r.id == table["member"], itx.guild.roles)
                    await itx.user.add_roles(role)
                    # send message in table chat
                    category = discord.utils.find(lambda r: r.id == table["category"], itx.guild.categories)
                    channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
                    await channel.send(f"{itx.user.nick or itx.user.name} ({itx.user.id}) joined the table!", allowed_mentions=discord.AllowedMentions.none())
                    # send message to clicker
                    await itx.followup.send(f"Successfully joined table {table['id']}",ephemeral=True)
                    return
                else:
                    await itx.followup.send("I don't know how you did it.. But you can't join a locked table!\nPerhaps the table doesn't have a status? That's odd...\n    Please give staff (Mia) a heads-up about this",ephemeral=True)
                    return

    async def tablemsg(self, itx: discord.Interaction,channel=None):
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find_one(query)
        if tableInfo is None:
            cmd_mention = self.client.getCommandMention("table admin build")
            await itx.response.send_message(f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention}!",ephemeral=True)
            return
        embed1 = discord.Embed(color=8481900, type='rich',description=" ")
        embed2 = discord.Embed(color=8481900, type='rich', title='Join a Table!',
                               description="Click one of the buttons below to create or join a table!~")
        embed1.set_image(url="https://i.imgur.com/SBy90SG.png")
        embed2.set_image(url="https://i.imgur.com/t3zhm4k.png") # i feel like this doesn't do anything..

        view = discord.ui.View(timeout=None)
        for x in tableInfo:
            x = tableInfo[x] #todo todo todo # i forgot why i wrote this thrice...
            try:
                disabled,status,label = getTableStatus(x)
            except TypeError:
                continue
            embed2.add_field(name=f'{x["emoji"]} Table {x["id"]} ({status})',value=f'<@&{x["member"]}>')
            view.add_item(self.TableButton(label=f'{label} {x["id"]}', disabled=disabled,
                          custom_id="table"+x["id"], emoji=discord.PartialEmoji.from_str(x["emoji"])))
            # button = discord.ui.Button(style=discord.ButtonStyle.secondary, label=f'{label} {x["id"]}',
            #             disabled=disabled, custom_id="table"+x["id"], emoji=discord.PartialEmoji.from_str(x["emoji"]))
            # view.add_item(button)

        if channel:
            itx.channel_id, itx.channel.id = [channel.id,channel.id]
        warning = ""
        if "message" in tableInfo:
            debug(f"I am looking for {tableInfo['message']}, most likely in {tableInfo['msgChannel']}",color="blue")
            # await itx.response.defer(ephemeral=True)
            try:
                c = itx.guild.text_channels[0]
                c.id = tableInfo["msgChannel"]
                msg = await c.fetch_message(tableInfo["message"])
                await msg.delete()
            except (discord.errors.HTTPException, discord.errors.Forbidden): # notsure
                warning = "Couldn't find a message to delete...\n"

        msg = await itx.channel.send(embeds=[embed1,embed2],view=view)

        collection.update_one(query, {"$set":{
            "msgChannel": msg.channel.id,
            "message"   : msg.id}}, upsert=True)
        await itx.response.send_message(warning+"Sent message successfully.",ephemeral=True)

    async def tablemsgupdate(self, itx: discord.Interaction):
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find_one(query)
        if tableInfo is None:
            cmd_mention = self.client.getCommandMention("table admin build")
            await itx.response.send_message(f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention}!",ephemeral=True)
            return

        embed1 = discord.Embed(color=8481900, type='rich',description=" ")
        embed2 = discord.Embed(color=8481900, type='rich', title='Join a Table!',
                               description="Click one of the buttons below to create or join a table!~")
        embed1.set_image(url="https://i.imgur.com/SBy90SG.png")
        embed2.set_image(url="https://i.imgur.com/t3zhm4k.png") # i feel like this doesn't do anything..
        view = discord.ui.View(timeout=None)
        for x in tableInfo:
            x = tableInfo[x]
            try:
                disabled,status,label = getTableStatus(x)
            except TypeError:
                continue
            embed2.add_field(name=f'{x["emoji"]} Table {x["id"]} ({status})',value=f'<@&{x["member"]}>')
            view.add_item(self.TableButton(label=f'{label} {x["id"]}', disabled=disabled,
                          custom_id="table"+x["id"], emoji=discord.PartialEmoji.from_str(x["emoji"])))

        if "message" not in tableInfo:
            debug("Couldn't find message in tableInfo (update)",color="yellow")
            return False
        c = await itx.guild.fetch_channel(tableInfo["msgChannel"])
        msg = await c.fetch_message(tableInfo["message"])
        await msg.edit(embeds=[embed1,embed2],view=view)

    admin = app_commands.Group(name='admin', description='Edit a table system')

    @admin.command(name="sendmsg",description="Send initial table object message. developmental purposes only")
    @app_commands.describe(channel="Which channel do you want to send the message in?")
    async def tablemsgsend(self,itx: discord.Interaction, channel: discord.TextChannel = None):
        if not isAdmin(itx):
            await itx.response.send_message("You do not have permission to send this message (staff-only)",ephemeral=True)
            return
        await self.tablemsg(itx,channel)

    @admin.command(name="list",description="Get a list of tables in the table system")
    async def list(self,itx: discord.Interaction):
        if not isAdmin(itx):
            await itx.response.send_message("You do not have permission to add a new table",ephemeral=True)
            return

        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find_one(query)
        if tableInfo is None:
            cmd_mention = self.client.getCommandMention("table admin build")
            await itx.response.send_message(f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention}!",ephemeral=True)
            return
        tables = "List of tables:"
        for tableId in tableInfo:
            table = tableInfo[tableId]
            if type(table) is not dict:
                continue
            tables += f"\nTable `{table['id']}`, Category:<#{table['category']}>, Owner: <@&{table['owner']}>, Member: <@&{table['member']}>, Emoji: {table['emoji']}, Status: {table['status']}"
        await itx.response.send_message(tables, allowed_mentions=discord.AllowedMentions.none())

    @admin.command(name="build",description="Link a new table to the table system")
    @app_commands.describe(id="Give the table a number: \"1\" for \"Table 1\", eg.",
                           category="Mention the table category",
                           owner="Ping/mention the table owner role",
                           member="Ping/mention the table (member) role",
                           emoji="Type the emoji (circle) for the table")
    async def build(self, itx: discord.Interaction, id: str, category: discord.CategoryChannel, owner: discord.Role, member: discord.Role, emoji: str):
        if not isAdmin(itx):
            await itx.response.send_message("You do not have permission to add a new table",ephemeral=True)
            return

        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find_one(query)
        if tableInfo is None:
            collection.insert_one(query)
            tableInfo = collection.find_one(query)

        warning = ""
        for table in tableInfo:
            if type(tableInfo[table]) is not dict:
                continue
            if id == tableInfo[table]["id"]:
                await itx.response.send_message("There is already a table with this ID. You can't add two tables with the same id.\nThat would make it difficult to link buttons and remove the table in the future :/.",ephemeral=True,allowed_mentions=discord.AllowedMentions.none())
                return
        for tableId in tableInfo:
            table = tableInfo[tableId]
            if type(table) is not dict:
                continue
            if category.id == table["category"]:
                warning += f"Warning: You already registered this category in table {table['id']}!\n"
            if owner.id == table["owner"]:
                warning += f"Warning: You already registered this owner role in table {table['id']}!\n"
            if member.id == table["member"]:
                warning += f"Warning: You already registered this member role in table {table['id']}!\n"
            if emoji == table["emoji"]:
                warning += f"Warning: You already registered this emoji in table {table['id']}!\n"

        tableData = {
            "id":id,
            "category":category.id,
            "owner":owner.id,
            "member":member.id,
            "emoji":emoji,
            "status":"new",
        }
        collection.update_one(query, {"$set":{"table"+id : tableData}}, upsert=True)
        await self.tablemsgupdate(itx)
        await itx.response.send_message(warning+f"┬─┬ ノ( ゜-゜ノ) Created `Table {id}` with category:<#{category.id}>, owner:<@&{owner.id}>, member:<@&{member.id}>, emoji:{emoji}",allowed_mentions=discord.AllowedMentions.none())

    @admin.command(name="force_close",description="Force close a table, so a new group can start.")
    @app_commands.describe(id="Give the table number: \"1\" for \"Table 1\", eg.")
    async def tableForceClose(self, itx: discord.Interaction, id: str):
        if not isAdmin(itx):
            await itx.response.send_message("You do not have permission to forcibly close a table",ephemeral=True)
            return
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find_one(query)
        if tableInfo is None:
            cmd_mention = self.client.getCommandMention("table admin build")
            await itx.response.send_message(f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention}!",ephemeral=True)
            return

        closable = ""
        if "message" not in tableInfo:
            cmd_mention = self.client.getCommandMention("table admin sendmsg")
            await itx.response.send_message(f"There is no table message to update, thus I'm afraid you can't close the table.. Please ask an admin to fix this with {cmd_mention}",ephemeral=True)
            return
        for table in tableInfo:
            if type(tableInfo[table]) is not dict:
                continue
            if tableInfo[table]["id"] == id:
                closable = table
                break
        if closable == "":
            cmd_mention = self.client.getCommandMention("table admin list")
            await itx.response.send_message(f"This id wasn't valid, thus couldn't close this table (for a list of tables, use {cmd_mention})!",ephemeral=True)
            return
        warning = ""
        if tableInfo[closable]["status"] == "new":
            warning += "This table is already closed... Closing anyway, I guess.\n"
        # remove every member and the owner from the table
        removedPeople = []
        ownerRole = discord.utils.find(lambda r: r.id == tableInfo[closable]["owner"], itx.guild.roles)
        for member in ownerRole.members:
            await member.remove_roles(ownerRole)
            removedPeople.append(f"{member.name or member.nick} ({member.id})")
        try:
            memberRole = discord.utils.find(lambda r: r.id == tableInfo[closable]["member"], itx.guild.roles)
            for member in memberRole.members:
                await member.remove_roles(memberRole)
                removedPeople.append(f"{member.name or member.nick} ({member.id})")
        except TypeError:
            debug(f"Tried to remove all members from table {tableInfo[closable]['id']}, but there were none maybe?",color="yellow")

        collection.update_one(query, {"$set":{f"{closable}.status":"new"}}, upsert=True)
        # tableInfo[closable]["status"] = "new"
        # send update message in table chat
        category = discord.utils.find(lambda r: r.id == tableInfo[closable]["category"], itx.guild.categories)
        channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
        await channel.send(f"Removed users from table: {', '.join(removedPeople)}\nThis table was forcibly closed by a staff member. A new table can be created now.")
        await self.tablemsgupdate(itx)
        await itx.response.send_message(warning+"Closed successfully",ephemeral=True)

    @admin.command(name="destroy",description="Remove a table from the table system")
    @app_commands.describe(id="Give the table a number: \"1\" for \"Table 1\", eg.")
    async def destroy(self, itx: discord.Interaction, id: str):
        if not isStaff(itx):
            await itx.response.send_message("You do not have permission to delete a table",ephemeral=True)
            return

        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find_one(query)
        if tableInfo is None:
            cmd_mention = self.client.getCommandMention("table admin build")
            await itx.response.send_message(f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention}!",ephemeral=True)
            return

        for tableId in tableInfo:
            if type(tableInfo[tableId]) is not dict:
                continue
            if tableInfo[tableId]["id"] == id:
                collection.update_one(query, {"$unset":{f"{tableId}":""}}, upsert=True)
                await itx.response.send_message(f"(╯°□°）╯︵ ┻━┻ Destroyed table {id} successfully. Happy now? ")
                await self.tablemsgupdate(itx)
                return

        await itx.response.send_message(f"Finished command without any action, thus the id was likely incorrect",ephemeral=True)

    @app_commands.command(name="lock",description="Lock your table, so no new players can join.")
    async def tableLock(self, itx: discord.Interaction):
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find_one(query)
        if tableInfo is None:
            cmd_mention = self.client.getCommandMention("table admin build")
            await itx.response.send_message(f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention}!",ephemeral=True)
            return
        lockable = ""
        if "message" not in tableInfo:
            await itx.response.send_message("There is no table message to update, thus I'm afraid you can't lock your table..",ephemeral=True)
            return
        for table in tableInfo:
            if type(tableInfo[table]) is not dict:
                continue
            for role in itx.user.roles:
                if role.id == tableInfo[table]["owner"]:
                    lockable = table
            if lockable:
                break
        if lockable == "":
            await itx.response.send_message("You aren't a table owner, thus can't lock this table!",ephemeral=True)
            await self.tablemsgupdate(itx)
            return
        collection.update_one(query, {"$set":{f"{lockable}.status":"locked"}}, upsert=True)

        # send update message in table chat
        category = discord.utils.find(lambda r: r.id == tableInfo[lockable]["category"], itx.guild.categories)
        channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
        cmd_mention = self.client.getCommandMention("table unlock")
        await channel.send(f"This table was locked by the table owner. No new players can join the table anymore.\nUse {cmd_mention} as table owner to open the table again.")
        await self.tablemsgupdate(itx)
        await itx.response.send_message("Locked successfully",ephemeral=True)

    @app_commands.command(name="unlock",description="Unlock your table, so new players can join again.")
    async def tableUnlock(self, itx: discord.Interaction):
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find_one(query)
        if tableInfo is None:
            cmd_mention = self.client.getCommandMention("table admin build")
            await itx.response.send_message(f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention}!",ephemeral=True)
            return
        unlockable = ""
        if "message" not in tableInfo:
            await itx.response.send_message("There is no table message to update, thus I'm afraid you can't lock your table..",ephemeral=True)
            return
        for table in tableInfo:
            if type(tableInfo[table]) is not dict:
                continue
            for role in itx.user.roles:
                if role.id == tableInfo[table]["owner"]:
                    unlockable = table
            if unlockable:
                break
        if unlockable == "":
            await itx.response.send_message("You aren't a table owner, thus can't unlock this table!",ephemeral=True)
            return

        collection.update_one(query, {"$set":{f"{unlockable}.status":"open"}}, upsert=True)

        # send update message in table chat
        category = discord.utils.find(lambda r: r.id == tableInfo[unlockable]["category"], itx.guild.categories)
        channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
        cmd_mention = self.client.getCommandMention("table lock")
        await channel.send(f"This table was unlocked by the table owner. Players can join the table again.\nUse {cmd_mention} as table owner to lock the table.")
        await self.tablemsgupdate(itx)
        await itx.response.send_message("Unlocked successfully",ephemeral=True)

    @app_commands.command(name="close",description="Close your table, a new group can start.")
    async def tableClose(self, itx: discord.Interaction):
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find_one(query)
        if tableInfo is None:
            cmd_mention = self.client.getCommandMention("table admin build")
            await itx.response.send_message(f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention}!",ephemeral=True)
            return
        closable = ""
        if "message" not in tableInfo:
            await itx.response.send_message("There is no table message to update, thus I'm afraid you can't close your table..",ephemeral=True)
            return
        for table in tableInfo:
            if type(tableInfo[table]) is not dict:
                continue
            for role in itx.user.roles:
                if role.id == tableInfo[table]["owner"]:
                    closable = table
            if closable:
                break
        if closable == "":
            await itx.response.send_message("You aren't a table owner, thus can't close this table!",ephemeral=True)
            return
        # remove every member and the owner from the table
        removedPeople = []
        ownerRole = discord.utils.find(lambda r: r.id == tableInfo[closable]["owner"], itx.guild.roles)
        for member in ownerRole.members:
            await member.remove_roles(ownerRole)
            removedPeople.append(f"{member.name or member.nick} ({member.id})")
        try:
            memberRole = discord.utils.find(lambda r: r.id == tableInfo[closable]["member"], itx.guild.roles)
            for member in memberRole.members:
                await member.remove_roles(memberRole)
                removedPeople.append(f"{member.name or member.nick} ({member.id})")
        except TypeError:
            debug(f"Tried to remove all members from table {tableInfo[closable]['id']}, but there were none maybe?",color="yellow")

        collection.update_one(query, {"$set":{f"{closable}.status":"new"}}, upsert=True)
        # send update message in table chat
        category = discord.utils.find(lambda r: r.id == tableInfo[closable]["category"], itx.guild.categories)
        channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
        await channel.send(f"Removed users from table: {', '.join(removedPeople)}\nThis table was closed by the table owner. A new table can be created now.")
        await self.tablemsgupdate(itx)
        await itx.response.send_message("Closed successfully",ephemeral=True)

    @app_commands.command(name="newowner",description="Transfer your ownership, in case you'd want someone else to have it instead.")
    @app_commands.describe(user="Mention the user who you want to become the new owner.")
    async def tableNewOwner(self, itx: discord.Interaction, user: discord.Member):
        query = {"guild_id": itx.guild_id}
        collection = RinaDB["tableInfo"]
        tableInfo = collection.find_one(query)
        if tableInfo is None:
            cmd_mention = self.client.getCommandMention("table admin build")
            await itx.response.send_message(f"Not enough data is configured to do this action! Please ask an admin to fix this with {cmd_mention}!",ephemeral=True)
            return
        transfer = ""
        for table in tableInfo:
            if type(tableInfo[table]) is not dict:
                continue
            for role in itx.user.roles:
                if role.id == tableInfo[table]["owner"]:
                    transfer = table
            if transfer:
                break
        if transfer == "":
            await itx.response.send_message("You aren't a table owner, thus can't transfer your ownership of this table!",ephemeral=True)
            return
        if discord.utils.find(lambda r: r.id == tableInfo[transfer]["member"], user.roles) is None:
            await itx.response.send_message("To grant someone ownership, they must have joined the table first (have table member role)!",ephemeral=True)
            return
        # change owner roles
        ownerRole = discord.utils.find(lambda r: r.id == tableInfo[transfer]["owner"], itx.guild.roles)
        memberRole = discord.utils.find(lambda r: r.id == tableInfo[transfer]["member"], itx.guild.roles)
        for member in ownerRole.members:
            await member.add_roles(memberRole)
            await member.remove_roles(ownerRole)
        await user.add_roles(ownerRole)
        await user.remove_roles(memberRole)

        # send update message in table chat
        category = discord.utils.find(lambda r: r.id == tableInfo[transfer]["category"], itx.guild.categories)
        channel = discord.utils.find(lambda r: r.name == "chat", category.channels)
        await channel.send(f"This table's ownership was transferred from {itx.user.nick or itx.user.name} ({itx.user.id}) to {user.nick or user.name} ({user.id}).",allowed_mentions=discord.AllowedMentions.none())
        await itx.response.send_message(f"Ownership transferred successfully", allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)

    @app_commands.command(name="help", description="Get a bit of info about Table commands")
    async def help(self, itx: discord.Interaction):
        await itx.response.send_message(f"""This is a list of commands you can use for your table, as table owner:
{self.client.getCommandMention('table lock')} -- Stops people from joining your table
{self.client.getCommandMention('table unlock')} -- Lets new people join the table again
{self.client.getCommandMention('table close')} -- Removes the table role from everyone and closes the table
{self.client.getCommandMention('table newowner')} -- Give the table owner role to another player (you can't share it)
{self.client.getCommandMention('table admin')} (admin only commands): list,build,force_close,destroy,sendmsg\
""",ephemeral=True)

async def setup(client):
    # client.add_command("toneindicator")
    await client.add_cog(Table(client))

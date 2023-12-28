from Uncute_Rina import *
from import_modules import *

async def add_to_data(emoji_id, emoji_name, location, animated):
    collection = asyncRinaDB["emojistats"]
    query = {"id": emoji_id}
    data = await collection.find_one(query)
    if data is None:
        await collection.insert_one(query)

    if location == "message":
        location = "messageUsedCount"
    elif location == "reaction":
        location = "reactionUsedCount"
    else:
        raise ValueError("Cannot add to database since the location of the reaction isn't defined correctly.")

    #increment the usage of the emoji in the dictionary, depending on where it was used (see $location above)
    await collection.update_one(query, {"$inc" : {location:1}} , upsert=True)
    await collection.update_one(query, {"$set":{"lastUsed": mktime(datetime.now(timezone.utc).timetuple()) , "name":emoji_name, "animated":animated}}, upsert=True)
    # collection.update_one( query, {"$set":{"name":emojiName}})
    #debug(f"Successfully added new data for {emojiID} as {location.replace('UsedCount','')}",color="blue")


class EmojiStats(commands.Cog):
    def __init__(self, client: Bot):
        global asyncRinaDB
        asyncRinaDB = client.asyncRinaDB
        self.client = client

    emojistats = app_commands.Group(name='emojistats', description='Get information about emoji usage in messages and reactions')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        emojis = []
        start_index = 0
        animated = None
        while True:
            emoji = re.search("<a?:[a-zA-Z_0-9]+:[0-9]+>", message.content[start_index:])
            if emoji is None:
                break
            sections = emoji.group().split(":")
            id = sections[2][:-1]
            name = sections[1]
            animated = (sections[0] == "<a")
            if not any(id in emojiList for emojiList in emojis):
                emojis.append([id,name])
            start_index += emoji.span()[1] # (11,29) for example


        for emoji in emojis:
            assert animated is not None
            await add_to_data(emoji[0], emoji[1], "message", animated)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        if reaction.emoji.id is not None:
            await add_to_data(str(reaction.emoji.id), reaction.emoji.name, "reaction", reaction.emoji.animated)

    @emojistats.command(name="getemojidata",description="Get emoji usage data from an ID!")
    @app_commands.rename(emoji_name="emoji")
    @app_commands.describe(emoji_name="Emoji you want to get data of")
    async def get_emoji_data(self, itx: discord.Interaction, emoji_name: str):
        if ":" in emoji_name:
            emoji_name = emoji_name.split(":")[2][:-1]
        emoji_id = emoji_name
        if not emoji_id.isdecimal():
            await itx.response.send_message("You need to fill in the ID of the emoji. This ID can't contain other characters. Only numbers.",ephemeral=True)
            return

        collection = asyncRinaDB["emojistats"]
        query = {"id": emoji_id}
        emoji = await collection.find_one(query)
        if emoji is None:
            await itx.response.send_message("That emoji doesn't have data yet. It hasn't been used since we started tracking the data yet. (<t:1660156260:R>, <t:1660156260:F>)", ephemeral=True)
            return

        msg_used = emoji.get('messageUsedCount',0)
        reaction_used = emoji.get('reactionUsedCount',0)
        animated = emoji.get('animated',False)
        # try:
        #     animated = emoji['animated']
        # except KeyError:
        #     animated = False

        emoji_search = ('a'*animated)+":"+emoji["name"]+":"+emoji["id"]
        emote = discord.PartialEmoji.from_str(emoji_search)

        await itx.response.send_message(f"Data for {emote}"+f"  ({emote})\n".replace(':','\\:') +
                                        f"messageUsedCount: {msg_used}\n" +
                                        f"reactionUsedCount: {reaction_used}\n" +
                                        f"Animated: {animated}\n" +
                                        f"Last used: {datetime.utcfromtimestamp(emoji['lastUsed']).strftime('%Y-%m-%d (yyyy-mm-dd) at %H:%M:%S')}",ephemeral=True)

    @emojistats.command(name="getunusedemojis",description="Get the least-used emojis")
    @app_commands.describe(hidden="Do you want everyone in this channel to be able to see this result?",
                           max_results="How many emojis do you want to retrieve at most? (may return fewer)",
                           used_max="Up to how many times may the emoji have been used? (= min_msg + min_react)(default: 5)",
                           msg_max="Up to how many times may the emoji have been used in a message? (default: 5)",
                           react_max="Up to how many times may the emoj have been used as a reaction? (default: 5)",
                           animated="Are you looking for animated emojis or static emojis")
    @app_commands.choices(animated=[
        discord.app_commands.Choice(name='Animated emojis', value=1),
        discord.app_commands.Choice(name='Static/Image emojis', value=2),
        discord.app_commands.Choice(name='Both', value=3)
    ])
    async def get_unused_emojis(self,itx: discord.Interaction, hidden: bool = True, max_results:int = 10, used_max:int = 5, msg_max:int = 5, react_max:int = 5, animated:int = 3):
        if not is_staff(itx):
            await itx.response.send_message("Due to the amount of database calls required, perhaps it's better not to make this publicly available. You can make use of /getemojidata and /getemojitop10 though :D", ephemeral=True)
            return
        await itx.response.send_message("This might take a while (\"Rina is thinking...\")\nThis message will be edited when it has found a few unused emojis (both animated and non-animated)",ephemeral=hidden)

        if max_results > 50:
            max_results = 50
        if used_max < 0:
            used_max = 0
        if msg_max < 0:
            msg_max = 0
        if react_max < 0:
            react_max = 0

        unused_emojis = []
        for emoji in itx.guild.emojis:
            if emoji.animated and (animated == 2):
                continue
            if (not emoji.animated) and animated == 1:
                continue

            collection = asyncRinaDB["emojistats"]
            query = {"id": str(emoji.id)}
            emojidata = await collection.find_one(query)
            if emojidata is None:
                unused_emojis.append(f"<{'a'*emoji.animated}:{emoji.name}:{emoji.id}> (0,0)")
                continue

            msg_used = emojidata.get('messageUsedCount',0)
            reaction_used = emojidata.get('reactionUsedCount',0)
            if (msg_used + reaction_used <= used_max) and (msg_used <= msg_max) and (reaction_used <= react_max):
                unused_emojis.append(f"<{'a'*emoji.animated}:{emoji.name}:{emoji.id}> ({msg_used},{reaction_used})")

            if len(unused_emojis) > max_results:
                break
            await asyncio.sleep(0)

        output = ', '.join(unused_emojis)
        if len(output) > 1850:
            output = output[:1850] + "\nShortened to be able to be sent."
        await itx.edit_original_response(content="These emojis have been used very little (x used in msg, x used as reaction):\n"+output)

    @emojistats.command(name="getemojitop10",description="Get top 10 most used emojis")
    async def get_emoji_top_10(self, itx: discord.Interaction):
        collection = asyncRinaDB["emojistats"]
        output = ""
        for type in ["messageUsedCount","reactionUsedCount"]:
            results = []
            async for emoji in collection.find({},limit=10,sort=[(type,pymongo.DESCENDING)]):
                animated = 0
                try:
                    animated = emoji['animated']
                    if animated:
                        animated = 1
                except KeyError:
                    pass

                emoji_full = "<"+("a"*animated)+":"+emoji["name"]+":"+emoji["id"]+">"
                try:
                    results.append(f"> **{emoji[type]}**: {emoji_full}")
                except KeyError:
                    # leftover emoji doesn't have a value for messageUsedCount or reactionUsedCount yet
                    pass
            output += "\nTop 10 for "+type.replace("UsedCount","")+"s:\n"
            output += '\n'.join(results)
        await itx.response.send_message(output,ephemeral=True)

class VCLogReader(commands.Cog):
    def __init__(self, client: Bot):
        global asyncRinaDB
        asyncRinaDB = client.asyncRinaDB
        self.client = client

    async def get_vc_activity(self, voice_log_channel: discord.abc.Messageable, min_time: int, max_time: int):
        """
        Retrieve the most recent voice channel activity from the logger channel and convert into neat string.

        ### Arguments:
        --------------
        voice_log_channel: :class:`discord.abc.Messageable`
            Channel from which you want to get the voice channel logs / information

        ### Returns:
        ------------
        `list[tuple[`event_time_unix, (user_id, username), (previous_channel_id, name) | None, (current_channel_id, name) | None `]]`
        """
        output: list[tuple[int, tuple[int, str], tuple[int, str] | None, tuple[int, str] | None]] = [] # list of [(username, user_id), (joined_channel_id), (left_channel_id)]
        count = 0

        async for message in voice_log_channel.history(before = datetime.fromtimestamp(max_time), 
                                                       after  = datetime.fromtimestamp(min_time)):
            # For context: the embed message sent by the Logger bot looks like this:
            #   author / image of user that sent message (author.name = username + descriminator (#0 in new discord update))
            #  case 1: the user joins/leaves a voice channel
            #   description: **username#0** joined/left voice channel vc_name
            #   fields[0].name: Channel
            #   fields[0].value: <#123456> (name)
            #   fields[1].name: ID
            #   fields[1].value: "```ini\nUser = 123456789\nChannel = 123456```"
            #  case 2: the user moves from one channel to another
            #   description: **username#0** moved from <#123456> (name1) to <#234567> (name2)
            #   fields[0].name: Current channel they are in    << New >>
            #   fields[0].value: <#234567> (name1)
            #   fields[0].name: Previously occupied channel    << Old >>
            #   fields[0].value: <#123456> (name2)
            #   fields[1].name: ID
            #   fields[1].value: "```ini\nUser = 123456789\nNew = 234567\nOld = 123456```"

            for embed in message.embeds[::-1]: # flip list because messages sort from newest to oldest whereas the embeds in these messages would sort from oldest to newest.
                data: tuple[int, tuple[int, str], tuple[int, str] | None, tuple[int, str] | None] = [] # yes i know this is a list. It is converted into a tuple later. I'm too lazy to make a second variable if this works too. (long live python?)
                data.append(int(mktime(embed.timestamp.timetuple()))) # unix timestamp of event
                username = embed.description.split("**",2)[1].split("#",1)[0] # split **mysticmia#0** to mysticmia (assumes discord usernames can't contain hashtags (which they can't))
                # print("Username = ", username)
                try:
                    type = embed.description.split("**",2)[2].split(" voice channel: ")[-2].split(") ")[-1].strip() # remove bold name and everything after the first word, to only select 'moved', 'joined', or 'left'
                    #  This transforms "**mysticmia#0** (Mia) joined voice channel: General.
                    #             into " (Mia) joined voice channel: General."
                    #             into " (Mia) joined"
                    #             into "joined"
                    # or, in the case there is no username: " joined", which is why you have to strip it too.
                except IndexError:
                    # this doesn't work if the user moved from one channel to another: 
                    #    "**mysticmia#0** (Mia) moved from ⁠〙 Quiet (〙 Quiet) to ⁠〙 General 2 (〙 General 2)."
                    #... honestly. i think it's probably safe to assume the user "moved" in this case. There isn't any fool-proof way to test otherwise
                    type = "moved"
                    # Will get an assertion error if it's not, anyway, so I'll leave it as it is for now.

                # print("Type = ", type)
                # print("Embed field count = ", len(embed.fields))
                user_data = []
                previous_channel_data = []
                current_channel_data = []

                # could be done more efficiently but oh well. Not like this is suitable for any other bot either anyway. And I'm limited by discord API anyway
                if len(embed.fields) == 3: # user moved channels (3 fields: previous/current channel, and IDs)
                    if type != "moved":
                        raise AssertionError(f"type '{type}' is not a valid type (should be 'moved')")
                    current_channel_data.append(embed.fields[0].value.split("#",1)[1].split(">",1)[0])           # split <#234567> (Channel Name) to 234567
                    current_channel_data.append(embed.fields[0].value.split(">",1)[1].split("(",1)[1][:-1])      # split <#234567> (Channel Name) to Channel Name
                    previous_channel_data.append(embed.fields[1].value.split("#",1)[1].split(">",1)[0])          # split <#123456> (Channel Name) to 123456
                    previous_channel_data.append(embed.fields[1].value.split(">",1)[1].split("(",1)[1][:-1])     # split <#123456> (Channel Name) to Channel Name
                elif len(embed.fields) == 2:
                    if type == "joined":
                        current_channel_data.append(embed.fields[0].value.split("#",1)[1].split(">",1)[0])       # split <#123456> (Channel Name) to 123456
                        current_channel_data.append(embed.fields[0].value.split(">",1)[1].split("(",1)[1][:-1])  # split <#123456> (Channel Name) to Channel Name
                    elif type == "left":
                        previous_channel_data.append(embed.fields[0].value.split("#",1)[1].split(">",1)[0])      # split <#234567> (Channel Name) to 234567
                        previous_channel_data.append(embed.fields[0].value.split(">",1)[1].split("(",1)[1][:-1]) # split <#234567> (Channel Name) to Channel Name
                    else:
                        raise AssertionError(f"type '{type}' is not a valid type (should be 'joined' or 'left')")
                else:
                    raise AssertionError(f"Embed fields count was expected to be 3 or 2. Instead, it was '{len(embed.fields)}'")

                
                id_data = embed.fields[-1].value.replace("```ini","")[:-3].strip() # remove the ```ini\n  ...   ``` from the embed field
                # print("id data = ", id_data)
                for line in id_data.splitlines():
                    key, value = line.split(" = ")
                    if key == "User": # could use match/case but it's not like as if it'll make much difference in speed or looks: extra indents- and discord API is bottleneck anyway
                        user_data.append(value)
                    elif key == "New":
                        current_channel_data.append(value)
                    elif key == "Old":
                        previous_channel_data.append(value)
                    elif key == "Channel":
                        if type == "joined":
                            current_channel_data.append(value)
                        elif type == "left":
                            previous_channel_data.append(value)
                        else:
                            raise AssertionError(f"type '{type}' is not a valid type (should be 'joined' or 'left')")
                    else:
                        raise AssertionError(f"key '{key}' is not a valid key (should be 'User', 'Old', 'New', or 'Channel')")
                user_data.append(username)
                
                try:
                    data.append((int(user_data[0]), user_data[1]))

                    if len(previous_channel_data) == 0:
                        data.append(None)
                    else:
                        data.append((int(previous_channel_data[0]), previous_channel_data[1]))

                    if len(current_channel_data) == 0:
                        data.append(None)
                    else:
                        data.append((int(current_channel_data[0]), current_channel_data[1]))
                except ValueError:
                    raise AssertionError(f"IDs were not numeric!\nFull error:\n{traceback.format_exc()}")
                output.append(tuple(data))

                # print()
                # print(f"author name: {embed.author.name}, author url: {embed.author.url}")
                # print(f"footer: {embed.footer}")
                # print(f"color: {embed.color}")
                # print(f"title: {embed.title}")
                # print(f"description: {embed.description}")
                # print(f"timestamp: {embed.timestamp}")
                # print(f"fields:")
                # for field in embed.fields:
                #     print(f"  field name: {field.name} (inline: {field.inline})")
                #     print(f"   field value: {field.value}")
                # print()
                # print("\n"*2)

                count+=1
                if count > 15:
                    break
            # if count > 3:
            #     break

        return output
            

    @app_commands.command(name="getvcdata", description="Get recent voice channel usage data.")
    async def get_voice_channel_data(self, itx: discord.Interaction, requested_channel: discord.VoiceChannel, lower_bound: str, upper_bound: str = None):
        if not is_staff(itx):
            await itx.response.send_message("You don't have permissions to use this command.", ephemeral=True)
            return
        cmd_mention = self.client.get_command_mention("editguildinfo")
        try:
            log_channel_id = await self.client.get_guild_info(itx.guild_id, "vcActivityLogChannel")
        except KeyError:
            await itx.response.send_message(f"Error: No log channel found! Set one with {cmd_mention} `mode:Edit` `option:51` `value:`.", ephemeral=True)
            return
        log_channel = self.client.get_channel(log_channel_id)
        if log_channel is None:
            await itx.response.send_message(f"Error: The given log channel id ({log_channel_id}) yielded no valid channels!", ephemeral=True)
            return
        
        if upper_bound is None:
            upper_bound = 0 # 0 minutes from now
        try:
            lower_bound = float(lower_bound)
            upper_bound = float(upper_bound)
            if lower_bound <= 0:
                await itx.response.send_message("Your period (data in the past [x] minutes) has to be above 0!",ephemeral=True)
                return
            # if lower_bound > 1000000:
            #     await itx.response.send_message("... I doubt you'll be needing to look 30 years into the past..",ephemeral=True)
            #     return
            if upper_bound > lower_bound:
                await itx.response.send_message("Your upper bound can't be bigger (-> longer ago) than the lower bound!", ephemeral=True)
                return
        except ValueError:
            await itx.response.send_message("Your bounding period has to be a number for the amount of minutes that have passed",ephemeral=True)
            return

        await itx.response.defer(ephemeral=True)
        
        accuracy = 0.0001#(lower_bound-upper_bound)*(60/36=1.66666667) #divide graph into 36 sections 
        lower_bound *= 60 # minutes to seconds
        upper_bound *= 60
        current_time = mktime(datetime.now().timetuple())
        # min_time = int((current_time-lower_bound)/accuracy)*accuracy
        # max_time = int((current_time-upper_bound)/accuracy)*accuracy
        min_time = current_time-lower_bound
        max_time = current_time-upper_bound
        
        events = await self.get_vc_activity(log_channel, min_time, max_time)

        # add fake "leave" event for every person that is currently still in the voice channel.
        # This ensures that even [those that haven't joined or left during the given time frame] will still be plotted on the graph.
        for member in requested_channel.members:
            events.append((current_time, (member.id, member.name), (requested_channel.id, requested_channel.name), None))

        intermediate_data: dict[int, int | None | list[int]] = {}

        for event in events:
            unix, user, from_channel, to_channel = event
            from_channel = from_channel[0] if from_channel else from_channel # set as its ID if not None (prevent TypeError: 'NoneType' object is not subscriptable)
            to_channel = to_channel[0] if to_channel else to_channel
            user_id = user[0]
            if requested_channel.id not in [from_channel, to_channel]:
                continue
            if user[0] not in intermediate_data:
                intermediate_data[user_id] = {"name":user[1], "time_temp":None, "timestamps":[]}

            if from_channel == requested_channel.id:
                if intermediate_data[user_id]["time_temp"] is None:
                    intermediate_data[user_id]["timestamps"].append((min_time, unix))
                else:
                    intermediate_data[user_id]["timestamps"].append((intermediate_data[user_id]["time_temp"], unix))
                    intermediate_data[user_id]["time_temp"] = None
            elif to_channel == requested_channel.id:
                intermediate_data[user_id]["time_temp"] = unix
        for user_id in intermediate_data:
            if intermediate_data[user_id]["time_temp"]:
                intermediate_data[user_id]["timestamps"].append((intermediate_data[user_id]["time_temp"], max_time))
            del intermediate_data[user_id]["time_temp"]

        data: dict[str, list[str | int]] = {"User":[],"Start":[],"Finish":[]}
        for user in intermediate_data:
            for time_tuple in intermediate_data[user]["timestamps"]:
                data["User"].append(intermediate_data[user]["name"])
                data["Start"].append(time_tuple[0])
                data["Finish"].append(time_tuple[1])

        # print("\n\nEvents:\n  ", events,
        #       "\n\nIntermediate data:\n  ", intermediate_data, 
        #       "\n\nData:\n  ", data)

        df = pd.DataFrame(data=data)
        df["Diff"] = df.Finish - df.Start

        color = "crimson"
        fig,ax=plt.subplots(figsize=(6,3))
        fig.suptitle(f"VC data in '{requested_channel.id}' from T-{lower_bound/60} to T-{upper_bound/60}")

        labels=[]
        for i, task in enumerate(df.groupby("User")):
            labels.append(task[0])
            # for r in task[1].groupby("Resource"):
            #     data = r[1][["Start", "Diff"]]
            #     ax.broken_barh(data.values, (i-0.4,0.8), color=color )
            data = task[1][["Start", "Diff"]]
            ax.broken_barh(data.values, (i-0.4,0.8), color=color )

        ax.set_xticks(ax.get_xticks()) # workaround to remove upcoming warning (warning about changing labels without preventing potential overlaps)

        tick_labels = [x.get_position()[0] for x in ax.xaxis.get_ticklabels()]
        label_time_text_format = "%H:%M"
        if tick_labels[-1] - tick_labels[0] < 5*60:
            label_time_text_format = "%H:%M:%S"
        elif tick_labels[-1] - tick_labels[0] > 86400:
            label_time_text_format = "%Y-%m-%dT%H:%M"
        ax.set_xticklabels([datetime.fromtimestamp(x).strftime(label_time_text_format) for x in tick_labels], rotation=30)

        # plt.xticks(tick_loc, tick_disp, rotation='vertical')
        # plt.setp(tick_disp, rotation=45, horizontalalignment='right')
        # ax.set_xticks(tick_loc,
        #               labels=tick_disp,
        #               horizontalalignment='right',
        #               minor=False,
        #               rotation=30)
        # xfmt = md.DateFormatter('%H:%M')
        # ax.xaxis.set_major_formatter(xfmt)
        
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)
        ax.set_xlabel("time (utc+0)")
        plt.tight_layout()
        #plt.show()
        plt.savefig('vcLogs.png', dpi=300)
        await itx.followup.send(f"VC activity from {requested_channel.mention} (`{requested_channel.id}`) from {lower_bound/60} to {upper_bound/60} minutes ago ({(lower_bound - upper_bound) / 60} minutes)",file=discord.File('vcLogs.png'))

        # id_pages = []
        # name_pages = []
        # ITEMS_PER_PAGE = 10
        # embed_color = 8481900
        # for i in range(ceil(len(data) / ITEMS_PER_PAGE)):
        #     result_id_page = ""
        #     result_name_page = ""
        #     for section in data[0 + ITEMS_PER_PAGE * i : ITEMS_PER_PAGE + ITEMS_PER_PAGE * i]:
        #         event_unix, user_data, previous_channel, current_channel = section
        #         if previous_channel and current_channel:
        #             result_id_page += f"<t:{event_unix}:d> <t:{event_unix}:t>- '{user_data[1]}' moved from '{previous_channel[1]}' to '{current_channel[1]}'\n"
        #             result_name_page += f"<t:{event_unix}:d> <t:{event_unix}:t>- '{user_data[0]}' moved from '{previous_channel[0]}' to '{current_channel[0]}'\n"
        #         if previous_channel:
        #             result_id_page += f"<t:{event_unix}:d> <t:{event_unix}:t>- '{user_data[1]}' left '{previous_channel[1]}'\n"
        #             result_name_page += f"<t:{event_unix}:d> <t:{event_unix}:t>- '{user_data[0]}' left '{previous_channel[0]}'\n"
        #         if current_channel:
        #             result_id_page += f"<t:{event_unix}:d> <t:{event_unix}:t>- '{user_data[1]}' joined '{current_channel[1]}'\n"
        #             result_name_page += f"<t:{event_unix}:d> <t:{event_unix}:t>- '{user_data[0]}' joined '{current_channel[0]}'\n"
        #     id_pages.append(result_id_page)
        #     name_pages.append(result_name_page)
        # page = 0
        #
        # # class LogPager(discord.ui.View):
        # #     def __init__(self, id_pages: list, name_pages: list, embed_title, timeout=None):
        # #         super().__init__()
        # #         self.value       = None
        # #         self.embed_title = embed_title
        # #         self.timeout     = timeout
        # #         self.page        = 0
        # #         self.id_pages    = id_pages
        # #         self.name_pages  = name_pages
        # #         self.pages_type_names = False # True if self.pages == self.name_pages
        # #         self.pages = self.id_pages
        # #
        # #     @discord.ui.button(label='Previous', style=discord.ButtonStyle.blurple)
        # #     async def previous(self, itx: discord.Interaction, _button: discord.ui.Button):
        # #         # self.value = "previous"
        # #         self.page -= 1
        # #         if self.page < 0:
        # #             self.page = len(self.pages)-1
        # #         result_page = self.pages[self.page]
        # #         embed = discord.Embed(color=embed_color, title=self.embed_title, description=result_page)
        # #         embed.set_footer(text="page: " + str(self.page+1) + " / " + str(len(self.pages)))
        # #         await itx.response.edit_message(embed=embed)
        # #
        # #     @discord.ui.button(label='Next', style=discord.ButtonStyle.blurple)
        # #     async def next(self, itx: discord.Interaction, _button: discord.ui.Button):
        # #         self.page += 1
        # #         if self.page >= len(self.pages):
        # #             self.page = 0
        # #         result_page = self.pages[self.page]
        # #         embed = discord.Embed(color=embed_color, title=self.embed_title, description=result_page)
        # #         embed.set_footer(text="page: " + str(self.page+1) + " / " + str(len(self.pages)))
        # #         await itx.response.edit_message(embed=embed)
        # #
        # #     @discord.ui.button(label='Convert IDs / names', style=discord.ButtonStyle.gray)
        # #     async def convert_ids(self, itx: discord.Interaction, _button: discord.ui.Button):
        # #         if self.pages_type_names: # currently displaying names
        # #             self.pages = self.id_pages
        # #         else: # currently displaying IDs
        # #             self.pages = self.name_pages
        # #         self.pages_type_names = not self.pages_type_names # True if self.pages == self.name_pages
        # #
        # #         result_page = self.pages[self.page]
        # #         embed = discord.Embed(color=embed_color, title=self.embed_title, description=result_page)
        # #         embed.set_footer(text="page: " + str(self.page+1) + " / " + str(len(self.pages)))
        # #         await itx.response.edit_message(embed=embed)
        #
        # result_id_page = id_pages[page]
        # embed_title = f'Recent voice channel logs'
        # embed = discord.Embed(color=embed_color, title=embed_title)
        # embed.add_field(name="Column 1",value=result_id_page, inline=False)
        # embed.set_footer(text="page: " + str(page+1) + " / " + str(len(id_pages)))
        # view = LogPager(id_pages, name_pages, embed_title, timeout=180)
        # await itx.followup.send(f"", embed=embed, view=view, ephemeral=True)
        # await view.wait()
        # if view.value is None:
        #     await itx.edit_original_response(view=None)







async def setup(client):
    # client.add_command(getMemberData)
    await client.add_cog(EmojiStats(client))
    await client.add_cog(VCLogReader(client))

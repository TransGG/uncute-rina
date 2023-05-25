from Uncute_Rina import *
from import_modules import *

async def add_to_data(member, type):
    collection = asyncRinaDB["data"]
    query = {"guild_id": member.guild.id}
    data = await collection.find_one(query)
    if data is None:
        await collection.insert_one(query)
        data = await collection.find_one(query)

    try:
        #see if this user already has data, if so, add a new joining time to the list
        data[type][str(member.id)].append(mktime(datetime.now(timezone.utc).timetuple()))
    except IndexError:
        data[type][str(member.id)] = [mktime(datetime.now(timezone.utc).timetuple())]
    except KeyError:
        data[type] = {}
        data[type][str(member.id)] = [mktime(datetime.now(timezone.utc).timetuple())]
    await collection.update_one(query, {"$set":{f"{type}.{member.id}":data[type][str(member.id)]}}, upsert=True)
    #debug(f"Successfully added new data for {member.name} to {repr(type)}",color="blue")

class MemberData(commands.Cog):
    def __init__(self, client: Bot):
        global asyncRinaDB
        self.client = client
        asyncRinaDB = client.asyncRinaDB

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await add_to_data(member, "joined")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await add_to_data(member, "left")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        role = discord.utils.find(lambda r: r.name == 'Verified', before.guild.roles)
        if role not in before.roles and role in after.roles:
            await add_to_data(after, "verified")

    @app_commands.command(name="getmemberdata",description="See joined, left, and recently verified users in x days")
    @app_commands.describe(upper_bound="Get data from [period] days ago",
                           doubles="If someone joined twice, are they counted double? (y/n or 1/0)")
    async def get_member_data(self, itx: discord.Interaction, lower_bound: str, upper_bound: str = None, doubles: bool = False, public: bool = False):
        # if not is_staff(itx):
        #     await itx.response.send_message("You don't have the right role to be able to execute this command! (sorrryyy)",ephemeral=True)
        #     return
        if upper_bound is None:
            upper_bound = 0 # 0 days from now
        try:
            lower_bound = float(lower_bound)
            upper_bound = float(upper_bound)
            if lower_bound <= 0:
                await itx.response.send_message("Your period (data in the past [x] days) has to be above 0!",ephemeral=True)
                return  
            # if period < 0.035:
            #     await itx.response.send_message("Idk why but it seems to break when period is smaller than 0.0035, so better not use it.", ephemeral=True)
            #     return #todo: figure out why you can't fill in less than 0.0035: ValueError: All arrays must be of the same length
            if lower_bound > 10958:
                await itx.response.send_message("... I doubt you'll be needing to look 30 years into the past..",ephemeral=True)
                return
            if upper_bound > lower_bound:
                await itx.response.send_message("Your upper bound can't be bigger (-> more days ago) than the lower bound!", ephemeral=True)
                return
        except ValueError:
            await itx.response.send_message("Your period has to be an integer for the amount of days that have passed",ephemeral=True)
            return

        accuracy = (lower_bound-upper_bound)*2400 #divide graph into 36 sections
        lower_bound *= 86400 # days to seconds
        upper_bound *= 86400
        # Get a list of people (in this server) that joined at certain times. Maybe round these to a certain factor (don't overstress the x-axis)
        # These certain times are in a period of "now" and "[period] seconds ago"
        totals = {}
        results = {}
        warning = ""
        current_time = mktime(datetime.now(timezone.utc).timetuple())
        min_time = int((current_time-lower_bound)/accuracy)*accuracy
        max_time = int((current_time-upper_bound)/accuracy)*accuracy

        collection = asyncRinaDB["data"]
        query = {"guild_id": itx.guild_id}
        data = await collection.find_one(query)
        if data is None:
            await itx.response.send_message("Not enough data is configured to do this action! Please hope someone joins sometime soon lol",ephemeral=True)
            return
        await itx.response.defer(ephemeral = not public)

        # gather timestamps in timeframe, as well as the lowest and highest timestamps
        for y in data:
            if type(data[y]) is not dict:
                continue
            column = []
            results[y] = {}
            for member in data[y]:
                for time in data[y][member]:
                    #if the current time minus the amount of seconds in every day in the period since now, is still older than more recent joins, append it
                    if current_time-lower_bound < time:
                        if current_time-upper_bound > time:
                            column.append(time)
                            if not doubles:
                                break
            await asyncio.sleep(0.1) # allow heartbeat or recognising other commands
            totals[y] = len(column)
            for time in range(len(column)):
                column[time] = int(column[time]/accuracy)*accuracy
                if column[time] in results[y]:
                    results[y][column[time]] += 1
                else:
                    results[y][column[time]] = 1
            await asyncio.sleep(0.1) # allow heartbeat or recognising other commands
            if len(column) == 0:
                warning += f"\nThere were no '{y}' users found for this time period."
                results[y] = {}
                #debug(warning[1:],color="light purple")
            else:
                time_list = sorted(column)
                if min_time > time_list[0]:
                    min_time = time_list[0]
                if max_time < time_list[-1]:
                    max_time = time_list[-1]
        
        # if the lowest timestamps are lower than the lowest timestamp, then set all missing data to 0 (up until the graph has data)        
        min_time_db = min_time
        for y in data:
            if type(data[y]) is not dict:
                continue
            min_time = min_time_db
            while min_time <= max_time:
                if min_time not in results[y]:
                    results[y][min_time] = 0
                min_time += accuracy
        
        for i in results: # sort data by key
            results[i] = {timestamp: results[i][timestamp] for timestamp in sorted(results[i])}
        
        await asyncio.sleep(0.1) # allow heartbeat or recognising other commands

        # make graph
        try:
            d = {
                "time": [i for i in results["joined"]],
            }
            for y in results:
                try:
                    d[y]= [results[y][i] for i in results[y]]
                except KeyError as ex:
                    # await itx.followup.send(f"{ex} did not have data, thus could not make the graph.")
                    # return
                    continue
            df = pd.DataFrame(data=d)
            fig, (ax1) = plt.subplots()#1, 1)
            fig.suptitle(f"Member data from {lower_bound/86400} to {upper_bound/86400} days ago")
            fig.tight_layout(pad=1.0)
            color = {
                "joined":"g",
                "left":"r",
                "verified":"b"
            }
            for graph in df:
                if graph == "time":
                    continue
                ax1.plot(df['time'], df[graph], color[graph], label=graph)
            ax1.legend()
            if doubles:
                re_text = "inc"
            else:
                re_text = "exc"
            ax1.set_ylabel(f"# of members ({re_text}. rejoins/-leaves/etc)")

            tick_loc = [i for i in df['time'][::3]]
            if (lower_bound-upper_bound)/86400 <= 1:
                tick_disp = [datetime.fromtimestamp(i).strftime('%H:%M') for i in tick_loc]
            else:
                tick_disp = [datetime.fromtimestamp(i).strftime('%Y-%m-%dT%H:%M') for i in tick_loc]


            # plt.xticks(tick_loc, tick_disp, rotation='vertical')
            # plt.setp(tick_disp, rotation=45, horizontalalignment='right')
            ax1.set_xticks(tick_loc,
                           labels=tick_disp,
                           horizontalalignment='right',
                           minor=False,
                           rotation=30)
            ax1.grid(visible=True, which='major', axis='both')
            fig.subplots_adjust(bottom=0.180, top=0.90, left=0.1, hspace=0.1)
            plt.savefig('userJoins.png', dpi=300)
        except ValueError:
            await itx.followup.send("You encountered a ValueError! Mia has been sent an error report to hopefully be able to fix it :)",ephemeral=True)
            raise
        output = ""
        try:
            output += f"`{totals['joined']}` members joined, "
        except:
            pass
        try:
            output += f"`{totals['left']}` members left, "
        except:
            pass
        try:
            output += f"`{totals['verified']}` members were verified."
        except:
            pass
        await itx.followup.send(f"From {lower_bound/86400} to {upper_bound/86400} days ago, {output} (with{'out'*(1-doubles)} doubles)"+warning,file=discord.File('userJoins.png'))

async def setup(client):
    # client.add_command(getMemberData)
    await client.add_cog(MemberData(client))

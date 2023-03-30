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
    @app_commands.describe(period="Get data from [period] days ago",
                           doubles="If someone joined twice, are they counted double? (y/n or 1/0)")
    async def get_member_data(self, itx: discord.Interaction, period: str, doubles: bool = False, hidden: bool = True):
        # if not isStaff(itx):
        #     await itx.response.send_message("You don't have the right role to be able to execute this command! (sorrryyy)",ephemeral=True)
        #     return
        try:
            period = float(period)
            if period <= 0:
                await itx.response.send_message("Your period (data in the past [x] days) has to be above 0!",ephemeral=True)
                return
            # if period < 0.035:
            #     await itx.response.send_message("Idk why but it seems to break when period is smaller than 0.0035, so better not use it.", ephemeral=True)
            #     return #todo: figure out why you can't fill in less than 0.0035: ValueError: All arrays must be of the same length
            if period > 10958:
                await itx.response.send_message("... I doubt you'll be needing to look 30 years into the past..",ephemeral=True)
                return
        except ValueError:
            await itx.response.send_message("Your period has to be an integer for the amount of days that have passed",ephemeral=True)
            return

        accuracy = period*2400 #divide graph into 36 sections
        period *= 86400 # days to seconds
        # Get a list of people (in this server) that joined at certain times. Maybe round these to a certain factor (don't overstress the x-axis)
        # These certain times are in a period of "now" and "[period] seconds ago"
        totals = {}
        results = {}
        warning = ""
        current_time = mktime(datetime.now(timezone.utc).timetuple())
        min_time = int((current_time-period)/accuracy)*accuracy
        max_time = int(current_time/accuracy)*accuracy

        collection = asyncRinaDB["data"]
        query = {"guild_id": itx.guild_id}
        data = await collection.find_one(query)
        if data is None:
            await itx.response.send_message("Not enough data is configured to do this action! Please hope someone joins sometime soon lol",ephemeral=True)
            return
        await itx.response.defer(ephemeral=hidden)

        for y in data:
            if type(data[y]) is not dict:
                continue
            column = []
            results[y] = {}
            for member in data[y]:
                for time in data[y][member]:
                    #if the current time minus the amount of seconds in every day in the period since now, is still older than more recent joins, append it
                    if current_time-period < time:
                        column.append(time)
                        if not doubles:
                            break
            totals[y] = len(column)
            for time in range(len(column)):
                column[time] = int(column[time]/accuracy)*accuracy
                if column[time] in results[y]:
                    results[y][column[time]] += 1
                else:
                    results[y][column[time]] = 1
            if len(column) == 0:
                warning += f"\nThere were no '{y}' users found for this time period."
                #debug(warning[1:],color="light purple")
            else:
                time_list = sorted(column)
                if min_time > time_list[0]:
                    min_time = time_list[0]
                if max_time < time_list[-1]:
                    max_time = time_list[-1]
        min_time_db = min_time
        for y in data:
            if type(data[y]) is not dict:
                continue
            min_time = min_time_db
            while min_time <= max_time:
                if min_time not in results[y]:
                    results[y][min_time] = 0
                min_time += accuracy
        result = {}
        for i in results:
            result[i] = {}
            for j in sorted(results[i]):
                result[i][j] = results[i][j]
            results[i] = result[i]
        try:
            try:
                d = {
                    "time": [i for i in results["joined"]],
                    "joined":[results["joined"][i] for i in results["joined"]],
                    "left":[results["left"][i] for i in results["left"]],
                    "verified":[results["verified"][i] for i in results["verified"]]
                }
            except KeyError as ex:
                await itx.followup.send(f"{ex} did not have data, thus could not make the graph.")
                return
            df = pd.DataFrame(data=d)
            fig, (ax1) = plt.subplots()#1, 1)
            fig.suptitle(f"Member +/-/verif (r/g/b) in the past {period/86400} days")
            fig.tight_layout(pad=1.0)
            ax1.plot(df['time'], df["joined"], 'r')
            ax1.plot(df['time'], df["left"], 'g')
            ax1.plot(df['time'], df["verified"], 'b')
            if doubles:
                re_text = "exc"
            else:
                re_text = "inc"
            ax1.set_ylabel(f"# of members ({re_text}. rejoins/-leaves/etc)")

            tick_loc = [i for i in df['time'][::3]]
            if period/86400 <= 1:
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
            plt.savefig('userJoins.png')
        except ValueError:
            await itx.followup.send("You encountered an error! This is likely a ValueError, caused by a too small number. "
                                    "I still have to figure out why this happens, exactly. Probably some rounding error or something. "
                                    "Anyway, try a larger number, it might work better",ephemeral=True)
        await itx.followup.send(f"In the past {period/86400} days, `{totals['joined']}` members joined, `{totals['left']}` left, and `{totals['verified']}` were verified. (with{'out'*(1-doubles)} doubles)"+warning,file=discord.File('userJoins.png'))

async def setup(client):
    # client.add_command(getMemberData)
    await client.add_cog(MemberData(client))

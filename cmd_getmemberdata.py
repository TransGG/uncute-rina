import discord # It's dangerous to go alone! Take this. /ref
from discord import app_commands # v2.0, use slash commands
from discord.ext import commands # required for client bot making
from utils import *
from datetime import datetime, timedelta
from time import mktime # for unix time code

import pymongo # for online database
from pymongo import MongoClient
mongoURI = open("mongo.txt","r").read()
cluster = MongoClient(mongoURI)
RinaDB = cluster["Rina"]

class MemberData(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def addToData(self, member, type):
        collection = RinaDB["data"]
        query = {"guild_id": member.guild.id}
        data = collection.find(query)
        try:
            data = data[0]
        except IndexError:
            collection.insert_one(query)
            data = collection.find(query)[0]
        try:
            #see if this user already has data, if so, add a new joining time to the list
            data[type][str(member.id)].append(mktime(datetime.utcnow().timetuple()))
        except IndexError:
            data[type][str(member.id)] = [mktime(datetime.utcnow().timetuple())]
        except KeyError:
            data[type] = {}
            data[type][str(member.id)] = [mktime(datetime.utcnow().timetuple())]
        collection.update_one(query, {"$set":{f"{type}.{member.id}":data[type][str(member.id)]}}, upsert=True)
        # print("Successfully added new data to "+repr(type))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await addToData(member,"joined")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await addToData(member,"left")

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        role = discord.utils.find(lambda r: r.name == 'Verified', before.guild.roles)
        if role not in before.roles and role in after.roles:
            await addToData(after,"verified")

    @app_commands.command(name="getmemberdata",description="See joined, left, and recently verified users in x days")
    @app_commands.describe(period="Get data from [period] days ago",
                           doubles="If someone joined twice, are they counted double? (y/n or 1/0)")
    async def getMemberData(self, itx: discord.Interaction, period: str, doubles: str = "false"):
        if not isStaff(itx):
            await itx.response.send_message("You don't have the right role to be able to execute this command! (sorrryyy)",ephemeral=True) #todo
            return
        try:
            period = float(period)
            if period <= 0:
                await itx.response.send_message("Your period (data in the past [x] days) has to be above 0!",hidden=True)
                return
        except ValueError:
            await itx.response.send_message("Your period has to be an integer for the amount of days that have passed",hidden=True)
            return

        values = {
            0:["false",'0','n','no','nah','nope','never','nein',"don't"],
            1:['true','1','y','ye','yes','okay','definitely','please']
        }
        for val in values:
            if str(doubles).lower() in values[val]:
                doubles = val
        if doubles not in [0,1]:
            await itx.response.send_message("Your value for Doubles is not a boolean or binary (true/1 or false/0)!",ephemeral=True)
        accuracy = period*2400 #divide graph into 36 sections
        period *= 86400 # days to seconds
        # Get a list of people (in this server) that joined at certain times. Maybe round these to a certain factor (don't overstress the x-axis)
        # These certain times are in a period of "now" and "[period] seconds ago"
        totals = []
        results = {}
        currentTime = mktime(datetime.utcnow().timetuple()) #  todo: globalize the time # maybe fixed with .utcnow() ?
        minTime = int((currentTime-period)/accuracy)*accuracy
        maxTime = int(currentTime/accuracy)*accuracy

        collection = RinaDB["data"]
        query = {"guild_id": itx.guild_id}
        data = collection.find(query)
        try:
            data = data[0]
        except IndexError:
            await itx.response.send_message("Not enough data is configured to do this action! Please hope someone joins sometime soon lol",ephemeral=True)
            return

        await itx.response.defer()
        for y in data:
            if type(data[y]) is not dict: continue
            column = []
            results[y] = {}
            for member in data[y]:
                for time in data[y][member]:
                    #if the current time minus the amount of seconds in every day in the period since now, is still older than more recent joins, append it
                    if currentTime-period < time:
                        column.append(time)
                        if doubles == 0:
                            break
            totals.append(len(column))
            for time in range(len(column)):
                column[time] = int(column[time]/accuracy)*accuracy
                if column[time] in results[y]:
                    results[y][column[time]] += 1
                else:
                    results[y][column[time]] = 1

            #minTime = sorted(column)[0]
            # minTime = int((currentTime-period)/accuracy)*accuracy
            # maxTime = int(currentTime/accuracy)*accuracy
            if len(column) == 0:
                print(f"There were no '{y}' users found for this time period.")
            else:
                timeList = sorted(column)
                if minTime > timeList[0]:
                    minTime = timeList[0]
                if maxTime < timeList[-1]:
                    maxTime = timeList[-1]
        minTimeDB = minTime
        for y in data:
            if type(data[y]) is not dict: continue
            minTime = minTimeDB
            # print(y)
            # print(data[str(ctx.guild.id)][y])
            while minTime < maxTime:
                if minTime not in results[y]:
                    results[y][minTime] = 0
                minTime += accuracy

        result = {}
        for i in results:
            result[i] = {}
            for j in sorted(results[i]):
                result[i][j]=results[i][j]
            results[i] = result[i]

        import matplotlib.pyplot as plt
        import pandas as pd
        try:
            d = {
                "time": [i for i in results["joined"]],
                "joined":[results["joined"][i] for i in results["joined"]],
                "left":[results["left"][i] for i in results["left"]],
                "verified":[results["verified"][i] for i in results["verified"]]
            }
        except KeyError as ex:
            await itx.followup.send(f"{ex} did not have data, thus could not make the graph.", ephemeral=True)
            return
        df = pd.DataFrame(data=d)
        # print(df)
        fig, (ax1) = plt.subplots(1,1)
        fig.suptitle(f"Member +/-/verif (r/g/b) in the past {period/86400} days")
        fig.tight_layout(pad=1.0)
        ax1.plot(df['time'], df["joined"], 'b')
        ax1.plot(df['time'], df["left"], 'r')
        ax1.plot(df['time'], df["verified"], 'g')
        ax1.set_ylabel("# of players")

        tickLoc = [i for i in df['time'][::3]]
        if period/86400 <= 1:
            tickDisp = [datetime.fromtimestamp(i).strftime('%H:%M') for i in tickLoc]
        else:
            tickDisp = [datetime.fromtimestamp(i).strftime('%Y-%m-%dT%H:%M') for i in tickLoc]

        # plt.xticks(tickLoc, tickDisp, rotation='vertical')
        # plt.setp(tickDisp, rotation=45, horizontalalignment='right')
        ax1.set_xticks(tickLoc,
                labels=tickDisp,
                horizontalalignment = 'right',
                minor=False,
                rotation=30)
        ax1.grid(visible=True, which='major', axis='both')
        fig.subplots_adjust(bottom=0.180, top=0.90, left=0.1, hspace=0.1)
        plt.savefig('userJoins.png')
        await itx.followup.send(f"In the past {period/86400} days, `{totals[0]}` members joined, `{totals[1]}` left, and `{totals[2]}` were verified. (with{'out'*(1-doubles)} doubles)",file=discord.File('userJoins.png') )


async def setup(client):
    # client.add_command(getMemberData)
    await client.add_cog(MemberData(client))

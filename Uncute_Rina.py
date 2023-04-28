if __name__ == '__main__':
    print("Program started")
from import_modules import *

if __name__ != '__main__':
    class Bot(commands.Bot):
        pass
else:
    debug(f"[#    ]: Loading api keys..." + " " * 30, color="light_blue", end='\r')
    # debug(f"[+     ]: Loading server settings" + " " * 30, color="light_blue", end='\r')
    try:
        api_keys = json.loads(open("api_keys.json","r").read())
        tokens = {}
        TOKEN = api_keys['Discord']
        for key in ['MongoDB', 'Open Exchange Rates']:
            # copy every other key to new dictionary to check if every key is in the file.
            tokens[key] = api_keys[key]
    except json.decoder.JSONDecodeError:
        raise SyntaxError("Invalid JSON file. Please ensure it has correct formatting.").with_traceback(None)
    except KeyError as ex:
        raise KeyError("Missing API key for: " + str(ex)).with_traceback(None)
    # mongoURI = open("mongo.txt","r").read()
    debug(f"[##   ]: Loading database clusters..." + " " * 30, color="light_blue", end='\r')
    cluster = MongoClient(tokens['MongoDB'])
    RinaDB = cluster["Rina"]
    cluster = motor.AsyncIOMotorClient(tokens['MongoDB'])
    asyncRinaDB = cluster["Rina"]
    appcommanderror_cooldown = 0
    debug(f"[###  ]: Loading version..." + " " * 30, color="light_blue", end='\r')
    # Dependencies:
    #   server members intent,
    #   message content intent,
    #   permissions:
    #       send messages
    #       attach files (for image of the member joining graph thing)
    #       read channel history (find previous Table messages from a specific channel afaik)
    #       create and delete voice channels
    #       move users between voice channels
    #       manage roles (for adding/removing table roles)
    #       manage channels (Global: You need this to be able to set the position of CustomVCs in a category, apparently) NEEDS TO BE GLOBAL?

    # dumb code for cool version updates
    fileVersion = "1.1.8.1".split(".")
    try:
        version = open("version.txt", "r").read().split(".")
    except FileNotFoundError:
        version = ["0"]*len(fileVersion)
    # if testing, which environment are you in?
    # 1: private dev server; 2: public dev server (TransPlace [Copy])
    testing_environment = 2
    for v in range(len(fileVersion)):
        if int(fileVersion[v]) > int(version[v]):
            version = fileVersion + ["0"]
            break
    else:
        version[-1] = str(int(version[-1])+1)
    version = '.'.join(version)
    open("version.txt","w").write(f"{version}")
    debug(f"[#### ]: Loading Bot" + " " * 30, color="light_blue", end='\r')

    intents = discord.Intents.default()
    intents.members = True #apparently this needs to be additionally defined cause it's not included in Intents.default()?
    intents.message_content = True #apparently it turned off my default intent or something: otherwise i can't send 1984, ofc.
    #setup default discord bot client settings, permissions, slash commands, and file paths


    class Bot(commands.Bot):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        commandList: list[discord.app_commands.AppCommand]
        logChannel: discord.TextChannel
        api_tokens = tokens
        startup_time = datetime.now() # used in /version
        RinaDB = RinaDB
        asyncRinaDB = asyncRinaDB

        def get_command_mention(self, _command):
            args = _command.split(" ")+[None, None]
            command_name, subcommand, subcommand_group = args[0:3]
            # returns one of the following:
            # </COMMAND:COMMAND_ID>
            # </COMMAND SUBCOMMAND:ID>
            # </COMMAND SUBCOMMAND_GROUP SUBCOMMAND:ID>
            #              /\- is posed as 'subcommand', to make searching easier
            for command in self.commandList:
                if command.name == command_name:
                    if subcommand is None:
                        return command.mention
                    for subgroup in command.options:
                        if subgroup.name == subcommand:
                            if subcommand_group is None:
                                return subgroup.mention
                            #now it techinically searches subcommand in subcmdgroup.options
                            #but to remove additional renaming of variables, it stays as is.
                            # subcmdgroup = subgroup # hm
                            for subcmdgroup in subgroup.options:
                                if subcmdgroup.name == subcommand_group:
                                    return subcmdgroup.mention
                                    # return f"</{command.name} {subgroup.name} {subcmdgroup.name}:{command.id}>"
            return "/"+_command

        async def get_guild_info(self, guild_id: discord.Guild | int, *args: str, log: discord.Interaction | str = None):
            if isinstance(guild_id, discord.Guild):
                guild_id = guild_id.id
            try:
                collection = self.RinaDB["guildInfo"]
                query = {"guild_id": guild_id}
                guild_data = collection.find_one(query)
                if guild_data is None:
                    debug("Not enough data is configured to do this action! Please fix this with `/editguildinfo`!", color="red")
                    raise KeyError(str(guild_id) + " does not have data in the guildInfo database!")
                if len(args) == 0:
                    return guild_data
                output = []
                unavailable = []
                for key in args:
                    try:
                        output.append(guild_data[key])
                    except KeyError:
                        unavailable.append(key)
                if unavailable:
                    raise KeyError("Guild " + str(guild_id) + " does not have data for: " + ', '.join(unavailable))
                if len(output) == 1: # prevent outputting [1] (one item as list)
                    return output[0]
                return output
            except KeyError:
                if log is None:
                    raise
                await log[0].response.send_message(log[1])
                raise

    debug(f"[#     ]: Loaded server settings" + " " * 30, color="green")
    debug(f"[#+    ]: Starting Bot...", color="light_blue", end='\r')
    client = Bot(
            intents=intents,
            command_prefix="/!\"@:\\#", #unnecessary, but needs to be set so.. uh.. yeah. Unnecessary terminal warnings avoided.
            case_insensitive=True,
            activity=discord.Game(name="with slash (/) commands!"),
            allowed_mentions=discord.AllowedMentions(everyone=False)
    )

    # Client events begin
    @client.event
    async def on_ready():
        debug(f"[######] Logged in as {client.user}, in version {version} (in {datetime.now()-program_start})",color="green")
        await client.logChannel.send(f":white_check_mark: **Started Rina** in version {version}")

    @client.event
    async def setup_hook():
        start = datetime.now()

        ## cache server settings into client, to prevent having to load settings for every extension
        debug(f"[##    ]: Started Bot"+" "*30,color="green")
        ## activate the extensions/programs/code for slash commands
        extensions = [
            "cmd_addons",
            "cmd_customvcs",
            "cmd_emojistats",
            "cmd_getmemberdata",
            "cmd_pronouns",
            "cmd_qotw",
            "cmd_termdictionary",
            "cmd_todolist",
            "cmd_toneindicator",
            "cmdg_Reminders",
            "cmdg_Starboard",
            # "cmdg_Table", # Disabled: it was never used. Will keep file in case of future projects
        ]

        for extID in range(len(extensions)):
            debug(f"[{'#'*extID}{' '*(len(extensions)-extID-1)} ]: Loading {extensions[extID]}"+" "*15,color="light_blue",end='\r')
            await client.load_extension(extensions[extID])
        debug(f"[###   ]: Loaded extensions successfully (in {datetime.now()-start})",color="green")

        ## activate the buttons in the table message
        ## Disabled: it was never used. Will keep file in case of future projects
        # debug(f"[##+   ]: Updating table message"+ " "*30,color="light_blue",end='\r')
        try:
            client.logChannel = await client.fetch_channel(988118678962860032)
        except (discord.errors.InvalidData, discord.errors.HTTPException, discord.errors.NotFound, discord.errors.Forbidden): #one of these
            if testing_environment == 1:
                client.logChannel = await client.fetch_channel(986304081234624554)
            else:
                client.logChannel = await client.fetch_channel(1062396920187863111)

        debug(f"[###+  ]: Restarting ongoing reminders"+" "*30,color="light_blue",end="\r")
        collection = RinaDB["reminders"]
        query = {}
        db_data = collection.find(query)
        for user in db_data:
            try:
                for reminder in user['reminders']:
                    creationtime = datetime.fromtimestamp(reminder['creationtime'])#, timezone.utc)
                    remindertime = datetime.fromtimestamp(reminder['remindertime'])#, timezone.utc)
                    Reminders.Reminder(client, creationtime, remindertime, user['userID'], reminder['reminder'], user, continued=True)
            except KeyError:
                pass
        debug(f"[####  ]: Finished setting up reminders"+" "*30,color="green")
        debug(f"[####+ ]: Caching bot's command names and their ids",color="light_blue",end='\r')
        commandList = await client.tree.fetch_commands()
        client.commandList = commandList
        debug(f"[##### ]: Cached bot's command names and their ids"+" "*30,color="green")
        debug(f"[#####+]: Starting..."+" "*30,color="light_blue",end='\r')

        # debug(f"[{'#'*extID}{' '*(len(extensions)-extID-1)} ]: Syncing command tree"+ " "*30,color="light_blue",end='\r')
        # await client.tree.sync()

    @client.event
    async def on_message(message):
        # kill switch, see cmd_addons for other on_message events.
        if message.author.id == 262913789375021056:
            if message.content == ":kill now please okay u need to stop.":
                sys.exit(0)

    # Bot commands begin

    @client.tree.command(name="version",description="Get bot version")
    async def botVersion(itx: discord.Interaction):
        await itx.response.send_message(f"Bot is currently running on v{version} (started at {client.startup_time.strftime('%Y-%m-%dT%H:%M:%S.%f')})")

    @client.tree.command(name="update",description="Update slash-commands")
    async def updateCmds(itx: discord.Interaction):
        if not isStaff(itx):
            await itx.response.send_message("Only Staff can update the slash commands (to prevent ratelimiting)", ephemeral=True)
            return
        await client.tree.sync()
        commandList = await client.tree.fetch_commands()
        client.commandList = commandList
        await itx.response.send_message("Updated commands")

    @client.event
    async def on_error(event, *_args, **_kwargs):
        try:
            log_guild = await client.fetch_guild(959551566388547676)
        except discord.errors.NotFound:
            if testing_environment == 1:
                log_guild = await client.fetch_guild(985931648094834798)
            else:
                log_guild = await client.fetch_guild(981615050664075404)

        # collection = RinaDB["guildInfo"]
        # query = {"guild_id": log_guild.id}
        # guild = collection.find_one(query)
        # if guild is None:
        #     debug("Not enough data is configured to do this action! Please fix this with `/editguildinfo`!",color="red")
        #     return
        # vcLog      = guild["vcLog"]
        try:
            vcLog = await client.get_guild_info(log_guild, "vcLog")
        except KeyError: # precaution to prevent infinite loops, I suppose
            pass
        #message = args[0]
        msg = ""
        msg += f"\n\n\n\n[{datetime.now().strftime('%H:%M:%S.%f')}] [ERROR]: {event}\n\n"
        msg += traceback.format_exc()
        debug(f"{msg}",add_time=False)

        # msg += '\n\n          '.join([repr(i) for i in args])+"\n\n"
        # msg += '\n\n                   '.join([repr(i) for i in kwargs])
        msg = msg.replace("\\","\\\\").replace("*","\\*").replace("`","\\`").replace("_","\\_").replace("~~","\\~\\~")
        channel = await log_guild.fetch_channel(vcLog)
        embed = discord.Embed(color=discord.Colour.from_rgb(r=181, g=69, b=80), title='Error log', description=msg)
        await channel.send("<@262913789375021056>", embed=embed)

    @client.tree.error
    async def on_app_command_error(interaction, error):
        global appcommanderror_cooldown
        if int(mktime(datetime.now().timetuple())) - appcommanderror_cooldown < 60:
            # prevent extra log (prevent excessive spam and saving myself some large mentioning chain) if within 1 minute
            return
        await interaction.followup.send("Something went wrong!", ephemeral=True)
        import traceback  # , logging
        try:
            log_guild = await client.fetch_guild(959551566388547676)
        except discord.errors.NotFound:
            if testing_environment == 1:
                log_guild = await client.fetch_guild(985931648094834798)
            else:
                log_guild = await client.fetch_guild(981615050664075404)

        #     try:
        #         client.logChannel = await client.fetch_channel(988118678962860032)
        #     except (discord.errors.InvalidData, discord.errors.HTTPException, discord.errors.NotFound, discord.errors.Forbidden): #one of these
        #         if testing_environment == 1:
        #             client.logChannel = await client.fetch_channel(986304081234624554)
        #         else:
        #             client.logChannel = await client.fetch_channel(1062396920187863111)
        # collection = RinaDB["guildInfo"]
        # query = {"guild_id": log_guild.id}
        # guild = collection.find_one(query)
        # if guild is None:
        #     debug("Not enough data is configured to do this action! Please fix this with `/editguildinfo`!", color="red")
        #     return
        # vcLog = guild["vcLog"]
        try:
            vcLog = await client.get_guild_info(log_guild, "vcLog")
        except KeyError: # precaution I guess, lol
            pass
        # message = args[0]
        msg = ""
        msg += f"\n\n\n\n[{datetime.now().strftime('%H:%M:%S.%f')}] [ERROR]: {error}\n\n"
        msg += traceback.format_exc()
        debug(f"{msg}", add_time=False)

        # msg += '\n\n          '.join([repr(i) for i in args])+"\n\n"
        # msg += '\n\n                   '.join([repr(i) for i in kwargs])
        msg = msg.replace("\\", "\\\\").replace("*", "\\*").replace("`", "\\`").replace("_", "\\_").replace("~~", "\\~\\~")
        channel = await log_guild.fetch_channel(vcLog)
        embed = discord.Embed(color=discord.Colour.from_rgb(r=255, g=0, b=127), title='App Command Error log', description=msg)
        await channel.send("<@262913789375021056>", embed=embed)
        appcommanderror_cooldown = int(mktime(datetime.now().timetuple()))

    try:
        client.run(TOKEN)
    except SystemExit:
        print("Exited the program forcefully using the kill switch")

# todo:
# - Translator
# - (Unisex) compliment quotes
# - Add error catch for when dictionaryapi.com is down

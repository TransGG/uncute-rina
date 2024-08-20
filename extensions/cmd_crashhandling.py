import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from time import mktime
import traceback # for crash logging
import sys # to stop the program (and automatically restart, thanks to pterodactyl)
from resources.customs.bot import Bot
from resources.utils.utils import debug, TESTING_ENVIRONMENT


appcommanderror_cooldown: datetime = datetime.fromtimestamp(0)
commanderror_cooldown: datetime = datetime.fromtimestamp(0)


async def send_crash_message(
        client: Bot,
        error_type: str,
        traceback_text: str,
        error_source: str,
        color: discord.Colour,
        itx: discord.Interaction | None = None
) -> None:
    """
    Sends crash message to Rina's main logging channel

    Parameters
    -----------
    error_type: :class:`str`
        Is it an 'Error' or an 'AppCommand Error'
    traceback_text: :class:`str`
        The traceback to send.
    error_source: :class:`str`
        Name of the error source, displayed at the top of the message. Think of event or command.
    color: :class:`discord.Colour`
        Color of the discord embed.
    itx: :class:`discord.Interaction` | :class:`None`, optional
        Interaction with a potential guild. This might allow Rina to send the crash log to that guild instead. Default: None.
    """
    log_guild: discord.Guild
    try:
        log_guild = itx.guild
        vcLog = await client.get_guild_info(itx.guild, "vcLog")
    except (AttributeError, KeyError): # no guild settings, or itx -> 'NoneType' has no attribute '.guild'
        try:
            log_guild = await client.fetch_guild(959551566388547676)
        except discord.errors.NotFound:
            if TESTING_ENVIRONMENT == 1:
                log_guild = await client.fetch_guild(985931648094834798)
            else:
                log_guild = await client.fetch_guild(981615050664075404)

        try:
            vcLog = await client.get_guild_info(log_guild, "vcLog")
        except KeyError:
            return # prevent infinite logging loops, i guess

    error_caps = error_type.upper()
    debug_message = f"\n\n\n\n[{datetime.now().strftime('%H:%M:%S.%f')}] [{error_caps}]: {error_source}\n\n{traceback_text}\n"
    debug(f"{debug_message}",add_time=False)

    channel = await log_guild.fetch_channel(vcLog) #crashes if none
    msg = debug_message.replace("``", "`` ")#("\\", "\\\\").replace("*", "\\*").replace("`", "\\`").replace("_", "\\_").replace("~~", "\\~\\~")
    msg = "```" + msg + "```"
    embed = discord.Embed(color=color, title = error_type +' Log', description=msg[:4095]) # max length of 4096 chars
    await channel.send(f"{client.bot_owner.mention}", embed=embed, allowed_mentions=discord.AllowedMentions(users=[client.bot_owner]))


class CrashHandling(commands.Cog):
    def __init__(self, client: Bot):
        self.client = client
        client.on_error = self.on_error
        client.tree.on_error = self.on_app_command_error

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        # kill switch, see cmd_addons for other on_message events. (and a few other extensions)
        if message.author.id == self.client.bot_owner.id:
            cool_keys = [
                ":restart",
                ":sudo restart",
                ":sudo reboot",
                ":sudo shutdown",
            ]
            if message.content == ":kill now please stop" or any([message.content.startswith(item) for item in cool_keys]):
                await message.add_reaction("🔄")
                sys.exit(0)
                # quitting the program also
        # this will only run if it hasn't already quit, of course
        if message.content.startswith(":sudo "):
            await message.reply("Cleo.CommandManager.InsufficientPermissionError: Could not run command: No permission\nTryin to be part of the cool kids? Try reading this:\n1 4M 4 V3RY C001 K16!")
            await message.add_reaction("⚠")
        elif message.content.lower().startswith("i am a very cool kid"):
            await message.channel.send("Yes. Yes you are.")

    async def on_error(self, event: str, *_args, **_kwargs):
        # msg = '\n\n          '.join([repr(i) for i in args])+"\n\n"
        # msg += '\n\n                   '.join([repr(i) for i in kwargs])
        global commanderror_cooldown
        if datetime.now() - commanderror_cooldown < timedelta(seconds=10):
            # prevent extra log (prevent excessive spam and saving myself some large mentioning chain) if within 10 seconds
            return
        msg = traceback.format_exc()
        await send_crash_message(self.client, "Error", msg, event, discord.Colour.from_rgb(r=255, g=77, b=77))
        commanderror_cooldown = datetime.now()

    async def on_app_command_error(self, itx: discord.Interaction, error):
        global appcommanderror_cooldown
        if datetime.now() - appcommanderror_cooldown < timedelta(seconds=60):
            # prevent extra log (prevent excessive spam and saving myself some large mentioning chain) if within 1 minute
            return

        async def reply(itx: discord.Interaction, message: str):
            try:
                if itx.response.is_done():
                    await itx.followup.send(message, ephemeral=True)
                else:
                    await itx.response.send_message(message, ephemeral=True)
            except discord.errors.NotFound: # ex: 404 interaction not found, eg. took too long
                #await itx.followup.send(message, ephemeral=True)
                pass # prevent other code from not running

        cmd_mention = self.client.get_command_mention("update")
        if isinstance(error, discord.app_commands.errors.CommandNotFound):
            await reply(itx, f"This command doesn't exist! Perhaps the commands are unsynced. Ask {self.client.bot_owner} ({self.client.bot_owner.mention}) if she typed {cmd_mention}!")
        elif isinstance(error, discord.app_commands.errors.CommandSignatureMismatch):
            await reply(itx, f"Error: CommandSignatureMismatch. Either Mia used GroupCog instead of Cog, or this command is out of date (try {cmd_mention})")
        else:
            if hasattr(error, 'original'):
                error_reply = "Error"
                if hasattr(error.original, 'status'):
                    error_reply += " " + str(error.original.status)
                    # if error.original.status == "403":
                    #     await reply(itx, f"Error 403: It seems like I didn't have permissions for this action! If you believe this is an error, please message or ping {client.bot_owner}} :)")
                if hasattr(error.original, 'code'):
                    error_reply += " (" + str(error.original.code) + ")"
                await reply(itx, error_reply + f". Please report the error and details to {self.client.bot_owner} ({self.client.bot_owner.mention}) by pinging her or sending her a DM")
            else:
                await reply(itx, "Something went wrong executing your command!\n    " + repr(error)[:1700])

        try:
            msg = f"    Executor details: {itx.user} ({itx.user.id})\n"
        except Exception as ex:
            msg = f"    Executor details: couldn't get interaction details: {repr(ex)}\n"
            #   f"    command: {error.command}\n" + \
            #   f"    arguments: {error.args}\n"
        if hasattr(error, 'original'):
            if hasattr(error.original, 'code'):
                msg += f"    code: {error.original.code}\n"
            if hasattr(error.original, 'status'):
                msg += f"    original error: {error.original.status}: {error.original.text}\n\n"
                    #    f"   error response:     {error.original.response}\n\n"
        msg += traceback.format_exc()
        # details: /help `page:1` `param2:hey`
        command_details = f"</{itx.command.name}:{itx.data.get('id')}> " + ' '.join([f"`{k}:{v}`" for k, v in itx.namespace.__dict__.items()])
        await send_crash_message(self.client, "AppCommand Error", msg, command_details, discord.Colour.from_rgb(r=255, g=121, b=77), itx=itx)
        appcommanderror_cooldown = datetime.now()

async def setup(client: Bot):
    await client.add_cog(CrashHandling(client))

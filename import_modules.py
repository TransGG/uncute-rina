class PrintProgress:
    def __init__(self, max):
        self.progress = 0
        self.max = max

    def increment(self, name):
        print(f"[{self.progress*'#'}+{(self.max-self.progress-1)*' '}] Importing modules:   {name}{' '*(50-len(name))}\033[F")
        self.progress += 1

class Object(object):
    pass

progress = PrintProgress(26)
progress.increment("datetime")
from datetime import datetime, timedelta, timezone # for checking if user is older than 7days (in verification
program_start = datetime.now()
progress.increment("discord")
import discord # It's dangerous to go alone! Take this. /ref
progress.increment("discord/app_commands")
from discord import app_commands # v2.0, use slash commands
progress.increment("discord.ext/commands")
from discord.ext import commands # required for client bot
progress.increment("typing")
import typing
progress.increment("time/mktime")
from time import mktime # for unix time code
progress.increment("json")
import json # to interpret the obtained api data
progress.increment("sys")
import sys # kill switch for rina (search for :kill)
progress.increment("random")
import random # for picking a random call_cute quote
progress.increment("re")
import re #use regex to remove pronouns from people's usernames, and split their names into sections by capital letter
#          and to identify custom emojis in a text message
#          and to remove API hyperlink definitions: {#Ace=asexual}
progress.increment("requests")
import requests # for getting the equality index of countries and to grab from en.pronouns.page api (search)
# progress.increment("aiohttp")
# import aiohttp
progress.increment("warnings")
import warnings #used to warn for invalid color thingy in the debug function; as well as for debug()
progress.increment("pymongo")
import pymongo # used in cmd_emojistats
progress.increment("pymongo/MongoClient")
from pymongo import MongoClient
progress.increment("motor/motor_asyncio")
import motor.motor_asyncio as motor # for making Mongo run asynchronously (during api calls)
progress.increment("apscheduler/schedulers/asyncio/AsyncIOScheduler")
from apscheduler.schedulers.asyncio import AsyncIOScheduler # for scheduling reminders

class Bot(commands.Bot): # Only used for type checking. Program will always use Bot in main.py
    def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    api_tokens: str
    startup_time: datetime
    version: str
    commandList: list[discord.app_commands.AppCommand]
    log_channel: discord.TextChannel
    RinaDB: typing.Any # not entirely sure
    asyncRinaDB: typing.Any
    custom_ids: dict[str, int]
    bot_owner: discord.User # for AllowedMentions in on_appcommand_error()
    reminder_scheduler: AsyncIOScheduler # for Reminders
    
    def get_command_mention(self, command_string: str) -> str:
        """
        Turn a string (/reminders remindme) into a command mention (</reminders remindme:43783756372647832>)

        ### Parameters
        --------------
        command_string:  :class:`str`
            Command you want to convert into a mention (without slash in front of it)
        ### Returns
        -----------
        command mention: :class:`str`
            The command mention, or input if not found
        """

    async def get_guild_info(self, guild_id: discord.Guild | int, *args: str, log: list[discord.Interaction | str] | None = None) -> typing.Any:
        """
        Get a guild's server settings (from /editguildinfo, in cmd_customvcs)

        ### Arguments:
        --------------
        guild_id: :class:`discord.Guild` or :class:`int`
            guild or id from which you want to get the guild info / settings
        *args: :class:`str`
            settings (or multiple) that you want to fetch
        log (optional): :class:`list[discord.Interaction, str]`
            A list of [itx, error_message], and will reply this error message to the given interaction if there's a KeyError.

        ### Returns:
        ------------
        `any` (whichever is given in the database)

        ### Raises:
        -----------
        `KeyError` if guild is None, does not have data, or not the requested data.
        """


progress.increment("asyncio")
import asyncio # lets rina take small pauses while getting emojis from MongoDB to allow room for other commands
# that asyncio is literally just 'await asyncio.sleep(0)' lol
# apparently letting it run asynchronously might prevent a lot of missing heartbeats when adding data on data-editing events
progress.increment("matplotlib/pyplot")
import matplotlib.pyplot as plt
progress.increment("matplotlib/dates")
import matplotlib.dates as md
progress.increment("pandas")
import pandas as pd
progress.increment("traceback")
import traceback
progress.increment("logging")
import logging
progress.increment("math/ceil")
from math import ceil
progress.increment("utils")
from utils import *
progress.increment("cmdg_Reminders/Reminders")
from cmdg_reminders import Reminders
progress.increment("cmd_qotw/get_watchlist_index")
from cmd_qotw import get_watchlist_index
# used for adding reminders when starting up the bot
# print_progress(21,31, "", end='\n')
debug(f"[{'#'*(progress.max)}] Imported modules     "+' '*50,color='green', add_time=False)

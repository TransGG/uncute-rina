def print_progress(now, max, name, end='\r'):
    print(f"[{now*'#'}{(max-now)*' '}] Importing modules:   {name}{' '*(50-len(name))}", end=end)

print_progress(0,22, "datetime/{datetime,timedelta,timezone}")
from datetime import datetime, timedelta, timezone # for checking if user is older than 7days (in verification
program_start = datetime.now()
print_progress(1,22, "discord")
import discord # It's dangerous to go alone! Take this. /ref
print_progress(2,22, "discord/app_commands")
from discord import app_commands # v2.0, use slash commands
print_progress(3,22, "discord.ext/commands")
from discord.ext import commands # required for client bot
print_progress(4,22, "time/mktime")
from time import mktime # for unix time code
print_progress(5,22, "json")
import json # to interpret the obtained api data
print_progress(6,22, "sys")
import sys # kill switch for rina (search for :kill)
print_progress(7,22, "random")
import random # for picking a random call_cute quote
print_progress(8,22, "re")
import re #use regex to remove pronouns from people's usernames, and split their names into sections by capital letter
#          and to identify custom emojis in a text message
#          and to remove API hyperlink definitions: {#Ace=asexual}
print_progress(9,22, "requests")
import requests # for getting the equality index of countries and to grab from en.pronouns.page api (search)
print_progress(10,22, "warnings")
import warnings #used to warn for invalid color thingy in the debug function; as well as for debug()
print_progress(11,22, "pymongo")
import pymongo # used in cmd_emojistats
print_progress(12,22, "pymongo/MongoClient")
from pymongo import MongoClient
print_progress(13,22, "motor/motor_asyncio")
import motor.motor_asyncio as motor # for making Mongo run asynchronously (during api calls)
print_progress(14,22, "asyncio")
import asyncio # lets rina take small pauses while getting emojis from MongoDB to allow room for other commands
# that asyncio is literally just 'await asyncio.sleep(0)' lol
# apparently letting it run asynchronously might prevent a lot of missing heartbeats when adding data on data-editing events
print_progress(15,22, "matplotlib/pyplot")
import matplotlib.pyplot as plt
print_progress(16,22, "pandas")
import pandas as pd
print_progress(17,22, "apscheduler/schedulers/asyncio/AsyncIOScheduler")
from apscheduler.schedulers.asyncio import AsyncIOScheduler # for scheduling reminders
print_progress(18,22, "traceback")
import traceback
print_progress(19,22, "logging")
import logging
print_progress(20,22, "utils")
from utils import *
print_progress(21,22, "reminders")
from cmdg_Reminders import Reminders
# used for adding reminders when starting up the bot
# print_progress(21,21, "", end='\n')
debug(f"[{'#'*22}] Imported modules                      ",color='green', add_time=False)

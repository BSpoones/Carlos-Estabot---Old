import discord, time, asyncio, json, sys, os
from datetime import datetime
from time import sleep
from glob import glob
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext.commands import Bot as BotBase
from discord.ext.commands.context import Context

from apscheduler.triggers.cron import CronTrigger
from ..db import db
from lib.cogs import *
from discord.ext.commands import (BadArgument, MissingRequiredArgument,CommandOnCooldown,CommandNotFound)
from discord.errors import HTTPException, Forbidden

sys.path.insert(0,os.getcwd())
print(os.getcwd())
with open("./data/Bot_Info.json") as f:
    Bot_Info = json.load(f)
    VERSION = Bot_Info["Version"]
    ACTIVITY_TYPE = Bot_Info["Activity type"]
    ACTIVITY_NAME = Bot_Info["Activity name"]
    PREFIX = Bot_Info["Prefix"] #Prefix for all bot commands
    TRUSTED_IDS = Bot_Info["Trusted IDs"]
    OWNER_IDS = Bot_Info["Owner IDs"] #Spoon ID
# PREFIX = "-"
# TRUSTED_IDS = [724351142158401577]
# OWNER_IDS = [724351142158401577]
# VERSION = "0.0.0"
# ACTIVITY_NAME = ""
COGS = [path.split("/")[-1][:-3] for path in glob("./lib/cogs/*.py")] #Selects all .py files in cog
class Ready(object):
    """
    Cogs return True if running, return False if not
    """
    try:#This is an insanely low effort solution to linux and windows breaking
        COGS = [path.split("/")[-1][:-3] for path in glob("./lib/cogs/*.py")]
    except:
        COGS = [path.split("\\")[-1][:-3] for path in glob("./lib/cogs/*.py")]

    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f"{cog} cog ready!")

    def all_ready(self):
        return all([getattr(self,cog) for cog in COGS])

class Bot(BotBase):
    """
    The main body of Carlos Estabot, all cogs and databases are loaded here and
    this is what is run in launcher.py
    """
    def __init__(self):
        self.PREFIX = PREFIX
        self.ready = False
        self.cogs_ready = Ready()
        self.guild = None
        self.scheduler = AsyncIOScheduler()
        self.TRUSTED_IDS = TRUSTED_IDS
        self.OWNER_IDS = OWNER_IDS
        self.start_time = time.time()
        self.banlist = []

        db.autosave(self.scheduler)
        
        super().__init__(command_prefix=PREFIX, owner_ids = OWNER_IDS)

    def setup(self): #Cog Setup
        try:# This is a low effort solution to stop windows and linux from being bad
            COGS = [path.split("/")[-1][:-3] for path in glob("./lib/cogs/*.py")]
            for cog in COGS:
                print(cog)
                self.load_extension(f"lib.cogs.{cog}")
                print(f"{cog} cog loaded.")
        except:
            COGS = [path.split("\\")[-1][:-3] for path in glob("./lib/cogs/*.py")]
            for cog in COGS:
                self.load_extension(f"lib.cogs.{cog}")
                print(f"{cog} cog loaded.")
                
        print("Setup complete!")

    def run(self): #Runs bot in launcher.py
        self.VERSION = VERSION
        self.ACTIVITY_NAME = ACTIVITY_NAME

        print("Running setup")
        self.setup()

        with open("./lib/bot/token.0","r",encoding="utf-8") as tf:
            self.TOKEN = tf.read()
        print("Running bot...")
        super().run(self.TOKEN, reconnect=True)

    async def print_message(self): #Prints out schedule will be used later
        await self.stdout.send("I am a timed notification don't mind me")

    async def process_commands(self, message):
        ctx = await self.get_context(message,cls=Context)

        if ctx.command is not None and ctx.guild is not None:
            if message.author.id in self.banlist:
                await ctx.send("You are banned from using commands")
            elif not self.ready:
                await ctx.send("I am still starting up, try again in a few seconds")
            else:
                await self.invoke(ctx)

    async def on_connect(self):
        print("Bot connected at",(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    async def on_disconnect(self):
        print("Bot disconnected at",(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    async def on_error(self, err, *args, **kwags): #Error handling taken directly off the interwebs
        if err == "on_command_error":
            await args[0].send("Something went wrong.")

        raise err

    async def on_command_error(self, ctx, exc):

        if isinstance(exc,CommandNotFound):
            await ctx.send("That is not a valid command")
        elif isinstance(exc, MissingRequiredArgument):
            await ctx.send("One or more required arguments are missing.")

        elif isinstance(exc, CommandOnCooldown):
            await ctx.send(f"That command is on {str(exc.cooldown.type).split('.')[-1]} cooldown. Try again in {exc.retry_after:,.2f} secs.")
        elif isinstance(exc, BadArgument):
            await ctx.send(f"You have typed the command wrong, use -help (command) to find the correct arguments")
        elif isinstance(exc,CommandNotFound):
            await ctx.send("That is not a valid command")
        elif hasattr(exc, "original"):
            if isinstance(exc.original, HTTPException):
                await ctx.send("Unable to send message, Discord is preventing me from sending it\nThis may be beacuse the message is too long or you have too many items pinned")

            if isinstance(exc.original, Forbidden):
                await ctx.send("I do not have permission to do that.")

            else:
	            raise exc.original

        else:
            raise exc

    async def on_ready(self):
        await self.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.playing, name=(self.ACTIVITY_NAME)))
        if not self.ready:
            self.ready = True
            self.stdout = self.get_channel(799647664580591687) 
            self.reminder_channel = self.get_channel(808856265152266242)
            while not self.cogs_ready.all_ready(): #Checks if all cogs are ready
                await asyncio.sleep(0.5)    
            self.ready= True
            print("Bot Ready!")

        else:
            print("Bot reconnected!")

    async def on_message(self,message):
        if not message.author.bot:
            await self.process_commands(message)

    async def is_trusted(ctx):
        return ctx.author.id in TRUSTED_IDS
    
    async def is_owner(ctx):
        return ctx.author.id in OWNER_IDS

    def log_command(author,command):
        now =(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        message = (f"[{now}] {author}: {command}")
        with open("./data/command_log.txt","a+") as log_file:
            log_file.write(message+"\n")
        print(message)

    


bot = Bot()


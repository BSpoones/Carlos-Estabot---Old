import discord, time, sys, emoji, threading, asyncio, os, json
import subprocess
from discord.errors import Forbidden
from datetime import datetime,timedelta
from discord.embeds import Embed
from discord.ext.commands.core import has_any_role, has_permissions, has_role
from time import sleep
from lib.bot import Bot
from discord.ext.commands import Cog, BucketType
from discord.ext.commands import command, cooldown
from discord import __version__ as discord_version
from humanfriendly import format_timespan
from psutil import Process, cpu_times,virtual_memory
from platform import python_version
from subprocess import call

is_timer_running = False
def is_trusted(ctx):
    return ctx.author.id in Bot.TRUSTED_IDS
    
def is_owner(ctx):
    return ctx.author.id in Bot.OWNER_IDS

class Utility(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.VERSION = bot.VERSION
        self.start_time = bot.start_time

    @command(brief="Tells the bot to type a message")
    async def type(self, ctx,*, message):
        """Tells the bot to type a message"""
        await ctx.channel.purge(limit=1)
        await ctx.channel.send(message)
        message = str("typed "+message)
        #Bot.log_command(ctx.author,(message))

    @command(brief="Deletes the last x messages in chat. Limit = 10")
    @cooldown(1,60,BucketType.user)
    @has_permissions(manage_messages = True)
    async def purge(self, ctx,amount:int):
        """Deletes the last x messages in chat. Limit = 10"""
        if amount <= 10:
            await ctx.channel.purge(limit=int(amount+1))
            Bot.log_command(ctx.author,f"purged the last {amount} messages!")
        else:
            await ctx.send(f"You cannot purge {amount} messages because it is over the limit (10)")
        if ctx.author.id == 724351142158401577:
            ctx.command.reset_cooldown(ctx)

    @command(brief="Changes the bot's status")
    @has_any_role('Spoon')
    async def changestatus(self,ctx, mode,*, userstatus):
        """Changes the bot's status"""
        if mode == ("watching"):
            await self.bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.watching, name=(userstatus)))
        if mode == ("playing"):
            await self.bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.playing, name=(userstatus)))    
        if mode == ("listening"):
            await self.bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Activity(type=discord.ActivityType.listening, name=(userstatus)))
        Bot.log_command(ctx.author,f"Set bot status to {mode} {userstatus}")
    @command(brief="Shows the current version of Carlos Estabot")
    async def version(self,ctx):
        """Shows the current version of Carlos Estabot"""
        await ctx.send(f'```py\nCarlos Estabot version {self.VERSION}```')
        Bot.log_command(ctx.author,f"-version")

    @command(brief="Shows how long the bot has been running for")
    async def uptime(self,ctx):
        """Shows how long the bot has been running for"""
        await ctx.send(f"```py\nUptime: {format_timespan((time.time()-self.start_time))}```")
        Bot.log_command(ctx.author,f"-uptime")

    @command(brief="Shows the ping to the discord API")
    async def ping(self,ctx):
        """Shows the ping to the discord API"""
        await ctx.send(f'{round(self.bot.latency*1000)}ms')
        Bot.log_command(ctx.author,f"-ping")
    @command(brief="Shows the status of the bot")
    async def status(self,ctx):
        embed = Embed(
            title = "Carlos Estabot Stats",
            thumbnail = self.bot.user.avatar_url,
            colour = ctx.author.colour
        )
        proc = Process()
        with proc.oneshot():
            uptime = format_timespan((time.time()-self.start_time))
            ping = (self.bot.latency*1000)
            mem_total = virtual_memory().total / (1024**3)
            mem_of_total = proc.memory_percent()
            mem_usage = mem_total * (mem_of_total / 100) * (1024)

        fields = [
            ("Bot version",self.bot.VERSION, True),
            ("Python verssion",python_version(),True),
            ("discord.py version",discord_version,True),
            ("Uptime",uptime,True),
            ("Ping",f"{ping:,.0f} ms",True),
            ("Memory usage",f"{mem_usage:,.3f} MiB / {mem_total:,.0f} GiB ({mem_of_total:.0f}%)", True),
            ("Users",f"{ctx.guild.member_count:,}",True)
        ]
        for name,value,inline in fields:
            embed.add_field(name=name,value=value,inline=inline)
        embed.set_author(name= ctx.author, icon_url = ctx.author.avatar_url)
        await ctx.send(embed=embed)
        Bot.log_command(ctx.author,f"-status")
    @command(brief="Closes the bot - OWNER ONLY")
    async def closebot(self,ctx):
        """Closes the bot - OWNER ONLY"""
        if ctx.author.id == 724351142158401577:
            await ctx.send("Closing bot")
            await self.bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name=("myself shutdown")))
            await self.bot.logout()
        else:
            await ctx.send("You do not have permission to kill me")


    @command(brief="Shows the last command sent to Carlos Estabot")
    async def logs(self, ctx, limit=25):
        """Shows the last command sent to Carlos Estabot"""
        message = "```cpp\n"
        with open("./data/command_log.txt") as f:
            content = f.read()
            log_list = content.split("\n")
        if ctx.author.id == 724351142158401577:
            newlist = (log_list[-limit-1:])
            for i in range(limit):
                try:
                    message += newlist[i]
                    message += "\n"
                except:
                    pass
        else:
            limit = 1
            newlist = (log_list[-limit-1:])
            for i in range(limit):
                try:
                    message += newlist[i]
                    message += "\n"
                except:
                    pass
            Bot.log_command(ctx.author,f"checked the last {limit} logs")
        message += "```"
        await ctx.send(message)

    @command(brief="Creates a countdown")
    async def timer(self, ctx, time,role="themself"):
        """Timer to countdown and give a notification every x secodns. Use {-timer (NUMBER)m 1m} to countdown from NUMBER minutes and display a message every 1 minute. Use s,m,h,d to get Seconds, Minutes, Hours or Days"""
        try:
            time_int = int(time[:-1])            
                    
            if time.endswith("s"):
                new_time = time_int
                new_step = 1
            elif time.endswith("m"):
                new_time = (time_int*60)
                new_step = 15
            elif time.endswith("h"):
                new_time = time_int*3600
                new_step = 60
            elif time.endswith("d"):
                new_time = time_int*86400
                new_step = 60
            else:
                await ctx.send("Your time has been entered wrong. Please try again")

        except:
            await ctx.send("Please enter a number!")
        global timer_message
        timer_message = await ctx.send(f"{format_timespan(new_time)} remaining!")
        Bot.log_command(ctx.author,f"Made a {format_timespan(new_time)} timer and pinged {role}")
        try:
            await timer_message.pin()
            pinned = True
        except:
            await ctx.send("Unable to pin message, you have more than 50 pins")
        global is_timer_running
        is_timer_running = True
        for i in range(new_time):
            if is_timer_running == False:
                break
            await asyncio.sleep(1)
            if i % new_step == 0:
                await timer_message.edit(content=f"{format_timespan(new_time-i)} remaining!")
        if is_timer_running == True:
            await timer_message.edit(content=f"Ended")
        
            if role == "themself": 
                await ctx.send(f"{ctx.author.mention} Timer up")
            elif role == "everyone" or role == "here":
                await ctx.send(f"@{role} Timer up")
            else:
                await ctx.send(f"{role} Timer up")
            if pinned:
                await timer_message.unpin()
        if is_timer_running == False:
            await timer_message.edit(content=(f"Timer Cancelled"))

    @command(brief="Cancels the timer")
    async def canceltimer(self,ctx):
        global is_timer_running
        is_timer_running = False
        await timer_message.unpin()
        await ctx.send("Timer Cancelled!")
        Bot.log_command(ctx.author,f"canceled all timers")
    @command(brief="Restarts the bot")
    async def restart(self,ctx):
        if ctx.author.id == 724351142158401577:
            
            await ctx.send("Restarting bot...")
            # await self.bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name=("myself reboot")))
            # await self.bot.logout()
            os.system("python launcher.py")
            exit()
    @command(brief="Changes the bot prefix")
    async def changeprefix(self,ctx,prefix):
        if ctx.author.id == 724351142158401577:
            with open("./data/Bot_Info.json") as f:
                Bot_Info = json.load(f)
            Bot_Info["Prefix"] = prefix
            json.dump(Bot_Info, open("./data/Bot_Info.json","w"), indent=4)
            await ctx.send(f"Bot prefix changed to `{prefix}`. Restarting bot...")
            await self.restart(ctx)
        else:
            await ctx.send("You can't do that.")

        
        


            
    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("utility")
        print("Utility cog ready!")
        await self.bot.stdout.send("Utility cog working!")
    

    

def setup(bot):
    bot.add_cog(Utility(bot))

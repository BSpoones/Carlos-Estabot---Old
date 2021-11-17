from logging import error
import discord, time, datetime, json, asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext.commands.core import has_any_role, has_permissions, has_role
from lib import bot
from lib.bot import Bot, Bot_Info
from discord.ext.commands import Cog, UserConverter
from discord.ext.commands import command
from humanfriendly import format_timespan
from apscheduler.triggers.cron import CronTrigger

class Reminder(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.days_of_week = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        self.knife_reminder_channel = 808856265152266242
        self.bcot_reminder_channel = 776816647695761490
        self.BCoT_IDS = Bot_Info["BCoT IDs"]
        self.NFS_IDS = Bot_Info["NFS IDs"]
        self.reminder_scheduler = AsyncIOScheduler()
        self.update_scheduler()
    def update_scheduler(self):
        try:
            if (self.reminder_scheduler.state) == 1:
                self.reminder_scheduler.shutdown(wait=False)
            self.reminder_scheduler = AsyncIOScheduler()
        except:
            self.reminder_scheduler = AsyncIOScheduler()
               
        with open("./data/Reminders.json") as f:
            global reminder_data
            reminder_data = json.load(f)
        for user in reminder_data:
            for key,val in (reminder_data[user].items()):
                # print(key,val, user)
                user = user
                target = val["Target"]
                repeat = val["Repeat"]
                date = str(val["Date"])
                time = val["Time"]
                send_hour = time[:-2]
                send_minute = time[2:]
                todo = key
                if date == "day": # Sends a reminder every day at the specified time
                    self.reminder_scheduler.add_job(
                        self.send_reminder,
                        trigger=CronTrigger(
                            hour=send_hour,
                            minute=send_minute,
                            second=0),
                        args=[user,target,repeat,todo]
                        )
                if len(str(date)) == 1: # Numerical value for a weekday
                    self.reminder_scheduler.add_job(self.send_reminder,
                    trigger=CronTrigger(
                        day_of_week=date,
                        hour=send_hour,
                        minute=send_minute,
                        second=0
                        ),
                    args=[user,target,repeat,todo]
                    )
                if len(str(date)) == 8: # 8 didgit value for date (YYYYMMDD)
                    send_year=int(date[:4])
                    send_month=int(date[4:6])
                    send_day=int(date[6:8])
                    self.reminder_scheduler.add_job(self.send_reminder,
                    trigger=CronTrigger(
                        year=send_year,
                        month=send_month,
                        day=send_day,
                        hour=send_hour,
                        minute=send_minute,
                        second=0
                        ),
                        args=[user,target,repeat,todo]
                        )
        self.reminder_scheduler.start()


    async def send_reminder(self,*args):
        sender = (args[0])
        target = args[1]
        repeat = args[2]
        todo = args[3]
        reminder_embed = discord.Embed(
            title = "***Reminder***",
            description = (todo),
            colour = discord.Colour.green()
        )

        await self.bot.reminder_channel.send(embed=reminder_embed)
        await self.bot.reminder_channel.send(f"{target}")
        if repeat == "on":
            del reminder_data[sender][todo]
            json.dump(reminder_data, open("./data/Reminders.json","w"), indent=4)

        
    @command(brief="Creates a reminder")
    async def remind(self,ctx,user, repeat, date, time,*, todo):
        """Creates reminders for you\n Usage:\nUser = me or @mention\nRepeat = "every" or "on"\nDate= `YYYY-DD-MM`, weekday or `day` for a daily reminder\nTime = `HH:MM` 24 hour format\nTo = Your reminder\nExample: `-remind me every monday 1145 Join a call`\nOutput: `11:45 every Monday: Join a call`"""
        sender = str(ctx.author)
        error_message = ''
        # if user != "me" or user[0] != "<": # Temporarily disabled due to error
        #     error_message += "Make sure to either enter `me` or `@mention` someone\n"
        if repeat != "every" and repeat != "on":
            error_message += "Make sure that you hcoose either `every` or `on` for the repeat\n"
        try:
            try: # Used to convert the date from YYYY-MM-DD to YYYYMMDD for code to understand
                date = date.replace("-","")
                int(date)
                if len(date) != 8: # Checks to make sure the date is roughly YYYY-MM-DD. Currently no error handling to check for positioning
                    error_message += "Make sure the date is in the format `YYYY-MM-DD`\n"
                date = int(date) #Sets date to int to be used in APScheduler
                if repeat == "every":
                    error_message += "You can not repeat a callendar date. Use `every [weekday]` as a format instead!\n"
            except:
                date = date.lower()
                if date in self.days_of_week:
                    date = (self.days_of_week.index(date))
                elif date == "day":
                    date = date
                else:
                    error_message += "Make sure the date is a valid day!\n"
        except:
            await ctx.send("Error") # Honestly i have no clue what causes this
        try:
            time = time.replace(":","")
            if len(time) != 4:
                error_message += "Please make sure you enter a 24 hour time in the format `HH:MM`\n"
            int(time) # Checks if the value given is a a number and nothing else
        except:
            error_message += "Please make sure you enter a 24 hour time in the format `HH:MM`\n"
        if user == "me":
            user = ctx.author.mention

        if error_message != '':
            embed = discord.Embed(
                title = f"Reminder error",
                colour = 0xFF0000 
            )
            embed.add_field(name="Syntax errors:",value=error_message,inline=False)
            embed.set_author(name= ctx.author, icon_url = ctx.author.avatar_url)
            await ctx.send(embed=embed)
        if error_message == '':

            item = {}
            item["Target"] = user
            item["Repeat"] = repeat
            item["Date"] = date
            item["Time"] = time
            
            try:
                temp_dict = reminder_data[sender]
            except:
                reminder_data[sender] = [{}]
                temp_dict = reminder_data[sender][0]
            my_dict = {todo:item}
            try:
                temp_dict.update(my_dict) 
            except:
                temp_dict = my_dict
            reminder_data[sender] = temp_dict
            json.dump(reminder_data, open("./data/Reminders.json","w"), indent=4)
            Bot.log_command(ctx.author,f"set a reminder at {time} {repeat} {date} to {todo}")
            self.update_scheduler()
        
    @command(brief="Shows all of your active reminders")
    async def showreminders(self,ctx):
        """Shows all of your active reminders"""
        user = str(ctx.author)
        embed = discord.Embed(
                title = "**Showing all reminders**",
                description= "Here is a list of all your reminders",
                colour = ctx.author.colour
            )
        embed.set_author(name= ctx.author, icon_url = ctx.author.avatar_url)
        for key,val in (reminder_data[user].items()):
            # print(key,val, user)
            user = user
            target = val["Target"]
            repeat = val["Repeat"]
            date = (val["Date"])
            try:
                date = self.days_of_week[date].capitalize()
            except:
                if len(str(date)) == 8:
                    date = str(date)
                    send_year=(date[:4])
                    send_month=(date[4:6])
                    send_day=(date[6:8])
                    date = f"{send_year}-{send_month}-{send_day}"
                else:
                    date ="Every day"
            time = (val["Time"])
            send_hour = time[:-2]
            send_minute = time[2:]
            time = send_hour+":"+send_minute
            todo = key
            message = (f"Date: `{date}`\nTime: `{time}`\nRepeat: `{repeat}`")
            embed.add_field(name=todo,value=message,inline=False)
        await ctx.send(embed=embed)
        Bot.log_command(ctx.author,f"showed all their reminders")



    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("reminder")
        print("Reminder cog ready!")
        await self.bot.stdout.send("Reminder cog working!")        
        
        
def setup(bot):
    bot.add_cog(Reminder(bot))

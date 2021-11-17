# Lesson scheduler cog for Carlos Estabot
# Made by BSpoones - Mar 2021

import discord, time, datetime, asyncio, json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext.commands.core import has_any_role, has_permissions, has_role
from discord.ext.commands.errors import ArgumentParsingError, BadArgument
from lib.bot import Bot, Bot_Info
from discord.ext.commands import Cog
from discord.ext.commands import command
from humanfriendly import format_timespan
from apscheduler.triggers.cron import CronTrigger
from itertools import cycle

class Lesson_Schedule(Cog):
    def __init__(self,bot):
        self.bot = bot
        self.lesson_scheduler = AsyncIOScheduler()
        self.days_of_week = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
        self.schools = ["bcot","nfs"]

        """The following are used for the Basingstoke College of Technology (BCoT) and other schools"""
        self.BCoT_IDS = Bot_Info["BCoT IDs"]
        self.BCoT_lesson_announcement_channel = (Bot_Info["BCoT Lesson announcement channel"])
        self.BCoT_Next_lesson_time_channel = (Bot_Info["BCoT nextlesson time channel"])
        self.BCoT_Next_lesson_weekday_channel = (Bot_Info["BCoT nextlesson day channel"])
        self.NFS_IDS = Bot_Info["NFS IDs"]
        self.NFS_lesson_announcement_channel = (Bot_Info["NFS Lesson announcement channel"])
        self.Lesson_warning_times = Bot_Info["Lesson warning times"]

        """Opens the lesson type and the lesson timetable JSON files"""
        with open("./data/Lesson Timetable.json") as f:
            global timetable_data
            timetable_data = json.load(f)
        with open("./data/Lesson Type.json") as f:
            global type_data
            type_data = json.load(f)

        self.load_schedule()

    async def lesson_embed(self,*args):
        """Used to create an embed to show lesson info"""
        lesson_ID = args[0]
        item = str(args[1])
        element = args[2]
        school_type = type_data[lesson_ID]["school type"]
        lesson_subject = type_data[lesson_ID]["lesson subject"]
        lesson_teacher = type_data[lesson_ID]["lesson teacher"]
        lesson_link = type_data[lesson_ID]["lesson link"]
        lesson_room = timetable_data[item]["lesson room"]
        start_time = (timetable_data[item]["lesson start"][:-2])+":"+(timetable_data[item]["lesson start"][2:])
        end_time = (timetable_data[item]["lesson end"][:-2])+":"+ (timetable_data[item]["lesson end"][2:])
        FMT = '%H:%M'
        tdelta = datetime.datetime.strptime(end_time,FMT)-datetime.datetime.strptime(start_time,FMT)
        lesson_online = type_data[lesson_ID]["lesson online"]
        embed_int = int((type_data[lesson_ID]["embed colour"]),16)
        embed_colour = int(hex(embed_int),0)
        if lesson_online:
            lesson_embed = discord.Embed(
                title = f"***{lesson_subject} online lesson with {lesson_teacher}***",
                description= f"Start time: `{start_time}`\nEnd time: `{end_time}`",
                url = lesson_link,
                colour = embed_colour
            )
            lesson_embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Google_Meet_icon_%282020%29.svg/934px-Google_Meet_icon_%282020%29.svg.png") # Google meet logo
        elif not lesson_online:
            lesson_embed = discord.Embed(
                title = f"***{lesson_subject} lesson with {lesson_teacher}***",
                description = f"**In {lesson_room}**\nStart time: `{start_time}`\nEnd time: `{end_time}`\nLesson duration: `{tdelta}`",
                colour=embed_colour
            )
            if school_type == "bcot":
                lesson_embed.set_thumbnail(url="https://pbs.twimg.com/profile_images/1086298369327271937/2UfNK52v_400x400.jpg") # BCoT Logo
            elif school_type == "nfs":
                lesson_embed.set_thumbnail(url="https://pbs.twimg.com/profile_images/503551590494531585/iKOwwaiU_400x400.png") # NFS Logo
        if school_type == "bcot":
            await self.bot.get_channel(self.BCoT_lesson_announcement_channel).send(embed=lesson_embed) 
            await self.bot.get_channel(self.BCoT_lesson_announcement_channel).send(f"@everyone your lesson is in {element} minutes")
        elif school_type == "nfs":
            await self.bot.get_channel(self.NFS_lesson_announcement_channel).send(embed=lesson_embed)
    
    async def lesson_warning(self,*args):
        """Sends the lesson warning text"""
        school_type = args[0]
        item = args[1]
        element = args[2]
        if element == 0: # If the lessson is just about to start
            if school_type == "bcot":
                await self.bot.get_channel(self.BCoT_lesson_announcement_channel).send("@everyone your lesson is now!")
            elif school_type == "nfs":
                await self.bot.get_channel(self.NFS_lesson_announcement_channel).send("@everyone your lesson is now!")
            item = str(int(args[1])+1)
            if item == "8":
                item = "0"
            elif item == "39":
                item = "8"
            day_of_week = self.days_of_week[timetable_data[item]["lesson day of week"]].capitalize()
            start_hour = (timetable_data[item]["lesson start"][:-2])
            start_minute = (timetable_data[item]["lesson start"][2:])
            if school_type == "bcot":
                await self.bot.get_channel(self.BCoT_Next_lesson_weekday_channel).edit(name=f'Next lesson: {day_of_week}')
                await self.bot.get_channel(self.BCoT_Next_lesson_time_channel).edit(name=f'Next lesson time: {start_hour}:{start_minute}')
        elif element == 5:
            if school_type == "bcot":
                await self.bot.get_channel(self.BCoT_lesson_announcement_channel).send(f"@everyone your lesson is in {element} minutes!")
                await self.bot.get_channel(self.BCoT_lesson_announcement_channel).send("<@!776817919883083786> finish your cig")

            
        else: # All other lesson warning times
            if school_type == "bcot":
                await self.bot.get_channel(self.BCoT_lesson_announcement_channel).send(f"@everyone your lesson is in {element} minutes!")
            elif school_type == "nfs":
                await self.bot.get_channel(self.NFS_lesson_announcement_channel).send(f"@everyone your lesson is in {element} minutes!")
    
    def load_schedule(self):
        try: # Prevents multiple schedulers running at the same time
            if (self.lesson_scheduler.state) == 1:
                self.lesson_scheduler.shutdown(wait=False)
            self.lesson_scheduler = AsyncIOScheduler()
        except:
            self.lesson_scheduler = AsyncIOScheduler()

        for item in timetable_data:
            lesson_ID = timetable_data[item]["lesson ID"]
            school_type = type_data[lesson_ID]["school type"]
            day_of_week = timetable_data[item]["lesson day of week"]
            start_hour = int(timetable_data[item]["lesson start"][:-2])
            start_minute = int(timetable_data[item]["lesson start"][2:])
            
            for element in self.Lesson_warning_times:
                hour_difference = int(element/60)
                minute_difference = element%60
                minute = start_minute - minute_difference
                if start_minute - minute_difference < 0: # Used to handle the minutes going below 0
                    minute += 60
                    hour_difference += 1
                
                if element == self.Lesson_warning_times[0]:
                    self.lesson_scheduler.add_job(
                        self.lesson_embed,
                        CronTrigger(
                            day_of_week=day_of_week,
                            hour=start_hour-hour_difference,
                            minute=minute,
                            second=0
                        ),
                        args=[lesson_ID,item,element]
                    )
                
                else:
                    self.lesson_scheduler.add_job(
                        self.lesson_warning,
                        CronTrigger(
                            day_of_week=day_of_week,
                            hour=start_hour-hour_difference,
                            minute=minute,
                            second=0
                        ),
                        args=[school_type, item, element]
                )
        self.lesson_scheduler.start()
    
    @command(brief="Sets the alert times for the lesson reminders")
    async def changealert(self,ctx,*,times):
        """Used to change when and how many alert messages are sent before a lesson\n**Usage**\n-changealert 10 5 0\n*Note: ensure that each number is seperated by a space and it always ends in 0"""
        if ctx.author.id == 724351142158401577:
            alert_list = times.split()
            print(alert_list)
            try:
                alert_list = [int(x) for x in alert_list]
            except:
                raise BadArgument
            if alert_list[-1] != 0:
                raise BadArgument
            Bot_Info["Lesson warning times"] = alert_list
            json.dump(Bot_Info, open("./data/Bot_Info.json","w"), indent=4)
            self.load_schedule()
              
    @command(brief="Sends the lessons you have for today")
    async def schedule(self,ctx,*, kwargs="None"):
        """Sends the lessons you have for today"""
        school, date = None,None
        try:
            kwargs = kwargs.lower()
        except:
            raise BadArgument
        kwargs = kwargs.split()
        if len(kwargs) > 2:
            raise BadArgument
        for item in kwargs:
            if item in self.days_of_week:
                date = self.days_of_week.index(item)
            elif item == "tomorrow":
                date = (datetime.datetime.today().weekday()) + 1
                if date == 7:
                    date = 0
            if item in self.schools:
                school = item
            
        if date == None:
            date = (datetime.datetime.today().weekday())
            dateformat = datetime.datetime.today().strftime('%d %B')
        else:
            current_day_of_week = self.days_of_week[(datetime.datetime.today().weekday())]
            date_day_of_week = self.days_of_week[date]
            difference = self.days_of_week.index(date_day_of_week)-self.days_of_week.index(current_day_of_week)
            if difference < 0:
                difference += 7
            full_date = (datetime.datetime.today()) + datetime.timedelta(days=difference)
            dateformat = full_date.strftime('%d %B')
        embed = discord.Embed(
            title=f"Schedule for {self.days_of_week[date].capitalize()}, {dateformat}",
            color = ctx.author.colour
        )
        if school== None:
            if ctx.author.id in self.BCoT_IDS:
                school = "bcot"
            elif ctx.author.id in self.NFS_IDS:
                school = "nfs"
        school = school.lower()
        
        message = ''
        i=0
        for item in (timetable_data):
            if timetable_data[item]["lesson day of week"] == date:
                lesson_ID = timetable_data[item]["lesson ID"]
                if type_data[lesson_ID]["school type"] == school:
                    start_time = (timetable_data[item]["lesson start"])[:2]+":"+(timetable_data[item]["lesson start"])[2:]
                    end_time = (timetable_data[item]["lesson end"])[:2]+":"+(timetable_data[item]["lesson end"])[2:]
                    lesson_teacher = type_data[lesson_ID]["lesson teacher"]
                    lesson_link = type_data[lesson_ID]["lesson link"]
                    lesson_type = type_data[lesson_ID]["lesson subject"]
                    lesson_online = type_data[lesson_ID]["lesson online"]
                    lesson_room = timetable_data[item]["lesson room"]
                    print(lesson_room, lesson_ID)
                    message = f"Lesson Type: `{lesson_type}`\nLesson teacher: `{lesson_teacher}`\nStart time: `{start_time}`\nEnd time: `{end_time}`\n"
                    i +=1
                    if int(timetable_data[item]["lesson start"]) == 1105:
                            i = 2
                    if lesson_online:
                        embed.add_field(name=f"Lesson {i}:", value = (message)+(f'Lesson link: [[Click here]]({lesson_link})'), inline=False)
                    elif not lesson_online:
                        embed.add_field(name=f"Lesson {i}:", value = (message)+(f"Lesson room: `{lesson_room}`"), inline=False)
        if message == '':
            embed.add_field(name="No lessons found",value="You don't have any lessons for today\nUse `-nextlesson` to show your next lesson",inline=True)
        embed.set_author(name= ctx.author, icon_url = ctx.author.avatar_url)
        await ctx.send(embed=embed)
        Bot.log_command(ctx.author,f"checked the schedule for {school} on {self.days_of_week[date]}")
    @command(brief="Shows the lesson information for your next lesson")
    async def nextlesson(self,ctx,school="None"):
        """Shows the lesson information for your next lesson"""
        date = (datetime.datetime.today().weekday())
        print(date)
        global message
        message = ''
        current_time = int(time.strftime("%H%M"))
        
        if school=="None":
            if ctx.author.id in self.BCoT_IDS:
                school = "bcot"
            elif ctx.author.id in self.NFS_IDS:
                school = "nfs"
        school = school.lower()

        def check(day,timestamp,school):
            global start_time, end_time
            for item in timetable_data:
                if timetable_data[item]["lesson day of week"] == day:
                    lesson_ID = timetable_data[item]["lesson ID"]
                    lesson_school = type_data[lesson_ID]["school type"]
                    lesson_start = (timetable_data[item]["lesson start"])
                    lesson_start_int = int(lesson_start)
                    if timestamp <= lesson_start_int and lesson_school == school:
                        start_time = (timetable_data[item]["lesson start"])[:2]+":"+(timetable_data[item]["lesson start"])[2:]
                        end_time = (timetable_data[item]["lesson end"])[:2]+":"+(timetable_data[item]["lesson end"])[2:]
                        lesson_teacher = type_data[lesson_ID]["lesson teacher"]
                        
                        global lesson_link, lesson_online, lesson_room
                        lesson_room = timetable_data[item]["lesson room"]
                        lesson_online = type_data[lesson_ID]["lesson online"]
                        lesson_link = type_data[lesson_ID]["lesson link"]
                        lesson_type = type_data[lesson_ID]["lesson subject"]
                        lesson_day_of_week = self.days_of_week[(timetable_data[item]["lesson day of week"])].capitalize()
                        message = f"Lesson day: `{lesson_day_of_week}`\nLesson Type: `{lesson_type}`\nLesson teacher: `{lesson_teacher}`\nStart time: `{start_time}`\nEnd time: `{end_time}`\n"
                        return message
            return ''

        while message == '':
            if date == 7:
                date =0
            message = check(date,current_time,school)
            date +=1
            current_time = 0000

        embed = discord.Embed(
            title=f"Next lesson is at `{start_time}`",
            color = ctx.author.colour
        )
        if lesson_online:
            embed.add_field(name=f"Showing next lesson:", value = (message)+(f'Lesson link: [[Click here]]({lesson_link})'), inline=False)
        elif not lesson_online:
            embed.add_field(name=f"Showing next lesson:", value = (message)+(f"Lesson room: `{lesson_room}`"), inline=False)
        embed.set_author(name= ctx.author, icon_url = ctx.author.avatar_url)
        await ctx.send(embed=embed)
        Bot.log_command(ctx.author,f"checked the next lesson for {school}")
        pass

    @command(brief="Shows the current lesson information")
    async def currentlesson(self,ctx):
        print("Test")
        current_date = (datetime.datetime.today().weekday())
        current_time = datetime.datetime.now()
        current_time = current_time.strftime("%H%M")
        print(current_date)
        # for item in timetable_data:
        #     if item["lesson day of week"] == current_date:
        #         print("test")
        #         if int(item["lesson start"]) <= current_time and current_time <= int(item["lesson end"]):
        #             await ctx.send("Test")
    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("lesson_scheduler")
        print("Lesson Scheduler cog ready!")
        await self.bot.stdout.send("Lesson Scheduler cog working!")        
    

def setup(bot):
    bot.add_cog(Lesson_Schedule(bot))

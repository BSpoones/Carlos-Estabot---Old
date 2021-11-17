import discord
from lib.bot import Bot
from datetime import datetime
from random import choice
from discord.ext.commands import Cog
from discord.ext.commands import command
from typing import Optional
from PyDictionary import PyDictionary

class Misc(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command(name="coord", aliases=["coords"],brief="Displays a hyperlinked embed of google maps coordinates")
    async def coord(self, ctx,*,coords):
        """Displays a hyperlinked embed of google maps coordinates"""
        coordlist = coords.split()
        try:
            coord = ('https://www.google.co.uk/maps/place/'+coordlist[0]+coordlist[1])
        except:
            coord =('https://www.google.co.uk/maps/place/'+coordlist[0])

        embed = discord.Embed(
            title="***Google maps coords***",
            description="Click the title",
            url=coord,
            color = ctx.author.colour
        )
        embed.set_author(name= ctx.author, icon_url = ctx.author.avatar_url)
        embed.set_thumbnail(url="https://storage.googleapis.com/gweb-uniblog-publish-prod/images/Maps_Pin_FullColor.max-1000x1000.png")
        await ctx.send(embed=embed)
        Bot.log_command(ctx.author,f"Checked coords of {coordlist}")

    @command(brief="Finds the user information of a user or yourself")
    async def userinfo(self,ctx, target: Optional[discord.Member]):
        """Finds the user information of a user or yourself"""
        target = target or ctx.author

        embed = discord.Embed(title="User information",
                    colour=target.colour,
                    timestamp=datetime.utcnow())

        embed.set_thumbnail(url=target.avatar_url)

        fields = [("Name", str(target), True),
                ("ID", target.id, True),
                ("Bot?", target.bot, True),
                ("Top role", target.top_role.mention, True),
                ("Status", str(target.status).title(), True),
                ("Activity", f"{str(target.activity.type).split('.')[-1].title() if target.activity else 'N/A'} {target.activity.name if target.activity else ''}", True),
                ("Created at", target.created_at.strftime("%d/%m/%Y %H:%M:%S"), True),
                ("Joined at", target.joined_at.strftime("%d/%m/%Y %H:%M:%S"), True),
                ("Boosted", bool(target.premium_since), True)]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        await ctx.send(embed=embed)
        Bot.log_command(ctx.author,f"Did -userinfo on {target}")

    @command(brief="Gets the server information of the current server")
    async def serverinfo(self, ctx):
        """Gets the server information of the current server"""
        embed = discord.Embed(title="Server information",
                        colour=discord.Color.green(),
                        timestamp=datetime.utcnow())

        embed.set_thumbnail(url=ctx.guild.icon_url)

        statuses = [len(list(filter(lambda m: str(m.status) == "online", ctx.guild.members))),
                    len(list(filter(lambda m: str(m.status) == "idle", ctx.guild.members))),
                    len(list(filter(lambda m: str(m.status) == "dnd", ctx.guild.members))),
                    len(list(filter(lambda m: str(m.status) == "offline", ctx.guild.members)))]

        fields = [("ID", ctx.guild.id, True),
                    ("Owner", ctx.guild.owner, True),
                    ("Region", ctx.guild.region, True),
                    ("Created at", ctx.guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), True),
                    ("Members", len(ctx.guild.members), True),
                    ("Humans", len(list(filter(lambda m: not m.bot, ctx.guild.members))), True),
                    ("Bots", len(list(filter(lambda m: m.bot, ctx.guild.members))), True),
                    ("Banned members", len(await ctx.guild.bans()), True),
                    ("Statuses", f"{statuses[0]} {statuses[1]} {statuses[2]} {statuses[3]}", True),
                    ("Text channels", len(ctx.guild.text_channels), True),
                    ("Voice channels", len(ctx.guild.voice_channels), True),
                    ("Categories", len(ctx.guild.categories), True),
                    ("Roles", len(ctx.guild.roles), True),
                    ("Invites", len(await ctx.guild.invites()), True),
                    ("\u200b", "\u200b", True)]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        await ctx.send(embed=embed)
        Bot.log_command(ctx.author,f"Did -serverinfo")
    @command(brief="Sends a dictionary definition of a word")
    async def define(self,ctx,*,word):
        """Sends a dictionary definition of a word"""
        dictionary = PyDictionary()
        embed = discord.Embed(
            title=f"**Defintion of: `{word}`**",
            color = ctx.author.colour
            )
                   
        definition = dictionary.meaning(word)
        if definition is not None:
            newkeys = definition.keys()
            newmsg = definition.values()
            
            for item in zip(newkeys,newmsg):
                message = ""
                word_type=(item[0])
                for chr in item[1][:2]:
                    message +="- "+(chr.capitalize())
                    message += "\n"
            embed.add_field(name=word_type,value=message,inline=False)
            embed.set_author(name= ctx.author, icon_url = ctx.author.avatar_url)
            await ctx.send(embed=embed)
            Bot.log_command(ctx.author,f"Looked up the meaning of {word}")
        if definition is None:
            await ctx.send("That word does not exist, check the spelling")

    @command(brief="Backs up all messages in a chat")
    async def backup(self,ctx):
        channel = self.bot.get_channel(ctx.channel.id)
        print(channel.history(limit=2))
        async for msg in channel.history(limit=10):
            if msg.content != "":
                print(msg.content, msg.created_at)
            else:
                print(msg.attachments)
    @command()
    async def leave(self,ctx):
        await ctx.send("Leaving guild")
        my_guild = self.bot.get_guild(0) # Guild ID redacted
        await my_guild.leave()

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("misc")
        print("Misc cog ready!")
        await self.bot.stdout.send("Misc cog working!")

def setup(bot):
    bot.add_cog(Misc(bot))

import discord
from lib.bot import Bot, bot
from random import choice
from discord.ext.commands import Cog
from discord.ext.commands import command
from typing import Union
from discord_slash import SlashCommand, SlashCommandOptionType, SlashContext

slash = SlashCommand(bot,sync_commands=True)
class Fun(Cog):
    def __init__(self, bot):
        self.bot = bot
        
        
    
    @command(name="hello", aliases=["hi"])
    async def say_hello(self, ctx):
        """Says hi to the bot. The bot might say hi back but it depends on wether or not you annoyed him"""
        Bot.log_command(ctx.author,f"-hi")
        await ctx.send(f"{choice(('Hello', 'Hi', 'Hey', 'Hiya','Hallo'))} {ctx.author.mention}!")
        
    @slash.slash(name="Brexit",description="Types out brexit emojis into chat",guild_ids=[694842694278578206],options={})
    @command(brief="Types out brexit emojis into chat")
    async def brexit(self, ctx: SlashContext):
        """Types out brexit emojis into the chat"""
        # await ctx.channel.purge(limit=1)
        await ctx.send(content="<:slumberparty:795657529744818187> <:brexit1:784428111092645890><:brexit2:784428111319138304><:brexit3:784428111402893323><:brexit4:784428111466594305> <:slumberparty:795657529744818187>")
        Bot.log_command(ctx.author,f"-brexit")
    @command(brief="Shows a hackerman GIF")
    async def hackerman(self, ctx):
        """Shows a hackerman GIF"""
        await ctx.channel.purge(limit=1)
        await ctx.send("https://giphy.com/gifs/YQitE4YNQNahy")
        Bot.log_command(ctx.author,f"-hackerman")

    @command(brief="Enlarges an emoji.")
    async def big(self,ctx, emoji: Union[discord.Emoji, discord.PartialEmoji]):
        """Enlarges an emoji. NOTE: Does not work with default discord emoji"""
        await ctx.channel.purge(limit=1)
        embed = discord.Embed(
            title ="**One big fat juicy emoji coming your way**",
            color = ctx.author.color
            )
        embed.set_image(url=emoji.url)
        embed.set_author(name= ctx.author, icon_url = ctx.author.avatar_url)
        await ctx.send(embed=embed)
        Bot.log_command(ctx.author,f"-big {emoji}")
    @command(brief="Enlarges :thonk: onto chat",aliases=["bigthonk"])
    async def thonk(self,ctx):
        """Enlarges :thonk: onto chat"""
        await ctx.channel.purge(limit=1)
        await ctx.send("https://cdn.discordapp.com/emojis/758717582773190676.png?v=1")
        Bot.log_command(ctx.author,f"-thonk")
    @command(brief="Puts a horny jail meme into chat")
    async def bonk(self,ctx):
        """Bonk! Go to horny jail"""
        await ctx.channel.purge(limit=1)
        await ctx.send("https://i.kym-cdn.com/entries/icons/facebook/000/033/758/Screen_Shot_2020-04-28_at_12.21.48_PM.jpg")
        Bot.log_command(ctx.author,f"-bonk")
    @command(brief="Enlarges :sponk: into chat")
    async def sponk(self,ctx):
        """Enlarges :sponk: into chat"""
        await ctx.channel.purge(limit=1)
        await ctx.send("https://cdn.discordapp.com/emojis/802260617095282700.png?v=1")
        Bot.log_command(ctx.author,f"-sponk")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up("fun")
        print("Fun cog ready!")
        await self.bot.stdout.send("Fun cog working!")
        

    
def setup(bot):
    bot.add_cog(Fun(bot))


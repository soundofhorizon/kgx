from discord.ext import commands, tasks
import discord


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.presence_change_task.start()

    @tasks.loop(seconds=20)
    async def presence_change_task(self):
        game = discord.Game(f"{self.bot.get_guild(558125111081697300).member_count}人を監視中")
        await self.bot.change_presence(status=discord.Status.online, activity=game)


def setup(bot):
    bot.add_cog(Loops(bot))

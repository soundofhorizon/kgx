import discord
from discord.ext import commands


class SimpleCommand(commands.Cog):
    """引数を持たないコマンド"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.message.content == ctx.prefix + ctx.invoked_with

    @commands.command()
    async def version(self, ctx):
        if not self.bot.is_normal_category(ctx) and not self.bot.is_auction_category(ctx):
            embed = discord.Embed(description="現在のバージョンは**6.0.0**です\nNow version **5.0.0** working.", color=0x4259fb)
            await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        if not self.bot.is_normal_category(ctx) and not self.bot.is_auction_category(ctx):
            await ctx.send('招待用URL:https://discord.gg/4UXtw5hB9K')


def setup(bot):
    bot.add_cog(SimpleCommand(bot))

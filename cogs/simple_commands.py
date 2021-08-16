from discord.ext import commands
import discord
from discord_slash import cog_ext

from kgx.bot import KGX


class SimpleCommand(commands.Cog):
    """引数を持たないコマンド"""
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.message.content == ctx.prefix + ctx.invoked_with

    @cog_ext.cog_slash(name="version",
                       guild_ids=KGX.guild_id,
                       description="現在のbotのバージョンを返します。",
                       permissions=KGX.permisson_verified
                       )
    async def version(self, ctx):
        if not self.bot.is_normal_category(ctx) and not self.bot.is_auction_category(ctx):
            embed = discord.Embed(description="現在のバージョンは**6.0.0**です\nNow version **6.0.0** working.", color=0x4259fb)
            await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="invite",
                       guild_ids=KGX.guild_id,
                       description="KGxサーバーへの招待リンクを表示します。",
                       permissions=KGX.permisson_verified
                       )
    async def invite(self, ctx):
        if not self.bot.is_normal_category(ctx) and not self.bot.is_auction_category(ctx):
            await ctx.send('招待用URL:https://discord.gg/Syp85R4')


def setup(bot):
    bot.add_cog(SimpleCommand(bot))

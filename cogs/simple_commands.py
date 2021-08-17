import discord
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_permission


class SimpleCommand(commands.Cog):
    """引数を持たないコマンド"""

    def __init__(self, bot):
        self.bot = bot

    guild_id = [558125111081697300]

    permisson_verified = {
        558125111081697300: [
            create_permission(558999306204479499, SlashCommandPermissionType.ROLE, True),
            create_permission(678502401723990046, SlashCommandPermissionType.ROLE, False)
        ]
    }

    permisson_not_verified = {
        558125111081697300: [
            create_permission(558999306204479499, SlashCommandPermissionType.ROLE, False),
            create_permission(678502401723990046, SlashCommandPermissionType.ROLE, True)
        ]
    }

    async def cog_check(self, ctx):
        return ctx.message.content == ctx.prefix + ctx.invoked_with

    @cog_ext.cog_slash(name="version",
                       guild_ids=guild_id,
                       description="現在のbotのバージョンを返します。",
                       permissions=permisson_verified
                       )
    async def version(self, ctx):
        if not self.bot.is_normal_category(ctx) and not self.bot.is_auction_category(ctx):
            embed = discord.Embed(description="現在のバージョンは**6.0.0**です\nNow version **5.0.0** working.", color=0x4259fb)
            await ctx.send(embed=embed, hidden=True)

    @cog_ext.cog_slash(name="invite",
                       guild_ids=guild_id,
                       description="KGxサーバーへの招待リンクを表示します。",
                       permissions=permisson_verified
                       )
    async def invite(self, ctx):
        if not self.bot.is_normal_category(ctx) and not self.bot.is_auction_category(ctx):
            await ctx.send('招待用URL:https://discord.gg/4UXtw5hB9K', hidden=True)


def setup(bot):
    bot.add_cog(SimpleCommand(bot))

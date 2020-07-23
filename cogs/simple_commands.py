from discord.ext import commands
import discord


class SimpleCommand(commands.Cog):

    """引数を持たないコマンド"""
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return ctx.message.content == ctx.prefix + ctx.invoked_with

    @commands.command()
    async def version(self, ctx):
        if not self.bot.is_normal_category(ctx) and not self.bot.is_auction_category(ctx):
            embed = discord.Embed(description="現在のバージョンは**5.0.0**です\nNow version **5.0.0** working.", color=0x4259fb)
            await ctx.send(embed=embed)

    @commands.command()
    async def invite(self, ctx):
        if not self.bot.is_normal_category(ctx) and not self.bot.is_auction_category(ctx):
            await ctx.send('招待用URL:https://discord.gg/Syp85R4')

    @commands.command()
    async def help(self, ctx):
        description = "<:shiina_balance:558175954686705664>!start\n\n" \
                      "オークションを始めるためのコマンドです。オークションチャンネルでのみ使用可能です。\n" \
                      "-------\n" \
                      "<:siina:558251559394213888>!bid\n\n" \
                      "オークションが終わったときにオークション内容を報告するためのコマンドです。\n" \
                      "ここで報告した内容は <#558132754953273355> に表示されます\n" \
                      "-------\n" \
                      "<:shiina_balance:558175954686705664>!end\n\n" \
                      "取引を終了するためのコマンドです。\n" \
                      "-------\n" \
                      "<:siina:558251559394213888>!bidscore 申請する落札ポイント\n\n" \
                      "落札ポイントを申請します。 <#558265536430211083> に入力すると申請できます。\n" \
                      "<#602197766218973185> に現在の落札ポイントが通知されます。\n" \
                      "<#677905288665235475> に現在の落札ポイントのランキングが表示されます。\n\n" \
                      "(例)!bidscore 2 {これで、自分の落札ポイントが2ポイント加算される。}\n" \
                      "-------\n" \
                      "<:shiina_balance:558175954686705664>!version\n\n" \
                      "現在のBotのバージョンを表示します。\n" \
                      "-------\n" \
                      "<:siina:558251559394213888>!help\n" \
                      "このBotのヘルプを表示します。\n" \
                      "-------\n"
        embed = discord.Embed(description=description, color=0x66cdaa)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(SimpleCommand(bot))

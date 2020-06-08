import asyncio
from discord.ext import commands
import discord
import os
import redis
import re

# Redisに接続
pool = redis.ConnectionPool.from_url(
    url=os.environ['REDIS_URL'],
    db=0,
    decode_responses=True
)

rc = redis.StrictRedis(connection_pool=pool)

# Redisに接続
pool2 = redis.ConnectionPool.from_url(
    url=os.environ['HEROKU_REDIS_ORANGE_URL'],
    db=0,
    decode_responses=True
)

rc2 = redis.StrictRedis(connection_pool=pool2)


class AdminOnly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):  # cog内のコマンド全てに適用されるcheck
        if discord.utils.get(ctx.author.roles, name="Administrator"):
            return True
        await ctx.send('運営以外のコマンド使用は禁止です')

    @commands.command(name='del')
    async def _del(self, ctx, n):  # メッセージ削除用
        p = re.compile(r'^[0-9]+$')
        if p.fullmatch(n):
            kazu = int(n)
            await ctx.channel.purge(limit=kazu + 1)

    @commands.command()
    async def check_all_user_ID(self, ctx):
        channel = self.bot.get_channel(642052474672250880)
        bot_count = 0
        for member in range(self.bot.get_guild(558125111081697300).member_count):
            if self.bot.get_guild(558125111081697300).members[member].bot:
                bot_count += 1
                continue
            await channel.send(
                f"{self.bot.get_guild(558125111081697300).members[member].id} : "
                f"{self.bot.get_guild(558125111081697300).members[member].display_name}")
            if member == (self.bot.get_guild(558125111081697300).member_count - 1):
                embed = discord.Embed(
                    description=f"このサーバーの全メンバーのユーザーIDの照会が終わりました。 現在人数:{member - bot_count + 1}",
                    color=0x1e90ff)
                await channel.send(embed=embed)
                await channel.send("--------ｷﾘﾄﾘ線--------")

    @commands.command()
    async def bidscore_ranking(self, ctx):
        channel = self.bot.get_channel(677905288665235475)
        # とりあえず、ランキングチャンネルの中身を消す
        await channel.purge(limit=1)
        await channel.send(embed=self.bot.create_ranking_embed())
        await asyncio.sleep(0.3)
        embed = discord.Embed(
            description=f"このサーバーの全メンバーの落札ポイントの照会が終わりました。"
                        f"\nランキングを出力しました。 ",
            color=0x1e90ff
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def show_bid_ranking(self, ctx):
        await self.bot.get_channel(705040893593387039).purge(limit=10)
        await asyncio.sleep(0.1)
        embed = self.bot.create_high_bid_ranking()
        for i in range(len(embed)):
            await self.bot.get_channel(705040893593387039).send(embed=embed[i])

    @commands.group(invoke_without_command=True)  # サブコマンドがない場合のみ実行
    async def bidscoreGS(self, ctx):
        await ctx.send(f'{ctx.prefix}bidscoreGS [get, set]')

    @bidscoreGS.command()
    async def get(self, ctx, user_id):
        r = redis.from_url(os.environ['REDIS_URL'])  # os.environで格納された環境変数を引っ張ってくる
        get_score = int(r.get(f"score-{user_id}" or "0"))
        embed = discord.Embed(description=f"ユーザーID：{user_id}の落札ポイントは{get_score}です。",
                              color=0x1e90ff)
        await ctx.send(embed=embed)

    @bidscoreGS.command()
    async def set(self, ctx, user_id, pt):
        r = redis.from_url(os.environ['REDIS_URL'])  # os.environで格納された環境変数を引っ張ってくる
        user = self.bot.get_user(int(user_id))
        r.set(f"score-{user_id}", pt)
        embed = discord.Embed(
            description=f"{ctx.author.display_name}により、ユーザー名：{user.display_name}"
                        f"の落札ポイントを{pt}にセットしました。",
            color=0x1e90ff)
        await ctx.channel.send(embed=embed)

        channel = self.bot.get_channel(677905288665235475)
        # とりあえず、ランキングチャンネルの中身を消す
        await channel.purge(limit=1)
        await channel.send(embed=self.bot.create_ranking_embed())
        channel = self.bot.get_channel(602197766218973185)
        embed = discord.Embed(
            description=f"{ctx.author.display_name}により、{user.display_name}"
                        f"の落札ポイントが{pt}にセットされました。",
            color=0xf04747
        )
        await channel.send(embed=embed)

    @commands.command()
    async def stop_deal(self, ctx):
        embed = discord.Embed(
            description=f"{ctx.author.display_name}によりこの取引は停止させられました。",
            color=0xf04747
        )
        await ctx.channel.send(embed=embed)
        await ctx.channel.send('--------ｷﾘﾄﾘ線--------')
        await ctx.channel.edit(name=ctx.channel.name + '☆')

    @commands.command()
    async def insert_ranking_data(self, ctx):
        def check(m):
            return m.channel == ctx.channel

        await ctx.channel.send("データを入力してください")
        data = await self.bot.wait_for("message", check=check)
        i = 0
        r = redis.from_url(os.environ['HEROKU_REDIS_ORANGE_URL'])
        while True:
            # keyに値がない部分まで管理IDを+
            if r.get(i):
                i += 1
            else:
                key = i
                break
        r.set(int(key), str(data.content))
        await ctx.channel.send(f"データ: {data.content}を入力しました。")

    @commands.command()
    async def star_delete(self, ctx):
        embed = discord.Embed(
            description=f"{ctx.author.display_name}により☆を強制的に取り外しました。",
            color=0xf04747
        )
        await ctx.channel.send(embed=embed)
        await ctx.channel.edit(name=ctx.channel.name.split('☆')[0])


def setup(bot):
    bot.add_cog(AdminOnly(bot))

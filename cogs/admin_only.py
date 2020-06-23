import asyncio
import datetime
import os
import re

import discord
import psycopg2
from discord.ext import commands

SQLpath = os.environ["DATABASE_URL"]
db = psycopg2.connect(SQLpath)  # sqlに接続
cur = db.cursor()  # なんか操作する時に使うやつ


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
    async def bid_task(self, ctx):
        # 終わるの早いやつ1つ取ってくる
        cur.execute("SELECT * from auction ORDER BY auction_end_time ASC")
        auction_data = cur.fetchone()
        auction_end_time = datetime.datetime.strptime(auction_data[6], '%Y/%m/%d-%H:%M')
        cur.execute("SELECT * from deal ORDER BY deal_end_time ASC")
        deal_data = cur.fetchone()
        deal_end_time = datetime.datetime.strptime(deal_data[5], '%Y/%m/%d-%H:%M')
        if auction_end_time <= datetime.datetime.now():
            cur.execute("SELECT * from tend WHERE ch_id = %s", (auction_data[0], ))
            tend_data = cur.fetchone()
            if tend_data[0] == 0:
                await self.bot.get_channel(id=int(auction_data[0])).send(f"{self.bot.get_user(id=int(auction_data[1])).mention}さん、入札者は…誰一人いませんでした…\nオークションを終了します")
                await self.bot.get_channel(id=int(auction_data[0])).send("--------ｷﾘﾄﾘ線--------")
                self.bot.reset_ch_db(auction_data[0], "a")
                return
            else:
                await self.bot.get_channel(id=int(auction_data[0])).send(f"{self.bot.get_user(id=int(auction_data[1])).mention}さん、{self.bot.get_user(id=int(tend_data[1])).mention}さんの落札で終了です。")
                await self.bot.get_channel(id=int(auction_data[0])).send("--------ｷﾘﾄﾘ線--------")

            # 椎名カテゴリならランキングを更新
            if "椎名" in self.bot.get_channel(id=int(auction_data[0])).name:
                # INSERTを実行。%sで後ろのタプルがそのまま代入される
                cur.execute("INSERT INTO bid_ranking VALUES (%s, %s, %s, %s)",
                            (self.bot.get_user(id=int(tend_data[1])).display_name, auction_data[3], tend_data[2], self.bot.get_user(id=int(auction_data[1])).display_name))
                db.commit()
                await asyncio.sleep(0.1)
                embed = self.bot.create_high_bid_ranking()
                for i in range(len(embed)):
                    await self.bot.get_channel(705040893593387039).send(embed=embed[i])

            # 記録送信
            channel = self.bot.get_channel(558132754953273355)
            d = datetime.datetime.now()  # 現在時刻の取得
            time = d.strftime("%Y/%m/%d")
            embed = discord.Embed(title="オークション取引結果", color=0x36a64f)
            embed.add_field(name="落札日", value=f'\n\n{time}', inline=False)
            embed.add_field(name="出品者", value=f'\n\n{self.bot.get_user(id=int(auction_data[1])).display_name}', inline=False)
            embed.add_field(name="品物", value=f'\n\n{auction_data[3]}', inline=False)
            embed.add_field(name="落札者", value=f'\n\n{self.bot.get_user(id=int(tend_data[1])).display_name}', inline=False)
            embed.add_field(name="落札価格", value=f'\n\n{auction_data[7]}{self.bot.stack_check_reverse(self.bot.stack_check(int(tend_data[2])))}', inline=False)
            embed.add_field(name="チャンネル名", value=f'\n\n{self.bot.get_channel(id=auction_data[0]).name}', inline=False)
            await channel.send(embed=embed)

            # 各種db削除
            self.bot.reset_ch_db(auction_data[0], "a")

        elif deal_end_time <= datetime.datetime.now():
            await self.bot.get_channel(id=int(auction_data[0])).send(f"{self.bot.get_user(id=int(auction_data[1])).mention}さん、取引は成立しませんでした…")
            self.bot.reset_ch_db(deal_data[0], "d")


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


@commands.command()
async def stop_deal(self, ctx):
    # dbのリセット
    if ">" in ctx.channel.category.name:
        self.bot.reset_ch_db(ctx.channel.id, "a")
    elif "*" in ctx.channel.category.name:
        self.bot.reset_ch_db(ctx.channel.id, "d")

    embed = discord.Embed(
        description=f"{ctx.author.display_name}によりこの取引は停止させられました。",
        color=0xf04747
    )
    await ctx.channel.send(embed=embed)
    await ctx.channel.edit(name=ctx.channel.name + '☆')
    await ctx.channel.send('--------ｷﾘﾄﾘ線--------')


@commands.command()
async def star_delete(self, ctx):
    embed = discord.Embed(
        description=f"{ctx.author.display_name}により☆を強制的に取り外しました。",
        color=0xf04747
    )
    await ctx.channel.send(embed=embed)
    await ctx.channel.edit(name=ctx.channel.name.split('☆')[0])


@commands.command()
async def execute_sql(self, ctx, *, content):
    cur.execute(content)
    data = cur.fetchone()
    if len(data) == 0:
        return await ctx.send(f'SQL文`{content}`は正常に実行されました')
    embed = discord.Embed(title="SQL文の実行結果", description=''.join(f"{d}、" for d in data))
    await ctx.send(embed=embed)


@commands.group(invoke_without_command=True)
async def user_caution(self, ctx):
    await ctx.send(f'{ctx.prefix}user_caution [set, get]')


@user_caution.command()
async def get(self, ctx, user: discord.Member):
    cur.execute("SELECT warn_level FROM user_data WHERE user_id = %s", (user.id,))
    data = cur.fetchone()
    caution_level = data[0]
    await ctx.send(f"{user}の警告レベルは{caution_level}です")


@user_caution.command()
async def set(self, ctx, user: discord.Member, n: int):
    cur.execute("UPDATE user_data SET warn_level = %s WHERE user_id = %s", (n, user.id))
    db.commit()
    await ctx.send(f'{user}に警告レベル{n}を付与しました')


@commands.group(invoke_without_command=True)
async def bidGS(self, ctx):
    await ctx.send(f'{ctx.prefix}score [set, get]')


@bidGS.command(name="get")
async def _get(self, ctx, user: discord.Member):
    cur.execute("SELECT bid_score FROM user_data WHERE user_id = %s", (user.id,))
    data = cur.fetchone()
    await ctx.send(f"{user}の落札ポイントは{data[0]}です")


@bidGS.command(name="set")
async def _set(self, ctx, user: discord.Member, n: int):
    cur.execute("UPDATE user_data SET bid_score = %s WHERE user_id = %s", (n, user.id))
    db.commit()
    await ctx.send(f'{user.display_name}の落札ポイントを{n}にセットしました')

    channel = self.bot.get_channel(677905288665235475)
    # とりあえず、ランキングチャンネルの中身を消す
    await channel.purge(limit=1)
    await channel.send(embed=self.bot.create_ranking_embed())
    channel = self.bot.get_channel(602197766218973185)
    embed = discord.Embed(
        description=f"{ctx.author.display_name}により、{user.display_name}"
                    f"の落札ポイントが{n}にセットされました。",
        color=0xf04747
    )
    await channel.send(embed=embed)


@commands.command()
async def get_auction_and_deal_ch_id(self, ctx):
    ch_category_1 = list({c.id for c in ctx.guild.categories if c.name.startswith('>')})
    ch_list_1 = list({a.id for a in ctx.guild.text_channels if a.category_id in ch_category_1})
    ch_category_2 = list({this.id for this in ctx.guild.categories if this.name.startswith('*')})
    ch_list_2 = list({b.id for b in ctx.guild.text_channels if b.category_id in ch_category_2})
    await ctx.send("auction\n------")
    for i in range(len(ch_list_1)):
        await ctx.send(
            f"INSERT INTO tend VALUES ({ch_list_1[i]}, 0, 0);")
    await ctx.send("deal\n------")
    for i in range(len(ch_list_2)):
        await ctx.send(
            f"INSERT INTO deal VALUES ({ch_list_2[i]}, 0, 0, 'undefined', 'undefined', 'undefined', 'undefined');")


@commands.command()
async def test(self, ctx):
    cur.execute("SELECT embed_message_id FROM auction WHERE ch_id = %s", (ctx.channel.id,))
    embed_id = cur.fetchone()
    delete_ch = ctx.channel
    msg = await delete_ch.fetch_message(embed_id[0])
    await delete_ch.purge(limit=None, after=msg)


def setup(bot):
    bot.add_cog(AdminOnly(bot))

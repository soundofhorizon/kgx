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
        if discord.utils.get(ctx.author.roles, id=558138575225356308):  # developer
            return True
        await ctx.send('運営以外のコマンド使用は禁止です')
        return False

    @commands.command(name='del')
    async def _del(self, ctx, n):  # メッセージ削除用
        p = re.compile(r'^[0-9]+$')
        if p.fullmatch(n):
            count = int(n)
            await ctx.channel.purge(limit=count + 1)

    @commands.command()
    async def check_all_user_ID(self, ctx):
        channel = self.bot.get_channel(642052474672250880)
        guild = self.bot.get_guild(558125111081697300)
        bot_count = 0
        for member in guild.members:
            if member.bot:
                bot_count += 1
                continue
            await channel.send(
                f"{member.id} : "
                f"{member.display_name}")
            if member == guild.members[-1]:
                embed = discord.Embed(
                    description=f"このサーバーの全メンバーのユーザーIDの照会が終わりました。 現在人数:{len(guild.members) - bot_count}",
                    color=0x1e90ff)
                await channel.send(embed=embed)
                await channel.send("--------ｷﾘﾄﾘ線--------")

    @commands.command()
    async def bid_task(self, ctx):
        # 終わるの早いやつ1つ取ってくる
        cur.execute("SELECT * from auction ORDER BY auction_end_time ASC")
        auction_data = cur.fetchone()
        auction_end_time = "null"
        if auction_data[1] != 0:
            auction_end_time = datetime.datetime.strptime(auction_data[6], '%Y/%m/%d-%H:%M')
        cur.execute("SELECT * from deal ORDER BY deal_end_time ASC")
        deal_data = cur.fetchone()
        deal_end_time = "null"
        if deal_data[1] != 0:
            deal_end_time = datetime.datetime.strptime(deal_data[5], '%Y/%m/%d-%H:%M')
        # オークション、取引どちらともnullならここで処理終わり
        if auction_end_time == "null" and deal_end_time == "null":
            return
        if auction_end_time <= datetime.datetime.now():
            cur.execute("SELECT * from tend WHERE ch_id = %s", (auction_data[0],))
            tend_data = cur.fetchone()
            if tend_data[0] == 0:
                await self.bot.get_channel(id=int(auction_data[0])).send(
                    f"{self.bot.get_user(id=int(auction_data[1])).mention}さん、入札者は…誰一人いませんでした…\nオークションを終了します")
                await self.bot.get_channel(id=int(auction_data[0])).send("--------ｷﾘﾄﾘ線--------")
                self.bot.reset_ch_db(auction_data[0], "a")
                return
            else:
                await self.bot.get_channel(id=int(auction_data[0])).send(
                    f"{self.bot.get_user(id=int(auction_data[1])).mention}さん、{self.bot.get_user(id=int(tend_data[1])).mention}さんの落札で終了です。")
                await self.bot.get_channel(id=int(auction_data[0])).send("--------ｷﾘﾄﾘ線--------")

            # 椎名カテゴリならランキングを更新
            if "椎名" in self.bot.get_channel(id=int(auction_data[0])).name:
                # INSERTを実行。%sで後ろのタプルがそのまま代入される
                cur.execute("INSERT INTO bid_ranking VALUES (%s, %s, %s, %s)",
                            (self.bot.get_user(id=int(tend_data[1])).display_name, auction_data[3], tend_data[2],
                             self.bot.get_user(id=int(auction_data[1])).display_name))
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
            embed.add_field(name="出品者", value=f'\n\n{self.bot.get_user(id=int(auction_data[1])).display_name}',
                            inline=False)
            embed.add_field(name="品物", value=f'\n\n{auction_data[3]}', inline=False)
            embed.add_field(name="落札者", value=f'\n\n{self.bot.get_user(id=int(tend_data[1])).display_name}',
                            inline=False)
            embed.add_field(name="落札価格",
                            value=f'\n\n{auction_data[7]}{self.bot.stack_check_reverse(self.bot.stack_check(int(tend_data[2])))}',
                            inline=False)
            embed.add_field(name="チャンネル名", value=f'\n\n{self.bot.get_channel(id=auction_data[0]).name}', inline=False)
            await channel.send(embed=embed)

            # 各種db削除
            self.bot.reset_ch_db(auction_data[0], "a")

        elif deal_end_time <= datetime.datetime.now():
            await self.bot.get_channel(id=int(auction_data[0])).send(
                f"{self.bot.get_user(id=int(auction_data[1])).mention}さん、取引は成立しませんでした…")
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
            description=f"{ctx.author.display_name}によりこのフローは停止させられました。",
            color=0xf04747
        )
        await ctx.channel.send(embed=embed)
        try:
            await asyncio.wait_for(ctx.channel.edit(name=f"{ctx.channel.name}☆"), timeout=3.0)
        except asyncio.TimeoutError:
            pass
        await ctx.channel.send('--------ｷﾘﾄﾘ線--------')

    @commands.command()
    async def star_delete(self, ctx):
        embed = discord.Embed(
            description=f"{ctx.author.display_name}により☆を強制的に取り外しました。",
            color=0xf04747
        )
        await ctx.channel.send(embed=embed)
        try:
            await asyncio.wait_for(ctx.channel.edit(name=ctx.channel.name.split('☆')[0]), timeout=3.0)
        except asyncio.TimeoutError:
            pass

    @commands.command()
    async def execute_sql(self, ctx, *, content):
        cur.execute(content)
        if not content.lower().startswith("select"):  # select以外だったらcommitしてreturn
            await ctx.send(f'SQL文`{content}`は正常に実行されました')
            return db.commit()

        data = cur.fetchall()

        result = ""
        for i in range(len(data)):
            result += '、'.join(str(d) for d in data[i])
            result += "\n"

        if len(result) <= 2000:
            embed = discord.Embed(title="SQL文の実行結果", description=result)
            await ctx.send(embed=embed)
        else:
            result_list = result.splitlines()
            react_list = ["\U000025c0\U0000fe0f", "\U000025b6\U0000fe0f"]

            page = 0
            max_page = round(len(result_list) / 10)
            embed = discord.Embed(title=f"SQL文の実行結果(1-10件目)",
                                  description="\n".join(value for value in result_list[0:10]))
            msg = await ctx.send(embed=embed)

            for react in react_list:
                await msg.add_reaction(react)

            def check(reaction, user):
                if reaction.message.id != msg.id:
                    return 0
                elif ctx.author.bot or user != ctx.author:
                    return 0
                elif str(reaction.emoji) in react_list:
                    return reaction, user
                else:
                    return 0

            while not self.bot.is_closed():
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=300)
                except asyncio.TimeoutError:
                    return await msg.clear_reactions()
                else:
                    emoji = str(reaction.emoji)
                    await msg.remove_reaction(emoji, user)
                    if emoji == react_list[0]:  # 戻るリアクションだったら
                        if page == 0:
                            page = max_page
                        else:
                            page -= 1

                    if emoji == react_list[1]:  # 進むリアクションだったら
                        if page == max_page:
                            page = 0
                        else:
                            page += 1
                    start_num = page * 10 + 1
                    if len(result_list) < start_num + 9:
                        embed = discord.Embed(title=f"SQL文の実行結果({start_num}-{len(result_list)}件目)",
                                              description="\n".join(
                                                  value for value in result_list[start_num - 1:len(result_list)]))
                    else:
                        embed = discord.Embed(title=f"SQL文の実行結果({start_num}-{start_num + 9}件目)",
                                              description="\n".join(
                                                  value for value in result_list[start_num - 1:start_num + 9]))
                    await msg.edit(embed=embed)

    @execute_sql.error
    async def sql_error(self, ctx, error):
        await ctx.send("SQL文が違うだろう！！？？")
        db.commit()

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
        for ch in ch_list_1:
            await ctx.send(
                f"INSERT INTO tend VALUES ({ch}, ARRAY[0], ARRAY[0]);")
        await ctx.send("deal\n------")
        for ch2 in ch_list_2:
            await ctx.send(
                f"INSERT INTO deal VALUES ({ch2}, 0, 0, 'undefined', 'undefined', 'undefined', 'undefined');")

    @commands.command()
    async def dbsetup(self, ctx, set_type):
        if set_type == "a":
            cur.execute("INSERT INTO auction (ch_id) values (%s)", (ctx.channel.id,))
            db.commit()
            await asyncio.sleep(1)
            self.bot.reset_ch_db(ctx.channel.id, set_type)
        elif set_type == "d":
            cur.execute("INSERT INTO deal (ch_id) values (%s)", (ctx.channel.id,))
            db.commit()
            await asyncio.sleep(1)
            self.bot.reset_ch_db(ctx.channel.id, set_type)
        else:
            await ctx.send(f"{ctx.prefix}dbsetup [a, d]")

    @commands.command()
    async def test(self, ctx):
        cur.execute("SELECT auction.ch_id, auction.auction_owner_id, auction.auction_item, tend.tender_id, "
                    "auction.unit, tend.tend_price FROM (auction JOIN tend ON auction.ch_id = tend.ch_id)")
        data = cur.fetchall()
        description = ""
        for i in range(len(data)):
            if data[i][1] == 0:
                description += f"{self.bot.get_channel(id=data[i][0]).name}:\n"
                description += f"   現在このチャンネルでオークションは開催していません！\n"
            else:
                description += f"{self.bot.get_channel(id=data[i][0]).name}:\n"
                description += f"   出品者 → {self.bot.get_user(id=data[i][1]).display_name}\n"
                description += f"   商品名 → {data[i][2]}\n"
                if data[i][3][-1] == 0:
                    description += "    入札者はまだいません！\n"
                else:
                    description += f"   最高額入札者 → {self.bot.get_user(id=data[i][3][-1]).display_name}\n"
                    description += f"   入札額 → {data[i][4]}{self.bot.stack_check_reverse(data[i][5][-1])}\n"
            description += "\n\n--------\n\n"
            if len(description) >= 1800:
                embed = discord.Embed(description=description, color=0x59a5e3)
                await ctx.channel.send(embed=embed)
                description = ""

        embed = discord.Embed(description=description, color=0x59a5e3)
        await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(AdminOnly(bot))

import asyncio
import os
import re
from traceback import TracebackException

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
        await self.bot.get_channel(832956663908007946).purge(limit=10)
        await asyncio.sleep(1)
        embed = self.bot.create_high_bid_ranking()
        for i in range(len(embed)):
            await self.bot.get_channel(832956663908007946).send(embed=embed[i])

    @commands.command()
    async def stop_deal(self, ctx):
        # dbのリセット
        if ">" in ctx.channel.category.name:
            cur.execute("SELECT * FROM auction where ch_id = %s", (ctx.channel.id,))
            auction = cur.fetchone()
            auction_embed = await ctx.fetch_message(auction[2])
            await auction_embed.unpin()
            self.bot.reset_ch_db(ctx.channel.id, "a")
        elif "*" in ctx.channel.category.name:
            cur.execute("SELECT * FROM deal where ch_id = %s", (ctx.channel.id,))
            deal = cur.fetchone()
            deal_embed = await ctx.fetch_message(deal[2])
            await deal_embed.unpin()
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

    @commands.command(aliases=["es"])
    async def execute_sql(self, ctx, *, content):
        cur.execute(content)
        if not content.lower().startswith("select"):  # select以外だったらcommitしてreturn
            await ctx.send(f'SQL文`{content}`は正常に実行されました')
            return db.commit()

        data = cur.fetchall()

        result = []
        for row in data:
            result.append(", ".join(map(repr, row)))

        if len("\n".join(result)) <= 2000:
            embed = discord.Embed(title="SQL文の実行結果", description="\n".join(result))
            await ctx.send(embed=embed)
        else:
            react_list = ["\U000025c0\U0000fe0f", "\U000025b6\U0000fe0f"]

            page = 0
            max_page = (len(result)-1)//10+1 # 切り上げ除算
            embed = discord.Embed(title=f"SQL文の実行結果(1-10件目)",
                                  description="\n".join(result[:10]))
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
                        page -= 1
                    elif emoji == react_list[1]:  # 進むリアクションだったら
                        page += 1
                    page %= max_page # (0 <= page < max_page) を満たすように

                    start_index = page * 10
                    if len(result) < start_index + 10:
                        embed = discord.Embed(title=f"SQL文の実行結果({start_index+1}-{len(result)}件目)",
                                              description="\n".join(result[start_index:]))
                    else:
                        embed = discord.Embed(title=f"SQL文の実行結果({start_index+1}-{start_index+10}件目)",
                                              description="\n".join(result[start_index:start_index+10]))
                    await msg.edit(embed=embed)

    @execute_sql.error
    async def sql_error(self, ctx, error):
        tb_format = "".join(TracebackException.from_exception(error).format_exception_only())
        await ctx.send(f"```\n{tb_format}```")
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
    async def dbsetup(self, ctx, set_type):
        if set_type == "a":
            cur.execute("INSERT INTO auction (ch_id) values (%s)", (ctx.channel.id,))
            cur.execute("INSERT INTO tend (ch_id) values (%s)", (ctx.channel.id,))
            db.commit()
            self.bot.reset_ch_db(ctx.channel.id, set_type)
        elif set_type == "d":
            cur.execute("INSERT INTO deal (ch_id) values (%s)", (ctx.channel.id,))
            db.commit()
            self.bot.reset_ch_db(ctx.channel.id, set_type)
        else:
            await ctx.send(f"{ctx.prefix}dbsetup [a, d]")

    @commands.command()
    async def restart(self, ctx):
        await ctx.send("restarting ")
        await self.bot.close()

    @commands.command()
    async def kick(self, ctx, role: discord.Role):
        n = len(role.members)
        for mem in role.members:
            await mem.kick()

        await ctx.channel.send(f"{role.mention}持ちの{n}人を吹き飛ばしました")


def setup(bot):
    bot.add_cog(AdminOnly(bot))

import asyncio
from discord.ext import commands, tasks
import discord
import psycopg2
import os
import datetime

SQLpath = os.environ["DATABASE_URL"]
db = psycopg2.connect(SQLpath)  # sqlに接続
cur = db.cursor()  # なんか操作する時に使うやつ


class CheckEndTime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_time.start()

    @tasks.loop(minutes=1)
    async def check_time(self):
        now = datetime.datetime.now().strftime("%Y/%m/%d")
        kgx = self.bot.get_guild(558125111081697300)
        log_ch = self.bot.get_channel(558132754953273355)

        cur.execute("SELECT * from auction;")
        auction_data = cur.fetchall()
        for row in auction_data:
            if not row[5] <= now:
                continue

            time = now.strftime("%Y/%m/%d")
            ch = self.bot.get_channel(row[0])
            owner = kgx.get_member(row[1])
            item = row[2]

            cur.execute("SELECT * from tend WHERE ch_id=%s;", (ch.id,))
            tend_data = cur.fetchone()
            tender = kgx.get_member(tend_data[1])
            price = self.bot.stack_check_reverse(tend_data[2])
            tend_price = f"{row[7]}{price}"

            embed = discord.Embed(title="オークション取引結果", color=0x36a64f)
            embed.add_field(name="落札日", value=f'\n\n{now}', inline=False)
            embed.add_field(name="出品者", value=f'\n\n{owner.display_name}', inline=False)
            embed.add_field(name="品物", value=f'\n\n{item}', inline=False)
            embed.add_field(name="落札者", value=f'\n\n{tender.display_name}', inline=False)
            embed.add_field(name="落札価格", value=f'\n\n{tend_price}', inline=False)
            embed.add_field(name="チャンネル名", value=f'\n\n{ch}', inline=False)

            # ランキング送信
            if "椎名" in ch.name
                # INSERTを実行。%sで後ろのタプルがそのまま代入される
                cur.execute("INSERT INTO bid_ranking VALUES (%s, %s, %s, %s)",
                            (tender.display_name, item, price, owner.display_name))
                db.commit()
                await self.bot.get_channel(705040893593387039).purge(limit=10)
                await asyncio.sleep(0.1)
                embed = self.bot.create_high_3_ranking()
                for i in range(len(embed)):
                    await self.bot.get_channel(705040893593387039).send(embed=embed[i])

            embed = discord.Embed(description="オークションを終了しました", color=0xffaf60)
            await ch.send(embed=embed)
            # chのdbを消し去る。これをもってその人のオークション開催回数を減らしたことになる
            self.bot.reset_ch_db(ch, "a")
            await ch.send('--------ｷﾘﾄﾘ線--------')
            await asyncio.sleep(0.3)
            await ch.edit(name=f"{ch.name}☆")

        cur.execute("SELECT * from deal;")
        deal_data = cur.fetchall()
        for row in deal_data:
            if row[5] <= now:
                pass


def setup(bot):
    bot.add_cog(CheckEndTime(bot))

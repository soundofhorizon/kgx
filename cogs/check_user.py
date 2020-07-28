import asyncio
import traceback
from discord.ext import commands, tasks
import discord
import psycopg2
import os
import datetime

SQLpath = os.environ["DATABASE_URL"]
db = psycopg2.connect(SQLpath)  # sqlに接続
cur = db.cursor()  # なんか操作する時に使うやつ

"""開催されているオークション、取引の主がいなくなった時close."""


class CheckUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_time.start()

    @tasks.loop(minutes=1)
    async def check_time(self):
        try:
            await self.bot.wait_until_ready()
            kgx = self.bot.get_guild(558125111081697300)
            # オークションについて
            cur.execute("SELECT * from auction;")
            auction_data = cur.fetchall()
            for row in auction_data:
                if row[1] == 0:
                    continue
                if not kgx.get_member(row[1]):
                    ch = self.bot.get_channel(id=row[0])
                    d = datetime.datetime.now()  # 現在時刻の取得
                    time = d.strftime("%Y/%m/%d %H:%M:%S")

                    description = f"ユーザーID: {row[1]} はこのサーバーから退出したためこのオークションは終了します。"
                    embed = discord.Embed(description=description, color=0xdc143c)
                    embed.set_footer(text=f'channel:{ch.name}\ntime:{time}')
                    self.bot.reset_ch_db(row[0], "a")
                    await ch.send(embed=embed)
                    await ch.send('--------ｷﾘﾄﾘ線--------')
                    await asyncio.sleep(0.3)
                    await ch.edit(name=f"{ch.name}☆")

            # 取引について
            cur.execute("SELECT * from deal;")
            deal_data = cur.fetchall()
            for row in deal_data:
                if row[1] == 0:
                    continue
                if not kgx.get_member(row[1]):
                    ch = self.bot.get_channel(id=row[0])
                    d = datetime.datetime.now()  # 現在時刻の取得
                    time = d.strftime("%Y/%m/%d %H:%M:%S")

                    description = f"ユーザーID: {row[1]} はこのサーバーから退出したためこの取引は終了します。"
                    embed = discord.Embed(description=description, color=0xdc143c)
                    embed.set_footer(text=f'channel:{ch.name}\ntime:{time}')
                    self.bot.reset_ch_db(row[0], "d")
                    await ch.send(embed=embed)
                    await ch.send('--------ｷﾘﾄﾘ線--------')
                    await asyncio.sleep(0.3)
                    await ch.edit(name=f"{ch.name}☆")

        except Exception as e:
            orig_error = getattr(e, "original", e)
            error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
            error_message = f'```{error_msg}```'
            ch = self.bot.get_channel(628807266753183754)
            d = datetime.datetime.now()  # 現在時刻の取得
            time = d.strftime("%Y/%m/%d %H:%M:%S")
            embed = discord.Embed(title='Error_log', description=error_message, color=0xf04747)
            embed.set_footer(text=f'channel:on_check_time_loop\ntime:{time}\nuser:None')
            await ch.send(embed=embed)


def setup(bot):
    bot.add_cog(CheckUser(bot))


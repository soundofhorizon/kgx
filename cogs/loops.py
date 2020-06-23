import datetime
import os

import psycopg2
from discord.ext import commands, tasks
import discord

SQLpath = os.environ["DATABASE_URL"]
db = psycopg2.connect(SQLpath)  # sqlに接続
cur = db.cursor()  # なんか操作する時に使うやつ


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.presence_change_task.start()

    @tasks.loop(seconds=20)
    async def presence_change_task(self):
        await self.bot.wait_until_ready()
        game = discord.Game(f"{self.bot.get_guild(558125111081697300).member_count}人を監視中")
        await self.bot.change_presence(status=discord.Status.online, activity=game)

    @tasks.loop(seconds=60)
    async def bid_task(self):
        # 終わるの早いやつ1つ取ってくる
        cur.execute("SELECT * from auction ORDER BY auction_end_time ASC")
        auction_data = cur.fetchone()
        if auction_data[6] >= datetime.datetime.now():
            await self.bot.get_channel(id=int(auction_data[0])).send("終わりです。")


def setup(bot):
    bot.add_cog(Loops(bot))

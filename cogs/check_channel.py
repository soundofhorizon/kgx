import asyncio
import traceback
from discord.ext import commands, tasks
import discord
import psycopg2
import os
import datetime

import requests #debug

SQLpath = os.environ["DATABASE_URL"]
db = psycopg2.connect(SQLpath)  # sqlに接続
cur = db.cursor()  # なんか操作する時に使うやつ

wh_url = "https://discordapp.com/api/webhooks/710752349601136641/dGfGWAPQycM81CN3UsnJsPBePGc_1epwy_RV_PqlSbGbqOerKaAtKsDYGzFbCkTSG8_N"

"""APIのレート制限により星が付かないチャンネル or 星が消えてないチャンネルを検知して変更."""


class CheckChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_channel.start()

    @tasks.loop(minutes=1)
    async def check_channel(self):
        try:
            await self.bot.wait_until_ready()
            # オークションについて
            cur.execute("SELECT * from auction")
            auction_data = cur.fetchall()
            for row in auction_data:
                content = {
                    "username": "debug",
                    "content": f"{type(auction_data)}"
                }
                requests.post(wh_url, content)
                """
                if self.bot.get_channel(id=row[0]):
                    await self.bot.get_channel(id=735708199377961072).send("True")
                ch = self.bot.get_channel(id=row[0])
                if row[1] == 0 and "☆" not in ch.name:
                    try:
                        await asyncio.wait_for(ch.edit(name=f"{ch.name}☆"), timeout=3.0)
                    except asyncio.TimeoutError:
                        continue
                elif row[1] != 0 and "☆" in ch.name:
                    try:
                        await asyncio.wait_for(ch.edit(name=ch.name.split('☆')[0]), timeout=3.0)
                    except asyncio.TimeoutError:
                        continue"""

            # 取引について
            cur.execute("SELECT * from deal;")
            deal_data = cur.fetchall()
            for row in deal_data:
                ch = self.bot.get_channel(id=row[0])
                if row[1] == 0 and "☆" not in ch.name:
                    try:
                        await asyncio.wait_for(ch.edit(name=f"{ch.name}☆"), timeout=3.0)
                    except asyncio.TimeoutError:
                        continue
                elif row[1] != 0 and "☆" in ch.name:
                    try:
                        await asyncio.wait_for(ch.edit(name=ch.name.split('☆')[0]), timeout=3.0)
                    except asyncio.TimeoutError:
                        continue

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
    bot.add_cog(CheckChannel(bot))

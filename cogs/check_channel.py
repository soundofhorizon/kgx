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
            cur.execute("SELECT ch_id, auction_owner_id from auction")
            auction_data = cur.fetchall()
            for ch_id, auction_owner_id in auction_data:
                ch = self.bot.get_channel(id=ch_id)
                if ch is None:
                    return
                if auction_owner_id == 0 and "☆" not in ch.name:
                    try:
                        await asyncio.wait_for(ch.edit(name=f"{ch.name}☆"), timeout=3.0)
                    except asyncio.TimeoutError:
                        continue
                elif auction_owner_id != 0 and "☆" in ch.name:
                    try:
                        await asyncio.wait_for(ch.edit(name=ch.name.split('☆')[0]), timeout=3.0)
                    except asyncio.TimeoutError:
                        continue

            # 取引について
            cur.execute("SELECT ch_id, deal_owner_id from deal;")
            deal_data = cur.fetchall()
            for ch_id, deal_owner_id in deal_data:
                ch = self.bot.get_channel(id=ch_id)
                if deal_owner_id == 0 and "☆" not in ch.name:
                    try:
                        await asyncio.wait_for(ch.edit(name=f"{ch.name}☆"), timeout=3.0)
                    except asyncio.TimeoutError:
                        continue
                elif deal_owner_id != 0 and "☆" in ch.name:
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

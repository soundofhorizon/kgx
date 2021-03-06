import datetime
import os
import re

import discord
import psycopg2
from discord.ext import commands, tasks

SQLpath = os.environ["DATABASE_URL"]
db = psycopg2.connect(SQLpath)  # sqlに接続
cur = db.cursor()  # なんか操作する時に使うやつ


class Loops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.presence_change_task.start()
        self.show_all_channel_info.start()

    @tasks.loop(seconds=20)
    async def presence_change_task(self):
        await self.bot.wait_until_ready()
        game = discord.Game(f"{self.bot.get_guild(558125111081697300).member_count}人を監視中")
        await self.bot.change_presence(status=discord.Status.online, activity=game)

    @tasks.loop(seconds=60)
    async def show_all_channel_info(self):
        await self.bot.wait_until_ready()
        auction_data_channel = self.bot.get_channel(id=771034285352026162)
        await auction_data_channel.purge(limit=100)
        cur.execute("SELECT DISTINCT auction.ch_id, auction.auction_owner_id, auction.auction_item,"
                    "tend.tender_id, auction.unit, tend.tend_price, auction.auction_end_time FROM "
                    "(auction JOIN tend ON auction.ch_id = tend.ch_id)")
        sql_data = cur.fetchall()

        description = ""
        before_sort_data = []
        # [ch_id, ch_name, data]の2重リストを作成し、ch_nameを基準に変更を加える。いい方法があったら変更してほしい><
        for i in range(len(sql_data)):
            # 椎名debug
            if sql_data[i][0] == 747728655735586876:
                continue
            else:
                before_sort_data.append([sql_data[i][0], self.bot.get_channel(id=sql_data[i][0]).name, sql_data[i]])

        # マジでここのアルゴリズムを変えたい
        # 椎名かガチャ券かなどを分類
        siina_ch = []
        gatya_ch = []
        all_ch = []
        yami_ch = []
        for i in range(len(before_sort_data)):
            if "椎名" in before_sort_data[i][1]:
                siina_ch.append(before_sort_data[i])
            elif "ガチャ券" in before_sort_data[i][1]:
                gatya_ch.append(before_sort_data[i])
            elif "all" in before_sort_data[i][1]:
                all_ch.append(before_sort_data[i])
            elif "闇取引" in before_sort_data[i][1]:
                yami_ch.append(before_sort_data[i])
        # 椎名 - ガチャ券 - all - 闇取引の順で正規表現で殴りラムダ式で並び替え
        siina_ch_sorted = sorted(siina_ch, reverse=False, key=lambda x: int(re.search(r'\d+', x[1]).group()))
        gatya_ch_sorted = sorted(gatya_ch, reverse=False, key=lambda x: int(re.search(r'\d+', x[1]).group()))
        all_ch_sorted = sorted(all_ch, reverse=False, key=lambda x: int(re.search(r'\d+', x[1]).group()))
        yami_ch_sorted = sorted(yami_ch, reverse=False, key=lambda x: int(re.search(r'\d+', x[1]).group()))
        data = []
        for i in siina_ch_sorted:
            data.append(i)
        for i in gatya_ch_sorted:
            data.append(i)
        for i in all_ch_sorted:
            data.append(i)
        for i in yami_ch_sorted:
            data.append(i)

        for i in range(len(data)):
            # debug出てもらっても困るので消滅させる。
            if data[i][2][1] == 0:
                continue
            # 他記述。
            else:
                # 終了時刻までの残り時間を計算
                now = datetime.datetime.now()
                check = datetime.datetime.strptime(data[i][2][6], "%Y/%m/%d-%H:%M")
                diff = check - now
                diff_hours = int(diff.seconds/3600)
                diff_minites = int((diff.seconds - diff_hours*3600)/60)
                diff_seconds = diff.seconds - diff_hours*3600 - diff_minites*60

                description += f"{self.bot.get_channel(id=data[i][2][0]).mention}:\n"
                description += f"   出品者 → {self.bot.get_user(id=data[i][2][1]).display_name}\n"
                description += f"   商品名 → {data[i][2][2]}\n"
                # 多分no bidで更新すると死ぬ気がするので分岐
                if data[i][2][3][-1] == 0:
                    description += "    入札者はまだいません！\n"
                else:
                    description += f"   最高額入札者 → {self.bot.get_user(id=data[i][2][3][-1]).display_name}\n"
                    description += f"   入札額 → {data[i][2][4]}{self.bot.stack_check_reverse(data[i][2][5][-1])}\n"
                if diff_hours == 0:
                    description += f"   終了まで残り → **{diff.days}日{diff_hours}時間{diff_minites}分{diff_seconds}秒**\n"
                else:
                    description += f"   終了まで残り → {diff.days}日{diff_hours}時間{diff_minites}分{diff_seconds}秒\n"
            description += "\n--------\n\n"

            # 文字数制限回避。多分足りない
            if len(description) >= 1800:
                embed = discord.Embed(description=description, color=0x59a5e3)
                await auction_data_channel.send(embed=embed)
                description = ""
        embed = discord.Embed(description=description, color=0x59a5e3)
        await auction_data_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Loops(bot))

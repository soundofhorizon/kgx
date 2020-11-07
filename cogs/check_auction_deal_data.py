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


class CheckAuctionDealData(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.auction_data.start()
        self.deal_data.start()
        await self.bot.wait_until_ready()

    # auctionのやつ
    @tasks.loop(minutes=1)
    async def auction_data(self, ctx):
        try:
            auction_data_channel = self.bot.get_channel(id=771034285352026162)
            await auction_data_channel.purge(limit=100)
            cur.execute("SELECT DISTINCT auction.ch_id, auction.auction_owner_id, auction.auction_item,"
                        "tend.tender_id, auction.unit, tend.tend_price, auction.auction_end_time FROM "
                        "(auction JOIN tend ON auction.ch_id = tend.ch_id)")
            sql_data = cur.fetchall()
            description = ""
            before_sort_data = []
            # [ch_id, ch_name, data]の2重リストを作成する。いい方法があったら変更してほしい><
            for i in range(len(before_sort_data)):
                before_sort_data.append([sql_data[i][0], self.bot.get_channel(id=sql_data[i][0]).name, sql_data])
            data = sorted(before_sort_data, reverse=False, key=lambda x: x[1])
            for i in range(len(data)):
                # debug出てもらっても困るので消滅させる。
                if data[i][0] == 747728655735586876:
                    continue
                # オークションが開催されてないときdisplay_nameが取れない。(人いないし)よって分岐
                elif data[i][1] == 0:
                    description += f"{self.bot.get_channel(id=data[i][0]).name}:\n"
                    description += f"   現在このチャンネルでオークションは開催していません！\n"
                # 他記述。
                else:
                    description += f"{self.bot.get_channel(id=data[i][0]).name}:\n"
                    description += f"   出品者 → {self.bot.get_user(id=data[i][1]).display_name}\n"
                    description += f"   商品名 → {data[i][2]}\n"
                    # 多分no bidで更新すると死ぬ気がするので分岐
                    if data[i][3][-1] == 0:
                        description += "    入札者はまだいません！\n"
                    else:
                        description += f"   最高額入札者 → {self.bot.get_user(id=data[i][3][-1]).display_name}\n"
                        description += f"   入札額 → {data[i][4]}{self.bot.stack_check_reverse(data[i][5][-1])}\n"
                    description += f"   終了時刻 → {data[i][6]}\n"
                description += "\n--------\n\n"

                # 文字数制限回避。多分足りない
                if len(description) >= 1800:
                    embed = discord.Embed(description=description, color=0x59a5e3)
                    await auction_data_channel.send(embed=embed)
                    description = ""

            embed = discord.Embed(description=description, color=0x59a5e3)
            await auction_data_channel.send(embed=embed)

        except Exception as e:
            db.commit()
            orig_error = getattr(e, "original", e)
            error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
            error_message = f'```{error_msg}```'
            ch = self.bot.get_channel(628807266753183754)
            d = datetime.datetime.now()  # 現在時刻の取得
            time = d.strftime("%Y/%m/%d %H:%M:%S")
            embed = discord.Embed(title='Error_log', description=error_message, color=0xf04747)
            embed.set_footer(text=f'channel:on_check_auction_deal_data\ntime:{time}\nuser:None')
            await ch.send(embed=embed)

    # dealのやつ
    @tasks.loop(minutes=1)
    async def deal_data(self, ctx):
        try:
            deal_data_channel = self.bot.get_channel(id=771068489627861002)
            await deal_data_channel.purge(limit=100)
            cur.execute("SELECT * from deal")
            data = cur.fetchall()
            description = ""
            for i in range(len(data)):
                # 取引が開催されてないときdisplay_nameが取れない。(人いないし)よって分岐
                if data[i][1] == 0:
                    description += f"{self.bot.get_channel(id=data[i][0]).name}:\n"
                    description += f"   現在このチャンネルで取引は開催していません！\n"
                # 他記述。
                else:
                    description += f"{self.bot.get_channel(id=data[i][0]).name}:\n"
                    description += f"   出品者 → {self.bot.get_user(id=data[i][1]).display_name}\n"
                    description += f"   商品名 → {data[i][3]}\n"
                    description += f"   出品価格 → {data[i][6]}{self.bot.stack_check_reverse(data[i][4])}\n"
                    description += f"   出品価格 → {data[i][5]}\n"
                description += "\n--------\n\n"

                # 文字数制限回避。多分足りない
                if len(description) >= 1800:
                    embed = discord.Embed(description=description, color=0x59a5e3)
                    await deal_data_channel.send(embed=embed)
                    description = ""

            embed = discord.Embed(description=description, color=0x59a5e3)
            await deal_data_channel.send(embed=embed)

        except Exception as e:
            orig_error = getattr(e, "original", e)
            error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
            error_message = f'```{error_msg}```'
            ch = self.bot.get_channel(628807266753183754)
            d = datetime.datetime.now()  # 現在時刻の取得
            time = d.strftime("%Y/%m/%d %H:%M:%S")
            embed = discord.Embed(title='Error_log', description=error_message, color=0xf04747)
            embed.set_footer(text=f'channel:on_check_auction_deal_data\ntime:{time}\nuser:None')
            await ch.send(embed=embed)


def setup(bot):
    bot.add_cog(CheckAuctionDealData(bot))


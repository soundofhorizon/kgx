import datetime
import os
import re
import traceback

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
        self.show_all_auction_channel_info.start()
        self.show_all_deal_channel_info.start()

    @tasks.loop(seconds=20)
    async def presence_change_task(self):
        await self.bot.wait_until_ready()
        game = discord.Game(f"{self.bot.get_guild(558125111081697300).member_count}人を監視中")
        await self.bot.change_presence(status=discord.Status.online, activity=game)

    @tasks.loop(seconds=60)
    async def show_all_auction_channel_info(self):
        try:
            await self.bot.wait_until_ready()
            auction_data_channel = self.bot.get_channel(id=771034285352026162)
            await auction_data_channel.purge(limit=100)
            cur.execute("SELECT DISTINCT auction.ch_id, auction.auction_owner_id, auction.auction_item,"
                        "tend.tender_id, auction.unit, tend.tend_price, auction.auction_end_time FROM "
                        "(auction JOIN tend ON auction.ch_id = tend.ch_id)")
            sql_data = cur.fetchall()

            def active_filter(record):
                """
                開催していないオークションならFalse。ついでにdebugも消す
                """
                ch_id, owner_id = record[:2]
                if ch_id == 747728655735586876:
                    return False # 椎名debug
                elif owner_id == 0:
                    return False # 開催していない
                else:
                    return True

            AUCTION_TYPES = ["椎名", "ガチャ券", "all", "闇取引"] # オークションの種類一覧
            def order_func(record):
                """
                チャンネル名に対応したタプルを返す
                椎名1 → (0, 1)、椎名2 → (0, 2), ガチャ券1 → (1, 1)など
                """
                ch_id = record[0]
                channel_name = self.bot.get_channel(id=ch_id).name

                for type_order, type_name in enumerate(AUCTION_TYPES):
                    if type_name in channel_name: 
                        # 該当すればtype_orderを確定させる
                        break
                else:
                    type_order = len(AUCTION_TYPES) # いずれにも該当しなければ他よりも大きい値にする
                
                ch_num = int(re.search(r"\d+", channel_name).group())
                return (type_order, ch_num) # type_order,ch_numの順に比較される
            
            auctions = list(filter(active_filter, sql_data))
            auctions.sort(key=order_func)

            if not auctions:
                embed = discord.Embed(description="オークションはまだ一つも行われていません！", color=0x59a5e3)
                await auction_data_channel.send(embed=embed)
                return

            auction_info_list = []
            for ch_id, owner_id, auction_item, tender_id, unit, tend_price, end_time in auctions:
                auction_info = []
                channel = self.bot.get_channel(ch_id)
                owner = self.bot.get_user(owner_id)

                # 終了時刻までの残り時間を計算
                now = datetime.datetime.now()
                check = datetime.datetime.strptime(end_time, "%Y/%m/%d-%H:%M")
                diff = check - now
                diff_hours = diff.seconds // 3600
                diff_minites = diff.seconds % 3600 // 60
                diff_seconds = diff.seconds % 60

                auction_info.append(f"{channel.mention}:")
                auction_info.append(f"出品者 → {owner.display_name}")
                auction_info.append(f"商品名 → {auction_item}")
                # 多分no bidで更新すると死ぬ気がするので分岐
                if tender_id[-1] == 0:
                    auction_info.append("入札者はまだいません！")
                else:
                    highest_tender = self.bot.get_user(id=tender_id[-1])
                    auction_info.append(f"最高額入札者 → {highest_tender.display_name}")
                    auction_info.append(f"入札額 → {unit}{self.bot.stack_check_reverse(tend_price[-1])}")
                if diff.days == 0: # 残り1日を切っていたら太字にする
                    auction_info.append(f"終了まで残り → **{diff_hours}時間{diff_minites}分{diff_seconds}秒**")
                else:
                    auction_info.append(f"終了まで残り → {diff.days}日{diff_hours}時間{diff_minites}分{diff_seconds}秒")
                
                auction_info_list.append("\n".join(auction_info))

            for description in self.bot.join_within_limit(auction_info_list, sep="\n\n--------\n\n"):
                embed = discord.Embed(description=description, color=0x59a5e3)
                await auction_data_channel.send(embed=embed)

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


    @tasks.loop(seconds=60)
    async def show_all_deal_channel_info(self):
        try:
            await self.bot.wait_until_ready()
            deal_data_channel = self.bot.get_channel(id=771068489627861002)
            await deal_data_channel.purge(limit=100)
            cur.execute("SELECT ch_id, deal_owner_id, deal_item, deal_hope_price, deal_end_time, unit from deal")
            sql_data = cur.fetchall()

            def active_filter(record):
                """
                開催していない取引ならFalse。ついでにdebugも消す
                """
                ch_id, owner_id = record[:2]
                if ch_id == 858158727576027146:
                    return False # 取引debug
                elif owner_id == 0:
                    return False # 開催していない
                else:
                    return True

            DEAL_TYPES = ["椎名", "ガチャ券", "all"] # 取引の種類一覧
            def order_func(record):
                """
                チャンネル名に対応したタプルを返す
                椎名1 → (0, 1)、椎名2 → (0, 2), ガチャ券1 → (1, 1)など
                """
                ch_id = record[0]
                channel_name = self.bot.get_channel(id=ch_id).name

                for type_order, type_name in enumerate(DEAL_TYPES):
                    if type_name in channel_name: 
                        # 該当すればtype_orderを確定させる
                        break
                else:
                    type_order = len(DEAL_TYPES) # いずれにも該当しなければ他よりも大きい値にする
                
                ch_num = int(re.search(r"\d+", channel_name).group())
                return (type_order, ch_num) # type_order,ch_numの順に比較される
            
            deals = list(filter(active_filter, sql_data))
            deals.sort(key=order_func)

            if not deals:
                embed = discord.Embed(description="取引はまだ一つも行われていません！", color=0x59a5e3)
                await deal_data_channel.send(embed=embed)
                return

            deal_info_list = []
            for ch_id, owner_id, deal_item, hope_price, end_time, unit in deals:
                deal_info = []
                channel = self.bot.get_channel(ch_id)
                owner = self.bot.get_user(owner_id)

                # 終了時刻までの残り時間を計算
                now = datetime.datetime.now()
                check = datetime.datetime.strptime(end_time, "%Y/%m/%d-%H:%M")
                diff = check - now
                diff_hours = diff.seconds // 3600
                diff_minites = diff.seconds % 3600 // 60
                diff_seconds = diff.seconds % 60

                deal_info.append(f"{channel.mention}:")
                deal_info.append(f"出品者 → {owner.display_name}")
                deal_info.append(f"商品名 → {deal_item}")
                deal_info.append(f"希望価格 → {unit}{self.bot.stack_check_reverse(int(hope_price))}")
                if diff.days == 0: # 残り1日を切っていたら太字にする
                    deal_info.append(f"終了まで残り → **{diff_hours}時間{diff_minites}分{diff_seconds}秒**")
                else:
                    deal_info.append(f"終了まで残り → {diff.days}日{diff_hours}時間{diff_minites}分{diff_seconds}秒")
                
                deal_info_list.append("\n".join(deal_info))


            for description in self.bot.join_within_limit(deal_info_list, sep="\n\n--------\n\n"):
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
            embed.set_footer(text=f'channel:on_check_time_loop\ntime:{time}\nuser:None')
            await ch.send(embed=embed)


def setup(bot):
    bot.add_cog(Loops(bot))

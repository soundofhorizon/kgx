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


class CheckEndTime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_time.start()

    @tasks.loop(minutes=1)
    async def check_time(self):
        try:
            await self.bot.wait_until_ready()
            now = datetime.datetime.now()
            kgx = self.bot.get_guild(558125111081697300)
            log_ch = self.bot.get_channel(558132754953273355)

            # オークションについて
            cur.execute("SELECT ch_id, auction_owner_id, embed_message_id, auction_item, auction_end_time, unit from auction;")
            auction_data = cur.fetchall()
            for ch_id, auction_owner_id, embed_message_id, item, auction_end_time, unit in auction_data:
                if auction_end_time == "undefined":
                    continue
                if datetime.datetime.strptime(auction_end_time, "%Y/%m/%d-%H:%M") <= now:
                    ch = self.bot.get_channel(ch_id)
                    owner = kgx.get_member(auction_owner_id)

                    cur.execute("SELECT tender_id, tend_price from tend WHERE ch_id=%s;", (ch.id,))
                    tenders_id, tend_prices = cur.fetchone()
                    tender = kgx.get_member(tenders_id[-1])
                    price = self.bot.stack_check_reverse(tend_prices[-1])
                    if int(self.bot.stack_check(price)) == 0:
                        # 入札者なしという事
                        embed = discord.Embed(description=f"{ch.name}のオークションは入札者が誰もいなかったので終了します")
                        time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                        embed.set_footer(text=f'channel:{ch.name}\nTime:{time}')
                        await self.bot.dm_send(auction_owner_id, embed)
                        embed = discord.Embed(description="オークションを終了しました", color=0xffaf60)
                        await ch.send(embed=embed)
                        # chのdbを消し去る。これをもってその人のオークション開催回数を減らしたことになる
                        self.bot.reset_ch_db(ch.id, "a")
                        await ch.send('--------ｷﾘﾄﾘ線--------')
                        await asyncio.sleep(0.3)
                        try:
                            await asyncio.wait_for(ch.edit(name=f"{ch.name}☆"), timeout=3.0)
                        except asyncio.TimeoutError:
                            continue
                        continue

                    tend_price = f"{unit}{price}"

                    embed = discord.Embed(title="オークション取引結果", color=0x36a64f)
                    embed.add_field(name="落札日", value=f'\n\n{now.strftime("%Y/%m/%d")}', inline=False)
                    embed.add_field(name="出品者", value=f'\n\n{owner.display_name}', inline=False)
                    embed.add_field(name="品物", value=f'\n\n{item}', inline=False)
                    embed.add_field(name="落札者", value=f'\n\n{tender.display_name}', inline=False)
                    embed.add_field(name="落札価格", value=f'\n\n{tend_price}', inline=False)
                    embed.add_field(name="チャンネル名", value=f'\n\n{ch.name}', inline=False)
                    await log_ch.send(embed=embed)

                    # オークションが終わったらその結果を主催者と落札者に通知
                    description = f"{ch.name}にて行われていた{owner.display_name}による 品物名: **{item}** のオークションは\n{tender.display_name}により" \
                                  f"**{tend_price}**にて落札されました"
                    embed = discord.Embed(description=description, color=0xffaf60)
                    time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                    embed.set_footer(text=f'channel:{ch.name}\nTime:{time}')
                    await self.bot.dm_send(auction_owner_id, embed)
                    await self.bot.dm_send(tenders_id[-1], embed)

                    # ランキング送信
                    if "椎名" in ch.name:
                        # INSERTを実行。%sで後ろのタプルがそのまま代入される
                        cur.execute("INSERT INTO bid_ranking VALUES (%s, %s, %s, %s)",
                                    (tender.display_name, item, tend_prices[-1], owner.display_name))
                        db.commit()
                        await self.bot.get_channel(832956663908007946).purge(limit=10)
                        await asyncio.sleep(1)
                        embed = self.bot.create_high_bid_ranking()
                        for i in range(len(embed)):
                            await self.bot.get_channel(832956663908007946).send(embed=embed[i])

                    embed = discord.Embed(description=f"{owner.display_name}が出品した{item}を{tender.display_name}が{tend_price}で落札しました！", color=0xffaf60)
                    await ch.send(embed=embed)

                    ch = self.bot.get_channel(id=ch_id)
                    auction_embed = await ch.fetch_message(embed_message_id)
                    await auction_embed.unpin()

                    # chのdbを消し去る。これをもってその人のオークション開催回数を減らしたことになる
                    self.bot.reset_ch_db(ch.id, "a")
                    await ch.send('--------ｷﾘﾄﾘ線--------')
                    await asyncio.sleep(0.3)
                    try:
                        await asyncio.wait_for(ch.edit(name=f"{ch.name}☆"), timeout=3.0)
                    except asyncio.TimeoutError:
                        continue
                await asyncio.sleep(1)

            # 取引について
            cur.execute("SELECT ch_id, deal_owner_id, embed_message_id, deal_end_time from deal;")
            deal_data = cur.fetchall()
            for ch_id, deal_owner_id, embed_message_id, deal_end_time in deal_data:
                if deal_end_time == "undefined":
                    continue
                if datetime.datetime.strptime(deal_end_time, "%Y/%m/%d-%H:%M") <= now:
                    ch = self.bot.get_channel(id=ch_id)
                    embed = discord.Embed(description=f"{ch.name}の取引は不成立でしたので終了します")
                    time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                    embed.set_footer(text=f'channel:{ch.name}\nTime:{time}')
                    await self.bot.dm_send(deal_owner_id, embed)
                    embed = discord.Embed(description="取引が終了しました", color=0xffaf60)
                    await ch.send(embed=embed)

                    ch = self.bot.get_channel(id=ch_id)
                    deal_embed = await ch.fetch_message(embed_message_id)
                    await deal_embed.unpin()

                    # chのdbを消し去る。これをもってその人のオークション開催回数を減らしたことになる
                    self.bot.reset_ch_db(ch_id, "d")
                    await ch.send('--------ｷﾘﾄﾘ線--------')
                    await asyncio.sleep(0.3)
                    try:
                        await asyncio.wait_for(ch.edit(name=f"{ch.name}☆"), timeout=3.0)
                    except asyncio.TimeoutError:
                        continue

        except Exception as e:
            if isinstance(e, psycopg2.InterfaceError):
                await self.bot.close()

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
    bot.add_cog(CheckEndTime(bot))

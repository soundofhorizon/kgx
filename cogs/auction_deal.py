import asyncio
import io
import os
import re
from datetime import datetime, timedelta

import discord
import psycopg2
import requests
from PIL import Image
from discord.ext import commands

SQLpath = os.environ["DATABASE_URL"]
db = psycopg2.connect(SQLpath)  # sqlに接続
cur = db.cursor()  # なんか操作する時に使うやつ

auction_notice_ch_id = 727333695450775613


class AuctionDael(commands.Cog):
    """オークション、取引に関するcog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bidscore(self, ctx, pt: int):  # カウントしてその数字に対応する役職を付与する
        if ctx.channel.id != 558265536430211083:
            return

        channel = self.bot.get_channel(602197766218973185)
        p = re.compile(r'^[0-9]+$')
        if p.fullmatch(str(pt)):
            cur.execute("SELECT bid_score FROM user_data where user_id = %s", (ctx.author.id,))
            oldscore = list(cur.fetchone())
            new_score = oldscore[0] + pt
            cur.execute("UPDATE user_data SET bid_score = %s WHERE user_id = %s", (new_score, ctx.author.id))
            db.commit()

            embed = discord.Embed(description=f'**{ctx.author.display_name}**の現在の落札ポイントは**{new_score}**です。',
                                  color=0x9d9d9d)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)  # ユーザー名+ID,アバターをセット
            await channel.send(embed=embed)

            if new_score in [1, 3, 5, 10, 30, 60, 100]:  # ランクアップのときのポイントだったら
                before, after = self.bot.check_role(new_score, ctx)
                if before is None:
                    await ctx.author.add_roles(after)
                    before_name = "落札初心者"
                else:
                    await asyncio.gather(
                        ctx.author.remove_roles(before),
                        ctx.author.add_roles(after)
                    )
                    before_name = before.name

                embed = discord.Embed(
                    description=f'**{ctx.author.display_name}**がランクアップ！``{before_name}⇒{after.name}``',
                    color=after.color)
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)  # ユーザー名+ID,アバターをセット
                await ctx.channel.send(embed=embed)

            embed = discord.Embed(description=f'**{ctx.author.display_name}**に落札ポイントを付与しました。', color=0x9d9d9d)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)  # ユーザー名+ID,アバターをセット
            await ctx.channel.send(embed=embed)
            await asyncio.sleep(0.5)
            # ランキングを出力する
            channel = self.bot.get_channel(677905288665235475)
            # とりあえず、ランキングチャンネルの中身を消す
            await channel.purge(limit=1)
            await channel.send(embed=self.bot.create_ranking_embed())

    @commands.command()
    async def start(self, ctx):

        def check(m):
            """ユーザーの次のメッセージを待つ"""
            if m.author.bot:
                return
            return m.channel == ctx.channel and m.author == ctx.author

        def check2(m):
            """日付型になってるかを確かめる"""
            if m.author.bot:
                return
                # フォーマットされたdatetimeとの変換を試みTrueかどうかを調べる
            try:
                return m.channel == ctx.channel and re.match(r"[0-9]{4}/[0-9]{2}/[0-9]{2}-[0-9]{2}:[0-9]{2}", m.content) and datetime.strptime(m.content, "%Y/%m/%d-%H:%M") and m.author == ctx.author
            except ValueError:
                return re.match(r"[0-9]{4}/[0-9]{2}/[0-9]{2}-24:00", m.content)

        def check3(m):
            """価格フォーマットチェック"""
            if m.author.bot:
                return
            if m.channel != ctx.channel:
                return False
            # 〇st+△(記号はint)もしくは△であるのを確かめる
            else:
                return (re.match(r"[0-9]{0,99}LC\+[0-9]{1,99}ST\+[0-9]{1,2}", m.content.upper()) or re.match(
                    r"[0-9]{1,99}ST\+[0-9]{1,2}", m.content.upper()) or re.match(r"[1-9]{1,2}", m.content)
                        ) and m.author == ctx.author

        def check4(m):
            """価格フォーマットチェック(なしを含む)"""
            if m.author.bot:
                return
            elif m.author == ctx.author:
                if m.channel != ctx.channel:
                    return False
                # 〇st+△(記号はint)もしくは△であるのを確かめる
                return (re.match(r"[0-9]{0,99}LC\+[0-9]{1,99}ST\+[0-9]{1,2}", m.content.upper()) or re.match(
                    r"[0-9]{1,99}ST\+[0-9]{1,2}", m.content.upper()) or re.match(r"[1-9]{1,2}", m.content)
                        or m.content == "なし") and m.author == ctx.author

        def over24Hdatetime(year, month, day, hour, minute):

            """24時間以上の表記を正常な表記にする"""
            minutes = int(hour)*60 + int(minute)

            dt = datetime(year=year, month=month, day=day)
            dt += timedelta(minutes=minutes)

            return dt

        # 2つ行ってる場合はreturn
        user = ctx.author.id
        if self.bot.get_user_auction_count(user) >= 2 and ctx.author.id != 251365193127297024:
            description = "貴方はすでに取引を2つ以上行っているためこれ以上取引を始められません。\n" \
                          "行っている取引が2つ未満になってから再度行ってください。"
            await ctx.channel.send(embed=discord.Embed(description=description, color=0xf04747))
            await ctx.channel.send("--------ｷﾘﾄﾘ線--------")
            return

        first_message_object = None
        # オークション系
        if self.bot.is_auction_category(ctx):

            # 既にオークションが行われていたらreturn
            if "☆" not in ctx.channel.name:
                description = "このチャンネルでは既にオークションが行われています。\n☆がついているチャンネルでオークションを始めてください。"
                await ctx.channel.send(embed=discord.Embed(description=description, color=0xf04747), delete_after=3)
                await asyncio.sleep(3)
                await ctx.message.delete()
                return

            # 単位の設定
            unit = ""
            if self.bot.is_siina_category(ctx):
                unit = "椎名"
            elif self.bot.is_gacha_category(ctx):
                unit = "ガチャ券"
            else:
                embed = discord.Embed(description="何によるオークションですか？単位を入力してください。(ex.GTギフト券, ガチャリンゴ, エメラルド etc)",
                                      color=0xffaf60)
                first_message_object = await ctx.channel.send(embed=embed)
                user_input_0 = await self.bot.wait_for("message", check=check)
                unit = user_input_0.content

            # ALLにおいて
            if "all" in ctx.channel.name.lower() and (unit == "椎名" or unit == "ガチャ券"):
                embed = discord.Embed(description="椎名、ガチャ券のオークションは専用のチャンネルで行ってください。",
                                      color=0xffaf60)
                await ctx.channel.send(embed=embed)
                return

            embed = discord.Embed(
                description="出品するものを入力してください。",
                color=0xffaf60)
            if first_message_object is not None:
                await ctx.channel.send(embed=embed)
            else:
                first_message_object = await ctx.channel.send(embed=embed)
            user_input_1 = await self.bot.wait_for('message', check=check)

            embed = discord.Embed(description="開始価格を入力してください。\n**※次のように入力してください。"
                                              "【〇LC+△ST+□】 or　【〇ST+△】 or 【△】 ex.1lc+1st+1 or 1st+1 or 32**",
                                  color=0xffaf60)
            await ctx.channel.send(embed=embed)
            user_input_2 = await self.bot.wait_for('message', check=check3)
            user_input_2 = self.bot.stack_check_reverse(self.bot.stack_check(user_input_2.content))
            # check3()の正規表現を正しいものにしてください「1hoge」で通ってしまい、
            # stack_check_reverse()で0が返ってくるため開始価格が0になります
            # そのための応急処置 20201114けい制作
            if user_input_2 == 0:
                await ctx.channel.send(f"{ctx.author.mention}さん、使用できる単位はLC, st, 個または数字のみです")
                return
            # ここまで応急処置
            kaisi_kakaku = self.bot.stack_check(user_input_2)  # kaisi_kakakuはint型

            embed = discord.Embed(description="即決価格を入力してください。\n**※次のように入力してください。"
                                              "【〇LC+△ST+□】 or　【〇ST+△】 or 【△】 ex.1lc+1st+1 or 1st+1 or 32**\n"
                                              " ない場合は「``なし``」とお書きください。",
                                  color=0xffaf60)
            await ctx.channel.send(embed=embed)
            user_input_3 = await self.bot.wait_for('message', check=check4)
            if not user_input_3.content == "なし":
                user_input_3 = self.bot.stack_check_reverse(self.bot.stack_check(user_input_3.content))
                sokketu_kakaku = self.bot.stack_check(user_input_3)  # sokketu_kakakuはint型
                if kaisi_kakaku >= sokketu_kakaku:
                    # purge()の処理は入っていません
                    await ctx.channel.send(f"{ctx.author.mention}さん、開始価格が即決価格より高い、又は即決価格と同じです。やり直してください。")
                    await ctx.channel.send("--------ｷﾘﾄﾘ線--------")
                    return
            else:
                user_input_3 = "なし"

            embed = discord.Embed(
                description="オークション終了日時を入力してください。\n**注意！**時間の書式に注意してください！\n"
                            "例 2020年5月14日の午後8時に終了したい場合：\n**2020/05/14-20:00**と入力してください。\n"
                            "この形でない場合認識されません！",
                color=0xffaf60)
            await ctx.channel.send(embed=embed)
            user_input_4 = await self.bot.wait_for('message', check=check2)

            year_month_day_list = list(map(int, user_input_4.content.split("-")[0].split("/")))
            hour_min_list = list(map(int, user_input_4.content.split("-")[1].split(":")))
            now = datetime.now()
            if hour_min_list == [24, 00]:
                finish_time = over24Hdatetime(year_month_day_list[0], year_month_day_list[1], year_month_day_list[2], hour_min_list[0], hour_min_list[1])
            else:
                finish_time = datetime.strptime(user_input_4.content, r"%Y/%m/%d-%H:%M")

            if now >= finish_time:
                # purge()の処理は入っていません
                await ctx.channel.send(f"{ctx.author.mention}さん、現在時刻より前、又は同時刻に終了時刻が設定されています。やり直してください。")
                await ctx.channel.send("--------ｷﾘﾄﾘ線--------")
                return
            two_months_later = now + timedelta(weeks=8)
            if finish_time > two_months_later:
                # purge()の処理は(ry
                await ctx.channel.send(f"{ctx.author.mention}さん、2ヵ月以上にわたるオークションは禁止されています。やり直してください。")
                await ctx.channel.send("--------ｷﾘﾄﾘ線--------")
                return

            embed = discord.Embed(
                description="その他、即決特典などありましたらお書きください。\n長い場合、改行などをして**１回の送信**で書いてください。\n"
                            "何も無ければ「なし」で構いません。",
                color=0xffaf60)
            await ctx.channel.send(embed=embed)
            user_input_5 = await self.bot.wait_for('message', check=check)

            await self.bot.delete_to(ctx, first_message_object.id)
            embed = discord.Embed(title="これで始めます。よろしいですか？YES/NOで答えてください。(小文字でもOK。NOの場合初めからやり直してください。)",
                                  color=0xffaf60)
            embed.add_field(name="出品者", value=f'\n\n{ctx.author.display_name}', inline=True)
            embed.add_field(name="出品物", value=f'\n\n{user_input_1.content}', inline=True)
            embed.add_field(name="開始価格", value=f'\n\n{unit}{user_input_2}', inline=False)
            # 卒決価格なしなら単位は付与しない
            if user_input_3 == "なし":
                value = user_input_3
            else:
                value = f"{unit}{user_input_3}"
            embed.add_field(name="即決価格", value=f'\n\n{value}', inline=False)
            embed.add_field(name="終了日時", value=f'\n\n{user_input_4.content}', inline=True)
            embed.add_field(name="特記事項", value=f'\n\n{user_input_5.content}', inline=True)
            await ctx.channel.send(embed=embed)
            user_input_6 = await self.bot.wait_for('message', check=check)

            if user_input_6.content == "YES" or user_input_6.content == "yes" or user_input_6.content == "いぇｓ" or user_input_6.content == "いぇs":
                kazu = 3
                await ctx.channel.purge(limit=kazu)
                await asyncio.sleep(0.3)
                embed = discord.Embed(title="オークション内容", color=0xffaf60)
                embed.add_field(name="出品者", value=f'\n\n{ctx.author.display_name}', inline=True)
                embed.add_field(name="出品物", value=f'\n\n{user_input_1.content}', inline=True)
                embed.add_field(name="開始価格", value=f'\n\n{unit}{user_input_2}', inline=False)
                embed.add_field(name="即決価格", value=f'\n\n{value}', inline=False)
                embed.add_field(name="終了日時", value=f'\n\n{user_input_4.content}', inline=True)
                embed.add_field(name="特記事項", value=f'\n\n{user_input_5.content}', inline=True)
                await ctx.channel.send("<:siina:558251559394213888>オークションを開始します<:siina:558251559394213888>")
                auction_embed = await ctx.channel.send(embed=embed)
                await auction_embed.pin()

                # 24:00だとSQL突っ込むと詰むのでここで変える
                if hour_min_list == [24, 00]:
                    user_input_4.content = finish_time.strftime('%Y/%m/%d-%H:%M')

                # 椎名の部分を数字に変換(開始と即決)
                user_input_2 = self.bot.stack_check(user_input_2)
                if user_input_3 == "なし":
                    pass
                else:
                    user_input_3 = self.bot.stack_check(user_input_3)

                # SQLにデータ登録
                cur.execute("UPDATE auction SET auction_owner_id = %s, embed_message_id = %s, auction_item = %s, "
                            "auction_start_price = %s, auction_bin_price = %s, auction_end_time = %s, "
                            "unit = %s, notice = %s WHERE ch_id = %s",
                            (ctx.author.id, auction_embed.id, user_input_1.content, str(user_input_2),
                             str(user_input_3), user_input_4.content, unit, user_input_5.content, ctx.channel.id))
                db.commit()

                try:
                    await asyncio.wait_for(ctx.channel.edit(name=ctx.channel.name.split('☆')[0]), timeout=3.0)
                except asyncio.TimeoutError:
                    pass

            else:
                kazu = 2
                await ctx.channel.purge(limit=kazu)
                await ctx.channel.send("初めからやり直してください。\n--------ｷﾘﾄﾘ線--------")

        # 通常取引について
        elif self.bot.is_normal_category(ctx):

            # 既に取引が行われていたらreturn
            if "☆" not in ctx.channel.name:
                description = "このチャンネルでは既に取引が行われています。\n☆がついているチャンネルで取引を始めてください。"
                await ctx.channel.send(embed=discord.Embed(description=description, color=0xf04747))
                await asyncio.sleep(3)
                await ctx.channel.purge(limit=2)
                return

            # 単位の設定
            if self.bot.is_siina_category(ctx):
                unit = "椎名"
            elif self.bot.is_gacha_category(ctx):
                unit = "ガチャ券"
            else:
                embed = discord.Embed(description="何による取引ですか？単位を入力してください。(ex.GTギフト券, ガチャリンゴ, エメラルド etc)",
                                      color=0xffaf60)
                first_message_object = await ctx.channel.send(embed=embed)
                user_input_0 = await self.bot.wait_for("message", check=check)
                unit = user_input_0.content

            # ALLにおいて
            if "all" in ctx.channel.name.lower() and (unit == "椎名" or unit == "ガチャ券"):
                await ctx.channel.purge(limit=2)
                embed = discord.Embed(description="椎名、ガチャ券の取引は専用のチャンネルで行ってください。",
                                      color=0xffaf60)
                await ctx.channel.send(embed=embed)
                await ctx.channel.send("--------ｷﾘﾄﾘ線--------")
                return

            embed = discord.Embed(
                description="出品するものを入力してください。",
                color=0xffaf60)
            if first_message_object is not None:
                await ctx.channel.send(embed=embed)
            else:
                first_message_object = await ctx.channel.send(embed=embed)
            user_input_1 = await self.bot.wait_for('message', check=check)

            embed = discord.Embed(description="希望価格を入力してください。\n**※次のように入力してください。"
                                              "【〇LC+△ST+□】 or　【〇ST+△】 or 【△】 ex.1LC+1ST+1 or 1ST+1 or 32**",
                                  color=0xffaf60)
            await ctx.channel.send(embed=embed)
            user_input_2 = await self.bot.wait_for('message', check=check3)
            user_input_2 = self.bot.stack_check_reverse(self.bot.stack_check(user_input_2.content))
            embed = discord.Embed(
                description="取引終了日時を入力してください。\n**注意！**時間の書式に注意してください！\n"
                            "例　5月14日の午後8時に終了したい場合：\n**2021/05/14-20:00**と入力してください。\nこの形でない場合認識されません！\n"
                            "**間違えて打ってしまった場合その部分は必ず削除してください。**",
                color=0xffaf60)
            await ctx.channel.send(embed=embed)
            user_input_3 = await self.bot.wait_for('message', check=check2)

            year_month_day_list = list(map(int, user_input_3.content.split("-")[0].split("/")))
            hour_min_list = list(map(int, user_input_3.content.split("-")[1].split(":")))
            now = datetime.now()
            if hour_min_list == [24, 00]:
                finish_time = over24Hdatetime(year_month_day_list[0], year_month_day_list[1], year_month_day_list[2], hour_min_list[0], hour_min_list[1])
            else:
                finish_time = datetime.strptime(user_input_3.content, r"%Y/%m/%d-%H:%M")

            if now >= finish_time:
                # purge()の処理は入っていません
                await ctx.channel.send(f"{ctx.author.mention}さん、現在時刻より前、又は同時刻に終了時刻が設定されています。やり直してください。")
                await ctx.channel.send("--------ｷﾘﾄﾘ線--------")
                return
            two_months_later = now + timedelta(weeks=8)
            if finish_time > two_months_later:
                # purge()の処理は(ry
                await ctx.channel.send(f"{ctx.author.mention}さん、2ヵ月以上にわたる取引は禁止されています。やり直してください。")
                await ctx.channel.send("--------ｷﾘﾄﾘ線--------")
                return

            embed = discord.Embed(
                description="その他、即決特典などありましたらお書きください。\n長い場合、改行などをして**１回の送信**で書いてください。\n"
                            "何も無ければ「なし」で構いません。",
                color=0xffaf60)
            await ctx.channel.send(embed=embed)
            user_input_4 = await self.bot.wait_for('message', check=check)

            await self.bot.delete_to(ctx, first_message_object.id)

            embed = discord.Embed(title="これで始めます。よろしいですか？YES/NOで答えてください。(小文字でもOK。NOの場合初めからやり直してください。)",
                                  color=0xffaf60)
            embed.add_field(name="出品者", value=f'\n\n{ctx.author.display_name}', inline=True)
            embed.add_field(name="出品物", value=f'\n\n{user_input_1.content}', inline=False)
            embed.add_field(name="希望価格", value=f'\n\n{unit}{user_input_2}', inline=True)
            embed.add_field(name="終了日時", value=f'\n\n{user_input_3.content}', inline=True)
            embed.add_field(name="特記事項", value=f'\n\n{user_input_4.content}', inline=False)
            await ctx.channel.send(embed=embed)
            user_input_6 = await self.bot.wait_for('message', check=check)
            if user_input_6.content == "YES" or user_input_6.content == "yes" or user_input_6.content == "いぇｓ" or user_input_6.content == "いぇs":
                kazu = 3
                await ctx.channel.purge(limit=kazu)
                await asyncio.sleep(0.3)
                embed = discord.Embed(title="取引内容", color=0xffaf60)
                embed.add_field(name="出品者", value=f'\n\n{ctx.author.display_name}', inline=True)
                embed.add_field(name="出品物", value=f'\n\n{user_input_1.content}', inline=False)
                embed.add_field(name="希望価格", value=f'\n\n{unit}{user_input_2}', inline=True)
                embed.add_field(name="終了日時", value=f'\n\n{user_input_3.content}', inline=True)
                embed.add_field(name="特記事項", value=f'\n\n{user_input_4.content}', inline=False)
                await ctx.channel.send(
                    "<:shiina_balance:558175954686705664>取引を開始します<:shiina_balance:558175954686705664>")
                deal_embed = await ctx.channel.send(embed=embed)
                await deal_embed.pin()

                # 24:00だとSQL突っ込むと詰むのでここで変える
                if hour_min_list == [24, 00]:
                    user_input_3.content = finish_time.strftime('%Y/%m/%d-%H:%M')

                user_input_2 = self.bot.stack_check(user_input_2)
                cur.execute("UPDATE deal SET deal_owner_id = %s, embed_message_id = %s, deal_item = %s, "
                            "deal_hope_price = %s, deal_end_time = %s, unit = %s, notice = %s WHERE ch_id = %s",
                            (ctx.author.id, deal_embed.id, user_input_1.content, str(user_input_2),
                             user_input_3.content, unit, user_input_4.content, ctx.channel.id))
                db.commit()

                try:
                    await asyncio.wait_for(ctx.channel.edit(name=ctx.channel.name.split('☆')[0]), timeout=3.0)
                except asyncio.TimeoutError:
                    pass

            else:
                kazu = 2
                await ctx.channel.purge(limit=kazu)
                await ctx.channel.send("初めからやり直してください。\n--------ｷﾘﾄﾘ線--------")

    @commands.command(aliases=["Tend"])
    @commands.cooldown(1, 1, type=commands.BucketType.channel)
    async def tend(self, ctx, price):
        if not self.bot.is_auction_category(ctx):
            embed = discord.Embed(description="このコマンドはオークションでのみ使用可能です。", color=0x4259fb)
            await ctx.send(embed=embed)
            return

        # priceのスタイルを調整
        price = f"{price}".replace(" ", "").replace("　", "")
        # そもそもオークションが開催してなかったらreturn
        if '☆' in ctx.channel.name:
            embed = discord.Embed(
                description=f'{ctx.author.display_name}さん。このチャンネルではオークションは行われていません',
                color=0xff0000)
            await ctx.channel.send(embed=embed)
            return

        # 少数は可能。
        def check_style(m: str) -> bool:
            """入札額の表記を確認する"""
            style_list = m.lower().replace("st", "").replace("lc", "").split("+")
            for i in range(len(style_list)):
                try:
                    float(style_list[i])
                except ValueError:
                    return False
            return True

        if check_style(price):
            # 開始価格、即決価格、現在の入札額を取り寄せ
            # auction[0] - auction[7]が各種auctionDBのデータとなる
            cur.execute("SELECT * FROM auction where ch_id = %s", (ctx.channel.id,))
            auction = cur.fetchone()
            cur.execute("SELECT * FROM tend where ch_id = %s", (ctx.channel.id,))
            tend_data = cur.fetchone()

            # ARRAYから最新の入札状況を引き抜く。初期状態は0
            tend = [tend_data[0], tend_data[1], tend_data[2]]

            # 条件に1つでも合致していたらreturn
            # 入札人物の判定
            if ctx.author.id == auction[1]:
                embed = discord.Embed(description="出品者が入札は出来ません。", color=0x4259fb)
                await ctx.send(embed=embed)
                return

            elif ctx.author.id == tend[1][-1] and (not self.bot.stack_check(price) >= int(auction[5])):
                embed = discord.Embed(description="同一人物による入札は出来ません。", color=0x4259fb)
                await ctx.send(embed=embed)
                return

            # 入札価格の判定
            if self.bot.stack_check(price) < int(auction[4]) or self.bot.stack_check(price) <= int(tend[2][-1]):
                embed = discord.Embed(description="入札価格が現在の入札価格、もしくは開始価格より低いです。", color=0x4259fb)
                await ctx.send(embed=embed)
                return

            elif auction[5] != "なし":
                if self.bot.stack_check(price) >= int(auction[5]):
                    embed = discord.Embed(description=f"即決価格と同額以上の価格が入札されました。{ctx.author.display_name}さんの落札です。",
                                          color=0x4259fb)
                    await ctx.send(embed=embed)
                    # オークション情報を取る
                    cur.execute(f"SELECT * FROM auction where ch_id = {ctx.channel.id}")
                    auction_data = cur.fetchone()
                    tend_price = f"{auction_data[7]}{self.bot.stack_check_reverse(self.bot.stack_check(price))}"

                    embed = discord.Embed(title="オークション取引結果", color=0x36a64f)
                    embed.add_field(name="落札日", value=f'\n\n{datetime.now().strftime("%Y/%m/%d")}', inline=False)
                    embed.add_field(name="出品者", value=f'\n\n{self.bot.get_user(id=auction_data[1]).display_name}',
                                    inline=False)
                    embed.add_field(name="品物", value=f'\n\n{auction_data[3]}', inline=False)
                    embed.add_field(name="落札者", value=f'\n\n{ctx.author.display_name}', inline=False)
                    embed.add_field(name="落札価格", value=f'\n\n{tend_price}', inline=False)
                    embed.add_field(name="チャンネル名", value=f'\n\n{ctx.channel.name}', inline=False)
                    await self.bot.get_channel(558132754953273355).send(embed=embed)
                    # オークションが終わったらその結果を通知
                    description = f"{ctx.channel.name}にて行われていた{self.bot.get_user(id=auction_data[1]).display_name}による 品物名: **{auction_data[3]}** のオークションは\n{ctx.author.display_name}により" \
                                  f"**{tend_price}**にて落札されました"
                    embed = discord.Embed(description=description, color=0xffaf60)
                    time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                    embed.set_footer(text=f'channel:{ctx.channel.name}\nTime:{time}')
                    await self.bot.dm_send(auction[1], embed)
                    await self.bot.dm_send(ctx.author.id, embed)

                    # ランキング送信
                    if "椎名" in ctx.channel.name:
                        # INSERTを実行。%sで後ろのタプルがそのまま代入される
                        cur.execute("INSERT INTO bid_ranking VALUES (%s, %s, %s, %s)",
                                    (ctx.author.display_name, auction_data[3], self.bot.stack_check(price),
                                     self.bot.get_user(id=auction_data[1]).display_name))
                        db.commit()
                        await self.bot.get_channel(705040893593387039).purge(limit=10)
                        await asyncio.sleep(0.1)
                        embeds = self.bot.create_high_bid_ranking()
                        for embed in embeds:
                            await self.bot.get_channel(705040893593387039).send(embed=embed)

                    embed = discord.Embed(description="オークションを終了しました", color=0xffaf60)
                    await ctx.channel.send(embed=embed)

                    auction_embed = await ctx.fetch_message(auction[2])
                    await auction_embed.unpin()

                    # chのdbを消し去る。これをもってその人のオークション開催回数を減らしたことになる
                    self.bot.reset_ch_db(ctx.channel.id, "a")
                    await ctx.channel.send('--------ｷﾘﾄﾘ線--------')
                    await asyncio.sleep(0.3)
                    try:
                        await asyncio.wait_for(ctx.channel.edit(name=f"{ctx.channel.name}☆"), timeout=3.0)
                    except asyncio.TimeoutError:
                        pass
                    return

            elif self.bot.stack_check(price) == 0:
                embed = discord.Embed(description="不正な値です。", color=0x4259fb)
                await ctx.send(embed=embed)
                return

            # 入札時間の判定
            time = datetime.now() + timedelta(hours=1)
            finish_time = datetime.strptime(auction[6], r"%Y/%m/%d-%H:%M")
            flag = False

            if time > finish_time:
                embed = discord.Embed(description="終了1時間前以内の入札です。終了時刻を1日延長します。", color=0x4259fb)
                await ctx.send(embed=embed)
                await asyncio.sleep(2)

                embed = discord.Embed(title="オークション内容", color=0xffaf60)
                embed.add_field(name="出品者", value=f'\n\n{self.bot.get_user(auction[1]).display_name}')
                embed.add_field(name="出品物", value=f'\n\n{auction[3]}')
                value = "なし" if auction[5] == "なし" else f"{auction[7]}{self.bot.stack_check_reverse(auction[5])}"
                embed.add_field(name="開始価格", value=f'\n\n{auction[7]}{self.bot.stack_check_reverse(auction[4])}',
                                inline=False)
                embed.add_field(name="即決価格", value=f'\n\n{value}', inline=False)
                finish_time = (finish_time + timedelta(days=1)).strftime("%Y/%m/%d-%H:%M")
                embed.add_field(name="終了日時", value=f'\n\n{finish_time}')
                embed.add_field(name="特記事項", value=f'\n\n{auction[8]}')
                msg = await ctx.fetch_message(auction[2])
                await msg.edit(embed=embed)  # メッセージの更新で対応する
                # 変更点をUPDATE
                cur.execute("UPDATE auction SET embed_message_id = %s, auction_end_time = %s WHERE ch_id = %s",
                            (msg.id, finish_time, ctx.channel.id))
                db.commit()

                # 延長をオークション主催者に伝える
                flag = True

            # オークション情報が変わってる可能性があるのでここで再度auctionのデータを取る
            cur.execute("SELECT * FROM auction where ch_id = %s", (ctx.channel.id,))
            auction = cur.fetchone()

            # チャンネルid, 入札者idのlist, 入札額のリストが入っている
            tend_data = [tend_data[0], list(tend_data[1]), list(tend_data[2])]

            updated_tend_data = tend_data.copy()
            updated_tend_data[1].append(ctx.author.id)
            updated_tend_data[2].append(self.bot.stack_check(price))

            updated_tend_data[1] = self.bot.list_to_tuple_string(updated_tend_data[1])
            updated_tend_data[2] = self.bot.list_to_tuple_string(updated_tend_data[2])

            cur.execute(
                f"UPDATE tend SET tender_id = '{updated_tend_data[1]}', tend_price = '{updated_tend_data[2]}' WHERE ch_id = %s",
                (ctx.channel.id,))
            db.commit()
            await ctx.message.delete()  # !tendのメッセージを削除する
            await asyncio.sleep(0.1)

            if flag:  # 終了時間が延長される場合は通知する
                text = f"チャンネル名: {self.bot.get_channel(id=auction[0]).name}において終了1時間前に入札があったため終了時刻を1日延長します。"
                embed = discord.Embed(description=text, color=0x4259fb)
                time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                embed.set_footer(text=f'channel:{ctx.channel.name}\nTime:{time}')
                await self.bot.dm_send(auction[1], embed)

            time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            avatar_url = ctx.author.avatar_url_as(format="png")
            image = requests.get(avatar_url)
            image = io.BytesIO(image.content)
            image.seek(0)
            image = Image.open(image)
            image = image.resize((100, 100))
            image.save("./icon.png")
            image = discord.File("./icon.png", filename="icon.png")
            embed = discord.Embed(description=f"入札者: **{ctx.author.display_name}**, \n"
                                              f"入札額: **{auction[7]}{self.bot.stack_check_reverse(self.bot.stack_check(price))}**\n",
                                  color=0x4259fb)
            embed.set_image(url="attachment://icon.png")
            embed.set_footer(text=f"入札時刻: {time}")
            await ctx.send(file=image, embed=embed)

            # 一つ前のtenderにDMする。ただし存在を確認してから。[0,なにか](初回tend)は送信しない(before_tender==0)
            # 今までの状態だと初回IndexErrorが発生するので順番を前に持ってきました
            if len(tend[1]) == 1:  # 初回の入札(tend_data=[0]の状態)は弾く
                return

            before_tender_id = int(tend[1][-1])

            text = f"チャンネル名: {ctx.channel.name}において貴方より高い入札がされました。\n" \
                   f"入札者: {ctx.author.display_name}, 入札額: **{auction[7]}{self.bot.stack_check_reverse(self.bot.stack_check(price))}**\n"
            embed = discord.Embed(description=text, color=0x4259fb)
            time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            embed.set_footer(text=f'channel:{ctx.channel.name}\nTime:{time}')

            await self.bot.dm_send(before_tender_id, embed)

        else:
            embed = discord.Embed(description=f"{ctx.author.display_name}さん。入力した値が不正です。もう一度正しく入力を行ってください。",
                                  color=0x4259fb)
            await ctx.send(embed=embed)

    @commands.command(aliases=["Add"])
    @commands.cooldown(1, 1, type=commands.BucketType.channel)
    async def add(self, ctx: commands.Context, add_price: str):
        if not self.bot.is_auction_category(ctx):
            embed = discord.Embed(description="このコマンドはオークションでのみ使用可能です。", color=0x4259fb)
            await ctx.send(embed=embed)
            return
        cur.execute("SELECT * FROM tend where ch_id = %s", (ctx.channel.id,))
        tend_data = cur.fetchone()
        tend_data = [tend_data[0], list(tend_data[1]), list(tend_data[2])]

        if tend_data[1][-1] == 0:
            embed = discord.Embed(description="入札がなにもありません。最初の入札はtendコマンドで行ってください。", color=0x4259fb)
            await ctx.send(embed=embed)
            return

        add_price = self.bot.stack_check(add_price)
        if add_price == 0:
            await ctx.send("入力値が不正です。")
            return

        price = tend_data[2][-1] + add_price
        tend = self.bot.get_command("tend")
        await ctx.invoke(tend, price)

    @commands.command()
    async def remand(self, ctx):
        if self.bot.is_auction_category(ctx):

            cur.execute("SELECT * FROM auction where ch_id = %s", (ctx.channel.id,))
            auction_data = cur.fetchone()

            # オークションが行われていなければ警告して終了
            if "☆" in ctx.channel.name:
                embed = discord.Embed(description="このコマンドはオークション開催中のみ使用可能です。", color=0x4259fb)
                await ctx.send(embed=embed)
                return
            # オークション主催者じゃなければ警告して終了
            elif ctx.author.id != auction_data[1]:
                embed = discord.Embed(description="このコマンドはオークション主催者のみ使用可能です。", color=0x4259fb)
                await ctx.send(embed=embed)
                return
            else:
                cur.execute("select * from tend where ch_id = %s", (ctx.channel.id,))
                tend_data = cur.fetchone()
                tend_data = [tend_data[0], list(tend_data[1]), list(tend_data[2])]

                tend_data[1].pop(-1)
                tend_data[2].pop(-1)

                # 0の時は最初の入札者になっているのでreturn
                if tend_data[1][-1] == 0:
                    embed = discord.Embed(description="最初の入札者です。これ以上の差し戻しは出来ません。", color=0x4259fb)
                    await ctx.send(embed=embed)
                    return

                tend_data_str_1 = self.bot.list_to_tuple_string(tend_data[1])
                tend_data_str_2 = self.bot.list_to_tuple_string(tend_data[2])

                cur.execute(
                    f"UPDATE tend SET tender_id = '{tend_data_str_1}', tend_price = '{tend_data_str_2}' WHERE ch_id = %s",
                    (ctx.channel.id,))
                db.commit()
                # 1つ戻した状態で入札状態を出力
                # await delete_to(ctx, auction_data[2])

                time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                avatar_url = self.bot.get_user(id=int(tend_data[1][-1])).avatar_url_as(format="png")
                image = requests.get(avatar_url)
                image = io.BytesIO(image.content)
                image.seek(0)
                image = Image.open(image)
                image = image.resize((100, 100))
                image.save("./icon.png")
                image = discord.File("./icon.png", filename="icon.png")
                embed = discord.Embed(
                    description=f"入札者: **{self.bot.get_user(id=int(tend_data[1][-1])).display_name}**, \n"
                                f"入札額: **{auction_data[7]}{self.bot.stack_check_reverse(self.bot.stack_check(tend_data[2][-1]))}**\n",
                    color=0x4259fb
                )
                embed.set_image(url="attachment://icon.png")
                embed.set_footer(text=f"入札時刻: {time}")
                await ctx.channel.send(file=image, embed=embed)

        else:
            embed = discord.Embed(description="このコマンドはオークションでのみ使用可能です。", color=0x4259fb)
            await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 1, type=commands.BucketType.channel)
    async def consent(self, ctx):
        if not self.bot.is_normal_category(ctx):
            return

        if '☆' in ctx.channel.name:
            embed = discord.Embed(
                description=f'{ctx.author.display_name}さん。このチャンネルでは取引は行われていません',
                color=0xff0000)
            await ctx.channel.send(embed=embed)
            return

        # chのdbを消し去る
        cur.execute("SELECT * from deal WHERE ch_id = %s", (ctx.channel.id,))
        dael_data = cur.fetchone()
        owner = self.bot.get_user(int(dael_data[1]))
        await owner.send(f"{ctx.author.name}が{ctx.channel.mention}の取引を承諾しました")

        deal_embed = await ctx.fetch_message(dael_data[2])
        await deal_embed.unpin()

        self.bot.reset_ch_db(ctx.channel.id, "d")

        await ctx.channel.send('--------ｷﾘﾄﾘ線--------')
        try:
            await asyncio.wait_for(ctx.channel.edit(name=f"{ctx.channel.name}☆"), timeout=3.0)
        except asyncio.TimeoutError:
            pass

    @commands.command()
    async def tend_history(self, ctx):
        cur.execute("SELECT * FROM auction where ch_id = %s", (ctx.channel.id,))
        auction_data = cur.fetchone()

        # オークションが行われていなければ警告して終了
        if "☆" in ctx.channel.name:
            embed = discord.Embed(description="このコマンドはオークション開催中のみ使用可能です。", color=0x4259fb)
            await ctx.send(embed=embed)
            return
        # オークション主催者じゃなければ警告して終了
        elif ctx.author.id != auction_data[1]:
            embed = discord.Embed(description="このコマンドはオークション主催者のみ使用可能です。", color=0x4259fb)
            await ctx.send(embed=embed)
            return
        else:
            cur.execute("select * from tend where ch_id = %s", (ctx.channel.id,))
            tend_data = cur.fetchone()

            tendrs_data = tend_data[1]
            tend_prices = tend_data[2]

            discription = ""

            for i in range(1, len(tend_data[1])):
                discription += f"{i}: {self.bot.get_user(id=tendrs_data[i]).display_name}, {auction_data[7]}{self.bot.stack_check_reverse(tend_prices[i])}\n\n"

                if len(discription) >= 1800:
                    await ctx.channel.send(embed=discord.Embed(description=discription, color=0xffaf60))
                    discription = ""

            await ctx.channel.send(embed=discord.Embed(description=discription, color=0xffaf60))


def setup(bot):
    bot.add_cog(AuctionDael(bot))

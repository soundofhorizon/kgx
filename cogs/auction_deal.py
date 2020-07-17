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
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def bidscore(self, ctx, pt):  # カウントしてその数字に対応する役職を付与する
        if not ctx.channel.id == 558265536430211083:
            return

        channel = self.bot.get_channel(602197766218973185)
        p = re.compile(r'^[0-9]+$')
        if p.fullmatch(pt):
            kazu = int(pt)
            cur.execute("SELECT bid_score FROM user_data where user_id = %s", (ctx.author.id,))
            oldscore = list(cur.fetchone())
            new_score = oldscore[0] + kazu
            cur.execute("UPDATE user_data SET bid_score = %s WHERE user_id = %s", (new_score, ctx.author.id))
            db.commit()

            embed = discord.Embed(description=f'**{ctx.author.display_name}**の現在の落札ポイントは**{new_score}**です。',
                                  color=0x9d9d9d)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url, )  # ユーザー名+ID,アバターをセット
            await channel.send(embed=embed)
            before, after, embed = self.bot.check_role(new_score, ctx.author, ctx)
            await ctx.author.remove_roles(before)
            await ctx.author.add_roles(after)
            if embed is not None:
                await ctx.channel.send(embed=embed)
            embed = discord.Embed(description=f'**{ctx.author.display_name}**に落札ポイントを付与しました。', color=0x9d9d9d)
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url, )  # ユーザー名+ID,アバターをセット
            await ctx.channel.send(embed=embed)
            await asyncio.sleep(0.5)
            # ランキングを出力する
            channel = self.bot.get_channel(677905288665235475)
            # とりあえず、ランキングチャンネルの中身を消す
            await channel.purge(limit=1)
            await channel.send(embed=self.bot.create_ranking_embed())

    @commands.command()
    async def start(self, ctx):
        # 2つ行ってる場合はreturn
        user = ctx.author.id
        if self.bot.get_user_auction_count(user) >= 2:
            description = "貴方はすでに取引を2つ以上行っているためこれ以上取引を始められません。\n" \
                          "行っている取引が2つ未満になってから再度行ってください。"
            await ctx.channel.send(embed=discord.Embed(description=description, color=0xf04747))
            await ctx.channel.send("--------ｷﾘﾄﾘ線--------")
            return

        # オークション系
        if self.bot.is_auction_category(ctx):

            # 既にオークションが行われていたらreturn
            if "☆" not in ctx.channel.name:
                description = "このチャンネルでは既にオークションが行われています。\n☆がついているチャンネルでオークションを始めてください。"
                await ctx.channel.send(embed=discord.Embed(description=description, color=0xf04747))
                await asyncio.sleep(3)
                await ctx.channel.purge(limit=2)
                return

            # メッセージを待つだけの変数。ほかの人からの入力は受け付けないようにしている
            def check(m):
                if m.author.bot:
                    return
                return m.channel == ctx.channel and m.author == ctx.author

            # 日付型になってるかを確かめる
            def check2(m):
                if m.author.bot:
                    return
                    # フォーマットされたdatetimeとの変換を試みTrueかどうかを調べる
                try:
                    return m.channel == ctx.channel and re.match(
                        r"[0-9]{4}/[0-9]{2}/[0-9]{2}-[0-9]{2}:[0-9]{2}",
                        m.content) and datetime.strptime(m.content, "%Y/%m/%d-%H:%M") and m.author == ctx.author
                except ValueError:
                    return False

            # 価格フォーマットチェック
            def check3(m):
                if m.author.bot:
                    return
                if m.channel != ctx.channel:
                    return False
                # 〇st+△(記号はint)もしくは△であるのを確かめる
                else:
                    return (re.match(r"[0-9]{0,99}LC\+[0-9]{1,99}ST\+[0-9]{1,2}", m.content.upper()) or re.match(
                        r"[0-9]{1,99}ST\+[0-9]{1,2}", m.content.upper()) or re.match(r"[1-9]{1,2}", m.content)
                            ) and m.author == ctx.author

            # 価格フォーマットチェック(なしを含む)
            def check4(m):
                if m.author.bot:
                    return
                elif m.author == ctx.author:
                    if m.channel != ctx.channel:
                        return False
                    # 〇st+△(記号はint)もしくは△であるのを確かめる
                    return (re.match(r"[0-9]{0,99}LC\+[0-9]{1,99}ST\+[0-9]{1,2}", m.content.upper()) or re.match(
                        r"[0-9]{1,99}ST\+[0-9]{1,2}", m.content.upper()) or re.match(r"[1-9]{1,2}", m.content)
                            or m.content == "なし") and m.author == ctx.author

            # 単位の設定
            unit = ""
            if self.bot.is_siina_category(ctx):
                unit = "椎名"
            elif self.bot.is_gacha_category(ctx):
                unit = "ガチャ券"
            else:
                embed = discord.Embed(description="何による取引ですか？単位を入力してください。(ex.GTギフト券, ガチャリンゴ, エメラルド etc)",
                                      color=0xffaf60)
                await ctx.channel.send(embed=embed)
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
            await ctx.channel.send(embed=embed)
            user_input_1 = await self.bot.wait_for('message', check=check)

            embed = discord.Embed(description="開始価格を入力してください。\n**※次のように入力してください。"
                                              "【〇LC+△ST+□】 or　【〇ST+△】 or 【△】 ex.1lc+1st+1 or 1st+1 or 32**",
                                  color=0xffaf60)
            await ctx.channel.send(embed=embed)
            user_input_2 = await self.bot.wait_for('message', check=check3)
            user_input_2 = self.bot.stack_check_reverse(self.bot.stack_check(user_input_2.content))
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
            now = datetime.now()
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

            await ctx.channel.purge(limit=13)
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
                kazu = 2
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
                await ctx.channel.edit(name=ctx.channel.name.split('☆')[0])

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

            # メッセージを待つだけの変数。ほかの人からの入力は受け付けないようにしている
            def check(m):
                if m.author.bot:
                    return
                return m.channel == ctx.channel and m.author == ctx.author

            # 日付型になってるかを確かめる
            def check2(m):
                if m.author.bot:
                    return
                    # フォーマットされたdatetimeとの変換を試みTrueかどうかを調べる
                try:
                    return m.channel == ctx.channel and re.match(
                        r"[0-9]{4}/[0-9]{2}/[0-9]{2}-[0-9]{2}:[0-9]{2}",
                        m.content) and datetime.strptime(m.content, "%Y/%m/%d-%H:%M") and m.author == ctx.author
                except ValueError:
                    return False

            # 価格フォーマットチェック
            def check3(m):
                if m.author.bot:
                    return
                if m.channel != ctx.channel:
                    return False
                # 〇st+△(記号はint)もしくは△であるのを確かめる
                else:
                    return (re.match(r"[0-9]{0,99}LC\+[0-9]{1,99}ST\+[0-9]{1,2}", m.content.upper()) or re.match(
                        r"[0-9]{1,99}ST\+[0-9]{1,2}", m.content.upper()) or re.match(r"[1-9]{1,2}", m.content)
                            ) and m.author == ctx.author

            # 単位の設定
            unit = ""
            if self.bot.is_siina_category(ctx):
                unit = "椎名"
            elif self.bot.is_gacha_category(ctx):
                unit = "ガチャ券"
            else:
                embed = discord.Embed(description="何による取引ですか？単位を入力してください。(ex.GTギフト券, ガチャリンゴ, エメラルド etc)",
                                      color=0xffaf60)
                await ctx.channel.send(embed=embed)
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
            await ctx.channel.send(embed=embed)
            user_input_1 = await self.bot.wait_for('message', check=check)

            embed = discord.Embed(description="希望価格を入力してください。\n**※次のように入力してください。"
                                              "【〇LC+△ST+□】 or　【〇ST+△】 or 【△】 ex.1LC+1ST+1 or 1ST+1 or 32**",
                                  color=0xffaf60)
            await ctx.channel.send(embed=embed)
            user_input_2 = await self.bot.wait_for('message', check=check3)
            user_input_2 = self.bot.stack_check_reverse(self.bot.stack_check(user_input_2.content))
            embed = discord.Embed(
                description="取引終了日時を入力してください。\n**注意！**時間の書式に注意してください！\n"
                            "例　5月14日の午後8時に終了したい場合：\n**2020/05/14-20:00**と入力してください。\nこの形でない場合認識されません！\n"
                            "**間違えて打ってしまった場合その部分は必ず削除してください。**",
                color=0xffaf60)
            await ctx.channel.send(embed=embed)
            user_input_3 = await self.bot.wait_for('message', check=check2)

            now = datetime.now()
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

            kazu = 11
            await ctx.channel.purge(limit=kazu)

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
                kazu = 2
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
                await ctx.channel.edit(name=ctx.channel.name.split('☆')[0])

                user_input_2 = self.bot.stack_check(user_input_2)
                cur.execute("UPDATE deal SET deal_owner_id = %s, embed_message_id = %s, deal_item = %s, "
                            "deal_hope_price = %s, deal_end_time = %s, unit = %s, notice = %s WHERE ch_id = %s",
                            (ctx.author.id, deal_embed.id, user_input_1.content, str(user_input_2),
                             user_input_3.content, unit, user_input_4.content, ctx.channel.id))
                db.commit()

            else:
                kazu = 2
                await ctx.channel.purge(limit=kazu)
                await ctx.channel.send("初めからやり直してください。\n--------ｷﾘﾄﾘ線--------")

    @commands.command()
    async def tend(self, ctx, *, price):
        if self.bot.is_auction_category(ctx):

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
            def check_style(m):
                style_list = m.lower().replace("st", "").replace("lc", "").split("+")
                for i in range(len(style_list)):
                    try:
                        float(style_list[i])
                    except ValueError:
                        return False
                return True

            async def delete_to(ctx, ch_id):
                delete_ch = ctx.channel
                msg = await delete_ch.fetch_message(ch_id)
                await delete_ch.purge(limit=None, after=msg)

            if check_style(price):
                # 開始価格、即決価格、現在の入札額を取り寄せ
                # auction[0] - auction[7]が各種auctionDBのデータとなる
                cur.execute("SELECT * FROM auction where ch_id = %s", (ctx.channel.id,))
                auction = cur.fetchone()
                cur.execute("SELECT * FROM tend where ch_id = %s", (ctx.channel.id,))
                tend = cur.fetchone()

                # 条件に1つでも合致していたらreturn

                # 入札人物の判定
                if ctx.author.id == auction[1]:
                    embed = discord.Embed(description="出品者が入札は出来ません。", color=0x4259fb)
                    await ctx.send(embed=embed)
                    return
                # elif ctx.author.id == tend[1]:
                #    embed = discord.Embed(description="同一人物による入札は出来ません。", color=0x4259fb)
                #    await ctx.send(embed=embed)
                #    return
                # 入札価格の判定
                if self.bot.stack_check(price) < int(auction[4]) or self.bot.stack_check(price) <= int(tend[2]):
                    embed = discord.Embed(description="入札価格が現在の入札価格、もしくは開始価格より低いです。", color=0x4259fb)
                    await ctx.send(embed=embed)
                    return
                elif auction[5] != "なし":
                    if self.bot.stack_check(price) >= int(auction[5]):
                        embed = discord.Embed(description=f"即決価格より高い価格が入札されました。{ctx.author.display_name}さんの落札です。",
                                              color=0x4259fb)
                        await ctx.send(embed=embed)
                        # todo ここにbid処理を挟む
                        return
                elif self.bot.stack_check(price) == 0:
                    embed = discord.Embed(description="不正な値です。", color=0x4259fb)
                    await ctx.send(embed=embed)
                    return
                # 入札時間の判定
                time = datetime.now() + timedelta(hours=1)
                finish_time = datetime.strptime(auction[6], r"%Y/%m/%d-%H:%M")
                text = "None"
                if time > finish_time:
                    embed = discord.Embed(description="終了1時間前以内の入札です。終了時刻を1日延長します。", color=0x4259fb)
                    await ctx.send(embed=embed)
                    await asyncio.sleep(2)

                    await delete_to(ctx, auction[2])
                    await asyncio.sleep(0.1)
                    await ctx.channel.purge(limit=1)
                    embed = discord.Embed(title="オークション内容", color=0xffaf60)
                    embed.add_field(name="出品者", value=f'\n\n{self.bot.get_user(auction[1]).display_name}', inline=True)
                    embed.add_field(name="出品物", value=f'\n\n{auction[3]}', inline=True)
                    value = "なし" if auction[5] == "なし" else f"{auction[7]}{self.bot.stack_check_reverse(auction[5])}"
                    embed.add_field(name="開始価格", value=f'\n\n{auction[7]}{self.bot.stack_check_reverse(auction[4])}', inline=False)
                    embed.add_field(name="即決価格", value=f'\n\n{value}', inline=False)
                    finish_time = (finish_time + timedelta(days=1)).strftime("%Y/%m/%d-%H:%M")
                    embed.add_field(name="終了日時", value=f'\n\n{finish_time}', inline=True)
                    embed.add_field(name="特記事項", value=f'\n\n{auction[8]}', inline=True)
                    embed_id = await ctx.send(embed=embed)
                    # 変更点をUPDATE
                    cur.execute("UPDATE auction SET embed_message_id = %s, auction_end_time = %s WHERE ch_id = %s",
                                (embed_id.id, finish_time, ctx.channel.id))
                    db.commit()

                    # 延長をオークション主催者に伝える
                    text = f"{self.bot.get_user(id=auction[1]).mention}さん、終了1時間前に入札があったため終了時刻を1日延長します。"

                # オークションが変わってる可能性があるのでここで再度auctionのデータを取る
                cur.execute("SELECT * FROM auction where ch_id = %s", (ctx.channel.id,))
                auction = cur.fetchone()
                cur.execute("UPDATE tend SET tender_id = %s, tend_price = %s WHERE ch_id = %s",
                            (ctx.author.id, self.bot.stack_check(price), ctx.channel.id))
                db.commit()
                await asyncio.sleep(0.1)
                await delete_to(ctx, auction[2])
                if text != "None":
                    embed = discord.Embed(description=text, color=0x4259fb)
                    time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                    embed.set_footer(text=f'channel:{ctx.channel.name}\nTime:{time}')
                    await self.bot.get_channel(id=auction_notice_ch_id).send(embed=embed)
                time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                # todo ここをembedに置き換える。iconを貼りたい・。・
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
                                      color=0x4259fb
                                      )
                embed.set_image(url="attachment://icon.png")
                embed.set_footer(text=f"入札時刻: {time}")
                await ctx.channel.send(file=image, embed=embed)
            else:
                embed = discord.Embed(description=f"{ctx.author.display_name}さん。入力した値が不正です。もう一度正しく入力を行ってください。",
                                      color=0x4259fb)
                await ctx.send(embed=embed)

        else:
            embed = discord.Embed(description="このコマンドはオークションでのみ使用可能です。", color=0x4259fb)
            await ctx.send(embed=embed)

    @commands.command()
    async def bid(self, ctx):
        if self.bot.is_auction_category(ctx):
            if '☆' in ctx.channel.name:
                embed = discord.Embed(
                    description=f'{ctx.author.display_name}さん。このチャンネルではオークションは行われていません',
                    color=0xff0000)
                await ctx.channel.send(embed=embed)
            else:
                auction_finish_user_id = ctx.author.id

                def check(m):
                    if m.author.bot:
                        return
                    elif m.author.id == auction_finish_user_id:
                        return m.channel == ctx.channel and "," not in m.content

                def check_siina_style(m):
                    if m.author.bot:
                        return
                    elif "椎名" in m.content:
                        return m.channel == ctx.channel

                kazu = 6
                embed = discord.Embed(
                    description="注:**全体の入力を通して[,]の記号は使用できません。何か代替の記号をお使いください。**\n\n"
                                "出品した品物名を書いてください。",
                    color=0xffaf60)
                await ctx.channel.send(embed=embed)
                user_input_1 = await self.bot.wait_for('message', check=check)
                embed = discord.Embed(description="落札者のユーザーネームを書いてください。", color=0xffaf60)
                await ctx.channel.send(embed=embed)
                user_input_2 = await self.bot.wait_for('message', check=check)
                description = "落札価格を入力してください。\n"
                if self.bot.is_siina_category(ctx):
                    description += "以下のような形式以外は認識されません。(個はなくてもOK): **椎名○○st+△(個)(椎名○○(個)も可)\n" \
                                   "ex: 椎名5st+16個 椎名336個"
                embed = discord.Embed(description=description, color=0xffaf60)
                await ctx.channel.send(embed=embed)
                siina_amount = -1
                user_input_3 = ""
                if self.bot.is_siina_category(ctx):
                    frag = True
                    while frag:
                        user_input_3 = await self.bot.wait_for('message', check=check_siina_style)
                        siina_amount = self.bot.stack_check(user_input_3.content)
                        if siina_amount == 0:
                            await ctx.channel.send("値が不正です。椎名○○st+△(個)の○と△には整数以外は入りません。再度入力してください。")
                            kazu += 2
                        else:
                            frag = False
                else:
                    user_input_3 = await self.bot.wait_for('message', check=check)
                await ctx.channel.purge(limit=kazu)
                embed = discord.Embed(description="オークション終了報告を受け付けました。", color=0xffaf60)
                await ctx.channel.send(embed=embed)

                # ランキング送信
                if self.bot.is_siina_category(ctx):
                    # INSERTを実行。%sで後ろのタプルがそのまま代入される
                    cur.execute("INSERT INTO bid_ranking VALUES (%s, %s, %s, %s)",
                                (user_input_2.content, user_input_1.content, siina_amount, ctx.author.display_name))
                    db.commit()
                    await self.bot.get_channel(705040893593387039).purge(limit=10)
                    await asyncio.sleep(0.1)
                    embed = self.bot.create_high_bid_ranking()
                    for i in range(len(embed)):
                        await self.bot.get_channel(705040893593387039).send(embed=embed[i])

                # 記録送信
                channel = self.bot.get_channel(558132754953273355)
                d = datetime.now()  # 現在時刻の取得
                time = d.strftime("%Y/%m/%d")
                embed = discord.Embed(title="オークション取引結果", color=0x36a64f)
                embed.add_field(name="落札日", value=f'\n\n{time}', inline=False)
                embed.add_field(name="出品者", value=f'\n\n{ctx.author.display_name}', inline=False)
                embed.add_field(name="品物", value=f'\n\n{user_input_1.content}', inline=False)
                embed.add_field(name="落札者", value=f'\n\n{user_input_2.content}', inline=False)
                embed.add_field(name="落札価格", value=f'\n\n{user_input_3.content}', inline=False)
                embed.add_field(name="チャンネル名", value=f'\n\n{ctx.channel}', inline=False)
                await channel.send(embed=embed)

                # chのdbを消し去る。これをもってその人のオークション開催回数を減らしたことになる
                self.bot.reset_ch_db(ctx.channel.id, "a")

                await ctx.channel.send('--------ｷﾘﾄﾘ線--------')
                await asyncio.sleep(0.3)
                await ctx.channel.edit(name=ctx.channel.name + '☆')

        elif self.bot.is_normal_category(ctx):
            description = "ここは通常取引チャンネルです。終了報告は``!end``をお使いください。"
            embed = discord.Embed(description=description, color=0x4259fb)
            await ctx.channel.send(embed=embed)

    @commands.command()
    async def end(self, ctx):
        if not self.bot.is_normal_category(ctx):
            return
        # chのdbを消し去る
        self.bot.reset_ch_db(ctx.channel.id, "d")

        await ctx.channel.send('--------ｷﾘﾄﾘ線--------')
        await ctx.channel.edit(name=ctx.channel.name + '☆')


def setup(bot):
    bot.add_cog(AuctionDael(bot))
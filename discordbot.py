# coding=utf-8
import asyncio
import os
import random
import re
import traceback
from datetime import datetime

import bs4
import discord
import redis
import requests
from discord import Embed
from discord.ext import commands, tasks  # フレームワークをimport

client = discord.Client()

# Redisに接続
pool = redis.ConnectionPool.from_url(
    url=os.environ['REDIS_URL'],
    db=0,
    decode_responses=True
)

rc = redis.StrictRedis(connection_pool=pool)

# Redisに接続
pool2 = redis.ConnectionPool.from_url(
    url=os.environ['HEROKU_REDIS_ORANGE_URL'],
    db=0,
    decode_responses=True
)

rc2 = redis.StrictRedis(connection_pool=pool2)
bot = commands.Bot(command_prefix='!')


def help():
    description = "<:shiina_balance:558175954686705664>!start\n\n"
    description += "オークションを始めるためのコマンドです。オークションチャンネルでのみ使用可能です。\n\n"
    description += "-------\n"
    description += "<:siina:558251559394213888>!bid\n\n"
    description += "オークションが終わったときにオークション内容を報告するためのコマンドです。\n"
    description += "ここで報告した内容は <#558132754953273355> に表示されます\n\n"
    description += "-------\n"
    description += "<:shiina_balance:558175954686705664>!end\n\n"
    description += "取引を終了するためのコマンドです。\n\n"
    description += "-------\n"
    description += "<:siina:558251559394213888>!bidscore 申請する落札ポイント\n\n"
    description += "落札ポイントを申請します。 <#558265536430211083> に入力すると申請できます。\n"
    description += "<#602197766218973185> に現在の落札ポイントが通知されます。\n"
    description += "<#677905288665235475> に現在の落札ポイントのランキングが表示されます。\n\n"
    description += "(例)!bidscore 2 {これで、自分の落札ポイントが2ポイント加算される。}\n\n"
    description += "-------\n"
    description += "<:shiina_balance:558175954686705664>!version\n\n"
    description += "現在のBotのバージョンを表示します。\n\n"
    description += "-------\n"
    description += "<:siina:558251559394213888>!help\n\n"
    description += "このBotのヘルプを表示します。\n\n"
    description += "-------\n"
    description += "**ここから以下は運営専用**\n--------\n"
    description += "<:shiina_balance:558175954686705664>!del 消去するメッセージの数(int)\n\n"
    description += "メッセージを指定した数、コマンドを打ったチャンネルの最新のメッセージから消します。\n\n"
    description += "-------\n"
    description += "<:siina:558251559394213888>!checkAllUserID\n\n"
    description += "<#642052474672250880> に、現在このサーバーにいるメンバーのニックネームとユーザーIDをセットで照会します。\n\n"
    description += "-------\n"
    description += "<:shiina_balance:558175954686705664>!bidscoreGS モード ユーザーID 落札ポイント(setモードのみ)\n\n"
    description += "特定の人の落札ポイントを調べたり、変更するために使用します。\n\n"
    description += "<mode:GET>　getモードでは、特定の人の落札ポイントを調べられます。\nコマンドは以下のように使用します。\n\n"
    description += "(例)!bidscoreGS get 251365193127297024\n{これで、EternalHorizonの落札ポイントがわかる}\n\n"
    description += "<mode:SET>　setモードでは、特定の人の落札ポイントを変更できます。\nコマンドは以下のように使用します。\n\n"
    description += "(例)!bidscoreGS set 251365193127297024 10\n{これで、EternalHorizonの落札ポイントが10ポイントに変更される。}\n\n "
    description += "-------\n"
    description += "<:siina:558251559394213888>!bidscoreRanking\n\n"
    description += "<#677905288665235475>を更新します\n\n"
    description += "-------\n"
    description += "<:shiina_balance:558175954686705664>!stop_deal\n\n"
    description += "問答無用で取引を停止します。オークションでも通常取引でも適用されます。\n\n"
    description += "-------\n"
    description += "<:siina:558251559394213888>!check_role\n\n"
    description += "全員の役職が落札ポイントと正しいものになってるかを照合します。\n\n"
    description += "-------\n"
    description += "<:shiina_balance:558175954686705664>!insert_ranking_data\n\n"
    description += "ランキングデータ送信用。落札者,落札物,落札金額,出品者ID\n\n"
    description += "-------\n"
    description += "<:siina:558251559394213888>!set_user_auction_count USER_ID 開催個数\n\n"
    description += "そのユーザーの現在のオークションの開催個数を指定します。\n\n"
    description += "-------\n"
    embed = discord.Embed(description=description, color=0x66cdaa)
    return embed


@tasks.loop(seconds=20)
async def presence_chenge_task():
    game = discord.Game(f"{client.get_guild(558125111081697300).member_count}人を監視中")
    await client.change_presence(status=discord.Status.online, activity=game)


@client.event
async def on_ready():
    presence_chenge_task.start()
    await client.get_channel(678083611697872910).purge(limit=1)
    await client.get_channel(678083611697872910).send(embed=help())


@client.event  # 入ってきたときの処理
async def on_member_join(member):
    if member.author.bot:
        role = discord.utils.get(member.guild.roles, name="bot")
        await member.add_roles(role)
        return

    role = discord.utils.get(member.guild.roles, name="新人")
    await member.add_roles(role)


@client.event
async def on_message_delete(message):
    if message.author.bot:
        return

    d = datetime.now()  # 現在時刻の取得
    time = d.strftime("%Y/%m/%d %H:%M:%S")
    embed = Embed(description=f'**Deleted in <#{message.channel.id}>**\n\n{message.content}\n\n',
                  color=0xff0000)  # 発言内容をdescriptionにセット
    embed.set_author(name=message.author, icon_url=message.author.avatar_url, )  # ユーザー名+ID,アバターをセット
    embed.set_footer(text=f'User ID：{message.author.id} Time：{time}',
                     icon_url=message.guild.icon_url, )  # チャンネル名,時刻,鯖のアイコンをセット
    ch = message.guild.get_channel(628807266753183754)
    await ch.send(embed=embed)


@client.event  # point付与の術
async def on_message_edit(before, after):
    # メッセージ送信者がBotだった場合は無視する
    if before.author.bot:
        return
    # URLの場合は無視する
    if "http" in before.content:
        return

    d = datetime.now()  # 現在時刻の取得
    time = d.strftime("%Y/%m/%d %H:%M:%S")
    # 発言内容をdescriptionにセット
    embed = Embed(
        description=f'**Changed in <#{before.channel.id}>**\n\n'
                    f'**before**\n{before.content}\n\n'
                    f'**after**\n{after.content}\n\n',
        color=0x1e90ff
    )
    embed.set_author(name=before.author, icon_url=before.author.avatar_url, )  # ユーザー名+ID,アバターをセット
    embed.set_footer(text=f'User ID：{before.author.id} Time：{time}',
                     icon_url=before.guild.icon_url, )  # チャンネル名,時刻,鯖のアイコンをセット
    ch = before.guild.get_channel(628807266753183754)
    await ch.send(embed=embed)


@client.event  # point付与の術
async def on_message(message):
    # メッセージ送信者がBotだった場合は無視する
    if message.author.bot:
        return
    try:
        def checkRole(newscore, user):
            role1 = discord.utils.get(message.guild.roles, name="新星")
            role2 = discord.utils.get(message.guild.roles, name="常連")
            role3 = discord.utils.get(message.guild.roles, name="金持ち")
            role4 = discord.utils.get(message.guild.roles, name="覚醒者")
            role5 = discord.utils.get(message.guild.roles, name="登頂者")
            role6 = discord.utils.get(message.guild.roles, name="落札王")
            role7 = discord.utils.get(message.guild.roles, name="落札神")
            if newscore >= 100:
                before = role6
                after = role7
                embed = discord.Embed(description=f'**{user.display_name}**がランクアップ！``落札王⇒落札神``',
                                      color=0x3efd73)
                embed.set_author(name=user, icon_url=user.avatar_url, )  # ユーザー名+ID,アバターをセット
                if role7 in user.roles:
                    embed = None
                return before, after, embed
            elif newscore >= 60:
                before = role5
                after = role6
                embed = discord.Embed(description=f'**{user.display_name}**がランクアップ！``登頂者⇒落札王``',
                                      color=0xfb407c)
                embed.set_author(name=user, icon_url=user.avatar_url, )  # ユーザー名+ID,アバターをセット
                if role6 in user.roles:
                    embed = None
                return before, after, embed
            elif newscore >= 30:
                before = role4
                after = role5
                embed = discord.Embed(description=f'**{user.display_name}**がランクアップ！``覚醒者⇒登頂者``',
                                      color=0xf3f915)
                embed.set_author(name=user, icon_url=user.avatar_url, )  # ユーザー名+ID,アバターをセット
                if role5 in user.roles:
                    embed = None
                return before, after, embed
            elif newscore >= 10:
                before = role3
                after = role4
                embed = discord.Embed(description=f'**{user.display_name}**がランクアップ！``金持ち⇒覚醒者``',
                                      color=0xe15555)
                embed.set_author(name=user, icon_url=user.avatar_url, )  # ユーザー名+ID,アバターをセット
                if role4 in user.roles:
                    embed = None
                return before, after, embed
            elif newscore >= 5:
                if role3 in user.roles:
                    pass
                before = role2
                after = role3
                embed = discord.Embed(description=f'**{user.display_name}**がランクアップ！``常連⇒金持ち``',
                                      color=0xc60000)
                embed.set_author(name=user, icon_url=user.avatar_url, )  # ユーザー名+ID,アバターをセット
                if role3 in user.roles:
                    embed = None
                return before, after, embed
            elif newscore >= 3:
                before = role1
                after = role2
                embed = discord.Embed(description=f'**{user.display_name}**がランクアップ！``新星⇒常連``',
                                      color=0xed8f10)
                embed.set_author(name=user, icon_url=user.avatar_url, )  # ユーザー名+ID,アバターをセット
                if role2 in user.roles:
                    embed = None
                return before, after, embed
            elif newscore >= 1:
                before = role1
                after = role1
                embed = discord.Embed(description=f'**{user.display_name}**がランクアップ！``落札初心者⇒新星``',
                                      color=0xeacf13)
                embed.set_author(name=user, icon_url=user.avatar_url, )  # ユーザー名+ID,アバターをセット
                if role1 in user.roles:
                    embed = None
                return before, after, embed

        def createRanckingEmbed():
            # scoreを抜き出したメンバーのIDのリストで一個一個keyとして突っ込んだ後、それに対応する落札ポイントを引っ張って突っ込む

            # 落札ポイントを入れるリスト
            scoreList = []

            # メンバーを入れるリスト
            memberList = []

            # 上記2つをまとめて辞書型にする
            bidscoreDict = {}

            botCount = 0
            r = redis.from_url(os.environ['REDIS_URL'])  # os.environで格納された環境変数を引っ張ってくる
            for member in range(client.get_guild(558125111081697300).member_count):
                if client.get_guild(558125111081697300).members[member].bot:
                    botCount += 1

                memberList.append(client.get_guild(558125111081697300).members[member].display_name)

                key = f"score-{client.get_guild(558125111081697300).members[member].id}"
                scoreList.append(int(r.get(key) or "0"))

                # メンバー : その人のスコア　で　辞書型結合を行う
                bidscoreDict[memberList[member]] = scoreList[member]

                # 全員分確認終わったら今度は出力
                if member == (client.get_guild(558125111081697300).member_count - 1):
                    description = ""
                    rank = 1
                    # ランキングを出力する。まずは辞書型の落札ポイントを基準として降順ソートする。メンバーをmem,スコアをscoreとする
                    for mem, score in sorted(bidscoreDict.items(), key=lambda x: -x[1]):
                        # 落札ポイント0ptは表示しない
                        if score == 0:
                            continue
                        description += f"{rank}位: {str(mem)} - 落札ポイント -> {str(score)}\n"
                        rank += 1

                    # 表示する
                    d = datetime.now()  # 現在時刻の取得
                    time = d.strftime("%Y/%m/%d %H:%M:%S")
                    embed = Embed(
                        title='**落札ポイントランキング**',
                        description=description,
                        color=0x48d1cc)  # 発言内容をdescriptionにセット
                    embed.set_footer(text=f'UpdateTime：{time}')  # チャンネル名,時刻,鯖のアイコンをセット
                    return embed

        # 落札額ランキングembed作成 複数のembed情報を詰め込んだリストを返す
        def createHighBidRanking():
            i = 0
            r = redis.from_url(os.environ['HEROKU_REDIS_ORANGE_URL'])  # os.environで格納された環境変数を引っ張ってくる
            radis_get_data_list = []

            # データをリストに突っ込む。NoneTypeはifにするとFalseとして解釈されるのを利用する
            # ついでに、ユーザーが存在するかを確かめて、存在しなかったらpass
            while True:
                if r.get(i):
                    if client.get_user(int(r.get(i).decode().split(",")[3])):
                        radis_get_data_list.append(r.get(i).decode().split(","))
                    else:
                        pass
                    i += 1
                else:
                    break

            # 降順でソートする
            radis_get_data_list.sort(key=lambda x: int(x[2]), reverse=True)

            # embed保管リスト
            embed_list = []
            # データ毎に取り出す
            description = ""
            for i in range(len(radis_get_data_list)):
                # 気持ち程度のレイアウト合わせ。1桁と2桁の違い
                if i <= 9:
                    description += " "
                # listの中身は[落札者,落札物,落札額,出品者ID]
                description += f"{i + 1}位: 出品者->{client.get_user(int(radis_get_data_list[i][3])).display_name}\n" \
                               f"  　　出品物->{radis_get_data_list[i][1]}\n" \
                               f"  　　落札額->{siina_check_reverse(int(radis_get_data_list[i][2]))}\n" \
                               f"  　　落札者->{radis_get_data_list[i][0]}\n\n"

                # descriptionの長さが2000を超えるとエラーになる。吐き出してリセット案件
                if len(description) > 1800:
                    embed = discord.Embed(title="**落札額ランキング**", description=description, color=0xddc7ff)
                    embed_list.append(embed)
                    description = ""
                else:
                    pass
                # 何位まで出力するか.
                if i >= 39:
                    break
            # embed儀式
            embed = discord.Embed(description=description, color=0xddc7ff)
            d = datetime.now()  # 現在時刻の取得
            time = d.strftime("%Y/%m/%d %H:%M:%S")
            embed.set_footer(text=f"UpdateTime: {time}")
            embed_list.append(embed)
            return embed_list

        # 椎名[a st + b]がvalueで来ることを想定する
        def siina_check(value):
            try:
                if "st" in value or "ST" in value:
                    if "+" in value:
                        value_new = str(value).replace("椎名", "").replace("st", "").replace("ST", "").replace("個",
                                                                                                             "").split(
                            "+")
                    else:
                        value_new = []
                        value_new.append(
                            str(value).replace("椎名", "").replace("st", "").replace("ST", "").replace("個", ""))
                        value_new.append(0)
                    a = int(value_new[0])
                    b = int(value_new[1])
                    if a * 64 + b <= 0:
                        return 0
                    else:
                        return a * 64 + b
                else:
                    value_new = str(value).replace("椎名", "").replace("st", "").replace("ST", "").replace("個", "")
                    if int(value_new) <= 0:
                        return 0
                    else:
                        return int(value_new)
            except ValueError:
                return 0

        # intがvalueで来ることを想定する
        def siina_check_reverse(value):
            try:
                value2 = int(value)
                if value2 <= 63:
                    return value2
                else:
                    print(value2)
                    i = 0
                    while value2 >= 64:
                        value2 -= 64
                        i += 1
                    j = -64 * i + int(value)
                    if j == 0:
                        return f"椎名{i}st"
                    else:
                        return f"椎名{i}st+{j}個"
            except ValueError:
                return 0

        def operate_user_auction_count(mode, user):
            r = redis.from_url(os.environ['HEROKU_REDIS_BLACK_URL'])
            key = int(user)
            if mode == "g":
                auction_now = int(r.get(key) or 0)
                return int(auction_now)
            if mode == "s+":
                return int(r.get(key) or 0) + 1
            if mode == "s-":
                return int(r.get(key) or 0) - 1

        if message.content == "!show_bid_ranking":
            if discord.utils.get(message.author.roles, name="Administrator"):
                await client.get_channel(705040893593387039).purge(limit=10)
                await asyncio.sleep(0.1)
                embed = createHighBidRanking()
                for i in range(len(embed)):
                    await client.get_channel(705040893593387039).send(embed=embed[i])
            else:
                await message.channel.send("運営以外のコマンド使用は禁止です")

        if message.content.startswith("!tend"):
            # todo ここでは a st + bの形式で来ることを想定している
            msg = f'{message.content}'.replace('!tend ', '')
            tend_price = siina_check(msg)
            if not tend_price == 0:
                r = redis.from_url(os.environ['HEROKU_REDIS_YELLOW_URL'])
                # todo チャンネルIDと入札額を紐づけする。また、bid操作で個々の値に0をセットする。
                # todo startの初期価格未満は弾く。同一人物の2回入札も弾く。
                key = message.channel.id
                before_tend_price = int(r.get(key) or 0)
                if tend_price > before_tend_price:
                    await message.channel.send(f"この入札は以前の入札額より低いです。やり直してください。")
                    return
            else:
                await message.channel.send(f"Error.有効な入札ではありません。\n{message.author.display_name}の入札:{message.content}")

        if message.content.startswith("!set_user_auction_count"):

            # その人が取り扱ってるオークションの個数を指定
            r = redis.from_url(os.environ['HEROKU_REDIS_BLACK_URL'])
            msg = f'{message.content}'.replace('!set_user_auction_count ', '').split(" ")
            key = int(msg[0])
            auction_now = int(msg[1])
            r.set(int(key), auction_now)
            await message.channel.send(f"{client.get_user(int(msg[0])).display_name}さんのオークションの開催個数を**{auction_now}**個にセットしました。")

        if message.content == "!stop_deal":
            if discord.utils.get(message.author.roles, name="Administrator"):
                embed = discord.Embed(
                    description=f"{message.author.display_name}によりこの取引は停止させられました。",
                    color=0xf04747
                )
                await message.channel.send(embed=embed)
                await message.channel.send('--------ｷﾘﾄﾘ線--------')
                Channel = message.channel
                await Channel.edit(name=Channel.name + '☆')
            else:
                await message.channel.send("運営以外のコマンド使用は禁止です")

        if message.content == "!insert_ranking_data":
            def check(m):
                return m.channel == message.channel

            if discord.utils.get(message.author.roles, name="Administrator"):
                await message.channel.send("データを入力してください")
                data = await client.wait_for("message", check=check)
                i = 0
                r = redis.from_url(os.environ['HEROKU_REDIS_ORANGE_URL'])
                while True:
                    # keyに値がない部分まで管理IDを+
                    if r.get(i):
                        i += 1
                    else:
                        key = i
                        break
                r.set(int(key), str(data.content))
                await message.channel.send(f"データ: {data.content}を入力しました。")
            else:
                await message.channel.send("運営以外のコマンド使用は禁止です")

        if message.content == "!star_delete":
            if discord.utils.get(message.author.roles, name="Administrator"):
                embed = discord.Embed(
                    description=f"{message.author.display_name}により☆を強制的に取り外しました。",
                    color=0xf04747
                )
                await message.channel.send(embed=embed)
                await message.channel.edit(name=message.channel.name.split('☆')[0])
            else:
                await message.channel.send("運営以外のコマンド使用は禁止です")

        # カウントしてその数字に対応する役職を付与する
        if message.channel.id == 558265536430211083 and message.content.startswith('!bidscore'):
            CHANNEL_ID = 602197766218973185
            channel = client.get_channel(CHANNEL_ID)
            msg = f'{message.content}'.replace('!bidscore ', '')
            p = re.compile(r'^[0-9]+$')
            if p.fullmatch(msg):
                kazu = int(msg)
                r = redis.from_url(os.environ['REDIS_URL'])  # os.environで格納された環境変数を引っ張ってくる
                key = f"score-{message.author.id}"
                oldscore = int(r.get(key) or "0")
                newscore = oldscore + kazu
                r.set(key, str(newscore))
                embed = discord.Embed(description=f'**{message.author.display_name}**の現在の落札ポイントは**{newscore}**です。',
                                      color=0x9d9d9d)
                embed.set_author(name=message.author, icon_url=message.author.avatar_url, )  # ユーザー名+ID,アバターをセット
                await channel.send(embed=embed)
                before, after, embed = checkRole(newscore, message.author)
                await message.author.remove_roles(before)
                await message.author.add_roles(after)
                if embed is not None:
                    await message.channel.send(embed=embed)
                embed = discord.Embed(description=f'**{message.author.display_name}**に落札ポイントを付与しました。', color=0x9d9d9d)
                embed.set_author(name=message.author, icon_url=message.author.avatar_url, )  # ユーザー名+ID,アバターをセット
                await message.channel.send(embed=embed)
                await asyncio.sleep(0.5)
                # ランキングを出力する
                CHANNEL_ID = 677905288665235475
                channel = client.get_channel(CHANNEL_ID)
                # とりあえず、ランキングチャンネルの中身を消す
                await channel.purge(limit=1)
                await channel.send(embed=createRanckingEmbed())

        # 更新
        if message.content == "!check_role":
            i = 0
            for member in range(client.get_guild(558125111081697300).member_count):
                if client.get_guild(558125111081697300).members[member].bot:
                    pass
                r = redis.from_url(os.environ['REDIS_URL'])  # os.environで格納された環境変数を引っ張ってくる
                key = f"score-{client.get_guild(558125111081697300).members[member].id}"
                score = int(r.get(key) or "0")
                await message.channel.send(client.get_guild(558125111081697300).members[member])
                before, after, embed = checkRole(score, client.get_guild(558125111081697300).members[member])
                await client.get_guild(558125111081697300).members[member].remove_roles(before)
                await client.get_guild(558125111081697300).members[member].add_roles(after)
            await message.channel.send("照会終了")

        # MCID_check
        if message.channel.id == 558278443440275461:
            mcid = f'{message.content}'.replace('\\', '')
            p = re.compile(r'^[a-zA-Z0-9_]+$')
            if p.fullmatch(message.content):
                mcid = str.lower(mcid)
                url = f"https://w4.minecraftserver.jp/player/{mcid}"
                try:
                    res = requests.get(url)
                    res.raise_for_status()
                    soup = bs4.BeautifulSoup(res.text, "html.parser")
                    td = soup.td
                    if f'{mcid}' in f'{td}':
                        # 存在した場合の処理
                        role1 = discord.utils.get(message.guild.roles, name="新人")
                        role2 = discord.utils.get(message.guild.roles, name="MCID報告済み")
                        emoji = ['👍', '🙆']
                        await message.author.remove_roles(role1)
                        await message.author.add_roles(role2)
                        await message.add_reaction(random.choice(emoji))
                        CHANNEL_ID = 591244559019802650
                        channel = client.get_channel(CHANNEL_ID)
                        color = [0x3efd73, 0xfb407c, 0xf3f915, 0xc60000, 0xed8f10, 0xeacf13, 0x9d9d9d, 0xebb652,
                                 0x4259fb,
                                 0x1e90ff]
                        embed = discord.Embed(description=f'{message.author.display_name}のMCIDの報告を確認したよ！',
                                              color=random.choice(color))
                        embed.set_author(name=message.author, icon_url=message.author.avatar_url, )  # ユーザー名+ID,アバターをセット
                        await channel.send(embed=embed)
                    else:
                        embed = discord.Embed(
                            description=f'{message.author} さん。\n入力されたMCIDは実在しないか、又はまだ一度も整地鯖にログインしていません。\n'
                                        f'続けて間違った入力を行うと規定によりBANの対象になることがあります。',
                            color=0xff0000)
                        await message.channel.send(embed=embed)
                except requests.exceptions.HTTPError:
                    await message.channel.send(f'requests.exceptions.HTTPError')
            else:
                embed = discord.Embed(description="MCIDに使用できない文字が含まれています'\n続けて間違った入力を行うと規定によりBANの対象になることがあります。",
                                      color=0xff0000)
                await message.channel.send(embed=embed)

        auction_category_ids = {c.id for c in message.guild.categories if c.name.startswith('>')}
        normal_category_ids = {this.id for this in message.guild.categories if this.name.startswith('*')}
        siina_category_ids = {siina.id for siina in message.guild.categories if "椎名" in siina.name}

        if message.channel.category_id in auction_category_ids:  # オークション会場で動かすコマンド(カテゴリ名の最初に>を入れているかで判断)

            if message.content == "!start":
                # 2つ行ってる場合はreturn
                user = message.author.id
                if operate_user_auction_count("g", user) >= 2:
                    description = "貴方はすでにオークションを2つ以上行っているためこれ以上オークションを始められません。\n" \
                                  "行っているオークションが2つ未満になってから再度行ってください。"
                    await message.channel.send(embed=discord.Embed(description=description, color=0xf04747))
                    await message.channel.send("--------ｷﾘﾄﾘ線--------")
                    return

                tmprole = discord.utils.get(message.guild.roles, name="現在商品登録中")
                await message.author.add_roles(tmprole)
                auction_registration_user_id = message.author.id
                await asyncio.sleep(0.3)
                if discord.utils.get(message.author.roles, name="現在商品登録中"):

                    def check(m):
                        if m.author.bot:
                            return
                        elif m.author.id == auction_registration_user_id:
                            return m.channel == message.channel

                    def check2(forthUserInput):
                        return forthUserInput.channel == message.channel and re.match(
                            r'[0-9]{2}/[0-9]{2}-[0-9]{2}:[0-9]{2}',
                            forthUserInput.content)

                    embed = discord.Embed(
                        description="出品するものを入力してください。",
                        color=0xffaf60)
                    await message.channel.send(embed=embed)
                    userInput1 = await client.wait_for('message', check=check)
                    embed = discord.Embed(description="開始価格を入力してください。(椎名か、ガチャ券かなどを明記して書くこと)", color=0xffaf60)
                    await message.channel.send(embed=embed)
                    userInput2 = await client.wait_for('message', check=check)
                    embed = discord.Embed(description="即決価格を入力してください。", color=0xffaf60)
                    await message.channel.send(embed=embed)
                    userInput3 = await client.wait_for('message', check=check)
                    embed = discord.Embed(
                        description="オークション終了日時を入力してください。\n**注意！**時間の書式に注意してください！\n"
                                    "例　5月14日の午後8時に終了したい場合：\n**05/14-20:00**と入力してください。\n"
                                    "この形でない場合認識されません！\n**間違えて打ってしまった場合その部分は必ず削除してください。**",
                        color=0xffaf60)
                    await message.channel.send(embed=embed)
                    userInput4 = await client.wait_for('message', check=check2)
                    embed = discord.Embed(
                        description="その他、即決特典などありましたらお書きください。\n長い場合、改行などをして**１回の送信**で書いてください。\n"
                                    "何も無ければ「なし」で構いません。",
                        color=0xffaf60)
                    await message.channel.send(embed=embed)
                    userInput5 = await client.wait_for('message', check=check)
                    kazu = 11
                    await message.channel.purge(limit=kazu)
                    embed = discord.Embed(title="これで始めます。よろしいですか？YES/NOで答えてください。(小文字でもOK。NOの場合初めからやり直してください。)",
                                          color=0xffaf60)
                    embed.add_field(name="出品者", value=f'\n\n{message.author.display_name}', inline=True)
                    embed.add_field(name="出品物", value=f'\n\n{userInput1.content}', inline=True)
                    embed.add_field(name="開始価格", value=f'\n\n{userInput2.content}', inline=False)
                    embed.add_field(name="即決価格", value=f'\n\n{userInput3.content}', inline=False)
                    embed.add_field(name="終了日時", value=f'\n\n{userInput4.content}', inline=True)
                    embed.add_field(name="特記事項", value=f'\n\n{userInput5.content}', inline=True)
                    await message.channel.send(embed=embed)
                    userInput6 = await client.wait_for('message', check=check)
                    if userInput6.content == "YES" or userInput6.content == "yes" or userInput6.content == "いぇｓ" or userInput6.content == "いぇs":
                        kazu = 2
                        await message.channel.purge(limit=kazu)
                        await asyncio.sleep(0.3)
                        embed = discord.Embed(title="オークション内容", color=0xffaf60)
                        embed.add_field(name="出品者", value=f'\n\n{message.author.display_name}', inline=True)
                        embed.add_field(name="出品物", value=f'\n\n{userInput1.content}', inline=True)
                        embed.add_field(name="開始価格", value=f'\n\n{userInput2.content}', inline=False)
                        embed.add_field(name="即決価格", value=f'\n\n{userInput3.content}', inline=False)
                        embed.add_field(name="終了日時", value=f'\n\n{userInput4.content}', inline=True)
                        embed.add_field(name="特記事項", value=f'\n\n{userInput5.content}', inline=True)
                        await message.channel.send(embed=embed)
                        await message.channel.send("<:siina:558251559394213888>オークションを開始します<:siina:558251559394213888>")
                        Channel = message.channel
                        await Channel.edit(name=Channel.name.split('☆')[0])
                        await message.author.remove_roles(tmprole)
                        # ここで、その人が行っているオークションの個数を増やす
                        user = message.author.id
                        r = redis.from_url(os.environ['HEROKU_REDIS_BLACK_URL'])
                        r.set(int(message.author.id), operate_user_auction_count("s+", user))
                    else:
                        kazu = 2
                        await message.channel.purge(limit=kazu)
                        await message.channel.send("初めからやり直してください。\n--------ｷﾘﾄﾘ線--------")
                        await message.author.remove_roles(tmprole)
                else:
                    await message.channel.send("RoleError.運営を呼んでください")

            if message.content == '!bid':
                tmprole = discord.utils.get(message.guild.roles, name="現在商品登録中")
                await message.author.add_roles(tmprole)
                await asyncio.sleep(0.3)
                if discord.utils.get(message.author.roles, name="現在商品登録中"):
                    if '☆' in message.channel.name:
                        embed = discord.Embed(
                            description=f'{message.author.display_name}さん。このチャンネルではオークションは行われていません',
                            color=0xff0000)
                        await message.channel.send(embed=embed)
                    else:
                        auction_finish_user_id = message.author.id

                        def check(m):
                            if m.author.bot:
                                return
                            elif m.author.id == auction_finish_user_id:
                                return m.channel == message.channel and "," not in m.content

                        def check_siina_style(m):
                            if m.author.bot:
                                return
                            elif "椎名" in m.content and "sT" not in m.content and "St" not in m.content:
                                return m.channel == message.channel

                        kazu = 6
                        embed = discord.Embed(
                            description="注:**全体の入力を通して[,]の記号は使用できません。何か代替の記号をお使いください。**\n\n"
                                        "出品した品物名を書いてください。",
                            color=0xffaf60)
                        await message.channel.send(embed=embed)
                        userInput1 = await client.wait_for('message', check=check)
                        embed = discord.Embed(description="落札者のユーザーネームを書いてください。", color=0xffaf60)
                        await message.channel.send(embed=embed)
                        userInput2 = await client.wait_for('message', check=check)
                        description = "落札価格を入力してください。\n"
                        if message.channel.category_id in siina_category_ids:
                            description += "以下のような形式以外は認識されません。(個はなくてもOK): **椎名○○st+△(個)(椎名○○(個)も可)\n" \
                                           "ex: 椎名5st+16個 椎名336個"
                        embed = discord.Embed(description=description, color=0xffaf60)
                        await message.channel.send(embed=embed)
                        siina_amount = -1
                        if message.channel.category_id in siina_category_ids:
                            frag = True
                            while frag:
                                userInput3 = await client.wait_for('message', check=check_siina_style)
                                siina_amount = siina_check(userInput3.content)
                                if siina_amount == 0:
                                    await message.channel.send("値が不正です。椎名○○st+△(個)の○と△には整数以外は入りません。再度入力してください。")
                                    kazu += 2
                                else:
                                    frag = False
                        else:
                            userInput3 = await client.wait_for('message', check=check)
                        await message.channel.purge(limit=kazu)
                        embed = discord.Embed(description="オークション終了報告を受け付けました。", color=0xffaf60)
                        await message.channel.send(embed=embed)

                        # ランキング送信
                        if message.channel.category_id in siina_category_ids:
                            r = redis.from_url(os.environ['HEROKU_REDIS_ORANGE_URL'])  # os.environで格納された環境変数を引っ張ってくる
                            # 設計図: unique_idの初めは1,無ければそこに値を代入
                            i = 0
                            while True:
                                # keyに値がない部分まで管理IDを+
                                if r.get(i):
                                    i += 1
                                else:
                                    key = i
                                    break
                            # 管理IDに紐づけて記録するデータの内容は[落札者,落札したもの,落札額,userid]がString型で入る.splitでlistにすること
                            redis_set_str = f"{userInput2.content},{userInput1.content},{siina_amount},{message.author.id}"
                            r.set(int(key), str(redis_set_str))
                            await client.get_channel(705040893593387039).purge(limit=10)
                            await asyncio.sleep(0.1)
                            embed = createHighBidRanking()
                            for i in range(len(embed)):
                                await client.get_channel(705040893593387039).send(embed=embed[i])

                        # 記録送信
                        CHANNEL_ID = 558132754953273355
                        channel = client.get_channel(CHANNEL_ID)
                        d = datetime.now()  # 現在時刻の取得
                        time = d.strftime("%Y/%m/%d")
                        embed = discord.Embed(title="オークション取引結果", color=0x36a64f)
                        embed.add_field(name="落札日", value=f'\n\n{time}', inline=False)
                        embed.add_field(name="出品者", value=f'\n\n{message.author.display_name}', inline=False)
                        embed.add_field(name="品物", value=f'\n\n{userInput1.content}', inline=False)
                        embed.add_field(name="落札者", value=f'\n\n{userInput2.content}', inline=False)
                        embed.add_field(name="落札価格", value=f'\n\n{userInput3.content}', inline=False)
                        embed.add_field(name="チャンネル名", value=f'\n\n{message.channel}', inline=False)
                        await channel.send(embed=embed)
                        await message.channel.send('--------ｷﾘﾄﾘ線--------')
                        await asyncio.sleep(0.3)
                        await message.channel.edit(name=message.channel.name + '☆')
                        await message.author.remove_roles(tmprole)
                        # ここで、その人が行っているオークションの個数を減らす
                        user = message.author.id
                        r = redis.from_url(os.environ['HEROKU_REDIS_BLACK_URL'])
                        r.set(int(message.author.id), operate_user_auction_count("s-", user))
                else:
                    await message.channel.send("RoleError.運営を呼んでください")
                    await message.author.remove_roles(tmprole)

        elif message.channel.category_id in normal_category_ids:

            if message.content == "!start":
                # 2つ行ってる場合はreturn
                user = message.author.id
                if operate_user_auction_count("g", user) >= 2:
                    description = "貴方はすでにオークションを2つ以上行っているためこれ以上オークションを始められません。\n" \
                                  "行っているオークションが2つ未満になってから再度行ってください。"
                    await message.channel.send(embed=discord.Embed(description=description, color=0xf04747))
                    await message.channel.send("--------ｷﾘﾄﾘ線--------")
                    return

                tmprole = discord.utils.get(message.guild.roles, name="現在商品登録中")
                await message.author.add_roles(tmprole)
                await asyncio.sleep(0.3)
                if discord.utils.get(message.author.roles, name="現在商品登録中"):

                    def check(m):
                        if m.author.bot:
                            return
                        else:
                            return m.channel == message.channel

                    def check2(forthUserInput):
                        return forthUserInput.channel == message.channel and re.match(
                            r'[0-9]{2}/[0-9]{2}-[0-9]{2}:[0-9]{2}',
                            forthUserInput.content)

                    embed = discord.Embed(
                        description="出品するものを入力してください。",
                        color=0xffaf60)
                    await message.channel.send(embed=embed)

                    userInput1 = await client.wait_for('message', check=check)
                    embed = discord.Embed(description="希望価格を入力してください。(椎名か、ガチャ券かなどを明記して書くこと)", color=0xffaf60)
                    await message.channel.send(embed=embed)

                    userInput2 = await client.wait_for('message', check=check)
                    embed = discord.Embed(
                        description="オークション終了日時を入力してください。\n**注意！**時間の書式に注意してください！\n"
                                    "例　5月14日の午後8時に終了したい場合：\n**05/14-20:00**と入力してください。\nこの形でない場合認識されません！\n"
                                    "**間違えて打ってしまった場合その部分は必ず削除してください。**",
                        color=0xffaf60)
                    await message.channel.send(embed=embed)

                    userInput3 = await client.wait_for('message', check=check2)
                    embed = discord.Embed(
                        description="その他、即決特典などありましたらお書きください。\n長い場合、改行などをして**１回の送信**で書いてください。\n"
                                    "何も無ければ「なし」で構いません。",
                        color=0xffaf60)
                    await message.channel.send(embed=embed)

                    userInput4 = await client.wait_for('message', check=check)
                    kazu = 11
                    await message.channel.purge(limit=kazu)

                    embed = discord.Embed(title="これで始めます。よろしいですか？YES/NOで答えてください。(小文字でもOK。NOの場合初めからやり直してください。)",
                                          color=0xffaf60)
                    embed.add_field(name="出品者", value=f'\n\n{message.author.display_name}', inline=True)
                    embed.add_field(name="出品物", value=f'\n\n{userInput1.content}', inline=False)
                    embed.add_field(name="希望価格", value=f'\n\n{userInput2.content}', inline=True)
                    embed.add_field(name="終了日時", value=f'\n\n{userInput3.content}', inline=True)
                    embed.add_field(name="特記事項", value=f'\n\n{userInput4.content}', inline=False)
                    await message.channel.send(embed=embed)
                    userInput6 = await client.wait_for('message', check=check)
                    # 出来ればYESとyesはlowerにするべきでは
                    if userInput6.content == "YES" or userInput6.content == "yes" or userInput6.content == "いぇｓ" or userInput6.content == "いぇs":
                        kazu = 2
                        await message.channel.purge(limit=kazu)
                        await asyncio.sleep(0.3)
                        embed = discord.Embed(title="オークション内容", color=0xffaf60)
                        embed.add_field(name="出品者", value=f'\n\n{message.author.display_name}', inline=True)
                        embed.add_field(name="出品物", value=f'\n\n{userInput1.content}', inline=False)
                        embed.add_field(name="希望価格", value=f'\n\n{userInput2.content}', inline=True)
                        embed.add_field(name="終了日時", value=f'\n\n{userInput3.content}', inline=True)
                        embed.add_field(name="特記事項", value=f'\n\n{userInput4.content}', inline=False)
                        await message.channel.send(embed=embed)
                        await message.channel.send(
                            "<:shiina_balance:558175954686705664>取引を開始します<:shiina_balance:558175954686705664>")
                        Channel = message.channel
                        await Channel.edit(name=Channel.name.split('☆')[0])
                        await message.author.remove_roles(tmprole)
                        # ここで、その人が行っているオークションの個数を増やす
                        user = message.author.id
                        r = redis.from_url(os.environ['HEROKU_REDIS_BLACK_URL'])
                        r.set(int(message.author.id), operate_user_auction_count("s+", user))
                    else:
                        kazu = 2
                        await message.channel.purge(limit=kazu)
                        await message.channel.send("初めからやり直してください。\n--------ｷﾘﾄﾘ線--------")
                        await message.author.remove_roles(tmprole)

            if message.content == '!end':
                await message.channel.send('--------ｷﾘﾄﾘ線--------')
                Channel = message.channel
                await Channel.edit(name=Channel.name + '☆')
                # ここで、その人が行っているオークションの個数を減らす
                user = message.author.id
                r = redis.from_url(os.environ['HEROKU_REDIS_BLACK_URL'])
                r.set(int(message.author.id), operate_user_auction_count("s-", user))

            if message.content == "!bid":
                description = "ここは通常取引チャンネルです。終了報告は``!end``をお使いください。"
                embed = discord.Embed(description=description, color=0x4259fb)
                await message.channel.send(embed=embed)

        else:
            if message.content == '!version':
                embed = discord.Embed(description="現在のバージョンは**5.0.0**です\nNow version **5.0.0** working.",
                                      color=0x4259fb)
                await message.channel.send(embed=embed)

            if message.content == '!invite':
                await message.channel.send('招待用URL:https://discord.gg/Syp85R4')

        # メッセージ削除用
        if message.content.startswith('!del'):
            if discord.utils.get(message.author.roles, name="Administrator"):
                msg = f'{message.content}'.replace('!del ', '')
                p = re.compile(r'^[0-9]+$')
                if p.fullmatch(msg):
                    kazu = int(msg)
                    await message.channel.purge(limit=kazu + 1)

        # 引用機能
        if "https://discordapp.com/channels/558125111081697300/" in message.content:
            for url in message.content.split('https://discordapp.com/channels/558125111081697300/')[1:]:
                try:
                    channel_id = int(url[0:18])
                    message_id = int(url[19:37])
                    ch = message.guild.get_channel(int(channel_id))
                    msg = await ch.fetch_message(int(message_id))

                    def quote_reaction(msg, embed):
                        if msg.reactions:
                            reaction_send = ''
                            for reaction in msg.reactions:
                                emoji = reaction.emoji
                                count = str(reaction.count)
                                reaction_send = f'{reaction_send}{emoji}{count} '
                            embed.add_field(name='reaction', value=reaction_send, inline=False)
                        return embed

                    if msg.embeds or msg.content or msg.attachments:
                        embed = Embed(description=msg.content, timestamp=msg.created_at)
                        embed.set_author(name=msg.author, icon_url=msg.author.avatar_url)
                        embed.set_footer(text=msg.channel.name, icon_url=msg.guild.icon_url)
                        if msg.attachments:
                            embed.set_image(url=msg.attachments[0].url)
                        embed = quote_reaction(msg, embed)
                        if msg.content or msg.attachments:
                            await message.channel.send(embed=embed)
                        if len(msg.attachments) >= 2:
                            for attachment in msg.attachments[1:]:
                                embed = Embed().set_image(url=attachment.url)
                                await message.channel.send(embed=embed)
                        for embed in msg.embeds:
                            embed = quote_reaction(msg, embed)
                            await message.channel.send(embed=embed)
                    else:
                        await message.channel.send('メッセージIDは存在しますが、内容がありません')
                except discord.errors.NotFound:
                    await message.channel.send("指定したメッセージが見つかりません")

        if message.content == "!checkAllUserID":
            if discord.utils.get(message.author.roles, name="Administrator"):
                CHANNEL_ID = 642052474672250880
                channel = client.get_channel(CHANNEL_ID)
                botCount = 0
                for member in range(client.get_guild(558125111081697300).member_count):
                    if client.get_guild(558125111081697300).members[member].bot:
                        botCount += 1
                        continue
                    await channel.send(
                        f"{client.get_guild(558125111081697300).members[member].id} : "
                        f"{client.get_guild(558125111081697300).members[member].display_name}")
                    if member == (client.get_guild(558125111081697300).member_count - 1):
                        embed = discord.Embed(description=f"このサーバーの全メンバーのユーザーIDの照会が終わりました。 現在人数:{member - botCount + 1}"
                                              , color=0x1e90ff)
                        await channel.send(embed=embed)
                        await channel.send("--------ｷﾘﾄﾘ線--------")

        if message.content == "!bidscoreRanking":
            if discord.utils.get(message.author.roles, name="Administrator"):
                CHANNEL_ID = 677905288665235475
                channel = client.get_channel(CHANNEL_ID)
                # とりあえず、ランキングチャンネルの中身を消す
                await channel.purge(limit=1)
                await channel.send(embed=createRanckingEmbed())
                await asyncio.sleep(0.3)
                embed = discord.Embed(
                    description=f"このサーバーの全メンバーの落札ポイントの照会が終わりました。"
                                f"\nランキングを出力しました。 ",
                    color=0x1e90ff
                )
                await message.channel.send(embed=embed)

        if message.content.startswith('!bidscoreGS'):
            if discord.utils.get(message.author.roles, name="Administrator"):
                r = redis.from_url(os.environ['REDIS_URL'])  # os.environで格納された環境変数を引っ張ってくる
                if message.content.split(" ")[1] == "get":
                    getScore = int(r.get(f"score-{message.content.split(' ')[2]}" or "0"))
                    embed = discord.Embed(description=f"ユーザーID：{message.content.split(' ')[2]}の落札ポイントは{getScore}です。",
                                          color=0x1e90ff)
                    await message.channel.send(embed=embed)
                elif message.content.split(" ")[1] == "set":
                    r.set(f"score-{message.content.split(' ')[2]}", str(message.content.split(' ')[3]))
                    embed = discord.Embed(
                        description=f"{message.author.display_name}により、ユーザー名：{client.get_user(int(message.content.split(' ')[2])).display_name}"
                                    f"の落札ポイントを{message.content.split(' ')[3]}にセットしました。",
                        color=0x1e90ff)
                    await message.channel.send(embed=embed)
                    CHANNEL_ID = 677905288665235475
                    channel = client.get_channel(CHANNEL_ID)
                    # とりあえず、ランキングチャンネルの中身を消す
                    await channel.purge(limit=1)
                    await channel.send(embed=createRanckingEmbed())
                    CHANNEL_ID = 602197766218973185
                    channel = client.get_channel(CHANNEL_ID)
                    embed = discord.Embed(
                        description=f"{message.author.display_name}により、{client.get_user(int(message.content.split(' ')[2])).display_name}"
                                    f"の落札ポイントが{message.content.split(' ')[3]}にセットされました。",
                        color=0xf04747
                    )
                    await channel.send(embed=embed)
        if message.content.startswith("!help"):
            description = "<:shiina_balance:558175954686705664>!start\n\n"
            description += "オークションを始めるためのコマンドです。オークションチャンネルでのみ使用可能です。\n"
            description += "-------\n"
            description += "<:siina:558251559394213888>!bid\n\n"
            description += "オークションが終わったときにオークション内容を報告するためのコマンドです。\n"
            description += "ここで報告した内容は <#558132754953273355> に表示されます\n"
            description += "-------\n"
            description += "<:shiina_balance:558175954686705664>!end\n\n"
            description += "取引を終了するためのコマンドです。\n"
            description += "-------\n"
            description += "<:siina:558251559394213888>!bidscore 申請する落札ポイント\n\n"
            description += "落札ポイントを申請します。 <#558265536430211083> に入力すると申請できます。\n"
            description += "<#602197766218973185> に現在の落札ポイントが通知されます。\n"
            description += "<#677905288665235475> に現在の落札ポイントのランキングが表示されます。\n\n"
            description += "(例)!bidscore 2 {これで、自分の落札ポイントが2ポイント加算される。}\n"
            description += "-------\n"
            description += "<:shiina_balance:558175954686705664>!version\n\n"
            description += "現在のBotのバージョンを表示します。\n"
            description += "-------\n"
            description += "<:siina:558251559394213888>!help\n\n"
            description += "このBotのヘルプを表示します。\n"
            description += "-------\n"
            embed = discord.Embed(description=description, color=0x66cdaa)
            await message.channel.send(embed=embed)

    except:
        error_message = f'```{traceback.format_exc()}```'
        ch = message.guild.get_channel(628807266753183754)
        d = datetime.now()  # 現在時刻の取得
        time = d.strftime("%Y/%m/%d %H:%M:%S")
        embed = Embed(title='Error_log', description=error_message, color=0xf04747)
        embed.set_footer(text=f'channel:{message.channel}\ntime:{time}\nuser:{message.author.display_name}')
        await ch.send(embed=embed)


client.run("NTUwNjQyNTQ0MjMzNDE0NjU3.XSrHdg.amSg0hQUvNMAPwCjQiuklJRuXYw")

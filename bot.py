# coding=utf-8
import asyncio
import json
import random
import os
import traceback
from datetime import datetime

import bs4
import discord
import psycopg2
import requests
from discord import Embed
from discord.ext import commands

SQLpath = os.environ["DATABASE_URL"]
db = psycopg2.connect(SQLpath)  # sqlに接続
cur = db.cursor()  # なんか操作する時に使うやつ


class KGX(commands.Bot):
    def __init__(self, prefix):
        super().__init__(command_prefix=prefix)

        description = "<:shiina_balance:558175954686705664>!start\n\n" \
                      "オークションを始めるためのコマンドです。オークションチャンネルでのみ使用可能です。\n\n" \
                      "-------\n" \
                      "<:siina:558251559394213888>!bid\n\n" \
                      "オークションが終わったときにオークション内容を報告するためのコマンドです。\n" \
                      "ここで報告した内容は <#558132754953273355> に表示されます\n\n" \
                      "-------\n" \
                      "<:shiina_balance:558175954686705664>!end\n\n" \
                      "取引を終了するためのコマンドです。\n\n" \
                      "-------\n" \
                      "<:siina:558251559394213888>!bidscore 申請する落札ポイント\n\n" \
                      "落札ポイントを申請します。 <#558265536430211083> に入力すると申請できます。\n" \
                      "<#602197766218973185> に現在の落札ポイントが通知されます。\n" \
                      "<#677905288665235475> に現在の落札ポイントのランキングが表示されます。\n\n" \
                      "(例)!bidscore 2 {これで、自分の落札ポイントが2ポイント加算される。}\n\n" \
                      "-------\n" \
                      "<:shiina_balance:558175954686705664>!version\n\n" \
                      "現在のBotのバージョンを表示します。\n\n" \
                      "-------\n" \
                      "<:siina:558251559394213888>!help\n\n" \
                      "このBotのヘルプを表示します。\n\n" \
                      "-------\n" \
                      "**ここから以下は運営専用**\n--------\n" \
                      "<:shiina_balance:558175954686705664>!del 消去するメッセージの数(int)\n\n" \
                      "メッセージを指定した数、コマンドを打ったチャンネルの最新のメッセージから消します。\n\n" \
                      "-------\n" \
                      "<:siina:558251559394213888>!check_all_user_ID\n\n" \
                      "<#642052474672250880> に、現在このサーバーにいるメンバーのニックネームとユーザーIDをセットで照会します。\n\n" \
                      "-------\n" \
                      "<:shiina_balance:558175954686705664>!bidscoreGS モード ユーザーID 落札ポイント(setモードのみ)\n\n" \
                      "特定の人の落札ポイントを調べたり、変更するために使用します。\n\n" \
                      "<mode:GET>　getモードでは、特定の人の落札ポイントを調べられます。\nコマンドは以下のように使用します。\n\n" \
                      "(例)!bidscoreGS get 251365193127297024\n{これで、EternalHorizonの落札ポイントがわかる}\n\n" \
                      "<mode:SET>　setモードでは、特定の人の落札ポイントを変更できます。\nコマンドは以下のように使用します。\n\n" \
                      "(例)!bidscore_gs set 251365193127297024 10\n{これで、EternalHorizonの落札ポイントが10ポイントに変更される。}\n\n" \
                      "-------\n" \
                      "<:siina:558251559394213888>!bidscore_ranking\n\n" \
                      "<#677905288665235475>を更新します\n\n" \
                      "-------\n" \
                      "<:shiina_balance:558175954686705664>!stop_deal\n\n" \
                      "問答無用で取引を停止します。オークションでも通常取引でも適用されます。\n\n" \
                      "-------\n" \
                      "<:siina:558251559394213888>!check_role\n\n" \
                      "全員の役職が落札ポイントと正しいものになってるかを照合します。\n\n" \
                      "-------\n" \
                      "<:shiina_balance:558175954686705664>!insert_ranking_data\n\n" \
                      "ランキングデータ送信用。落札者,落札物,落札金額,出品者ID\n\n" \
                      "-------\n" \
                      "<:siina:558251559394213888>!set_user_auction_count USER_ID 開催個数\n\n" \
                      "そのユーザーの現在のオークションの開催個数を指定します。\n\n" \
                      "-------\n"
        self.embed = discord.Embed(description=description, color=0x66cdaa)

        self.cur = cur

        self.remove_command('help')  # デフォルトのヘルプコマンドを除外
        for cog in os.listdir(f"./cogs"):  # cogの読み込み
            if cog.endswith(".py"):
                try:
                    self.load_extension(f"cogs.{cog[:-3]}")
                except Exception:
                    traceback.print_exc()

    async def on_ready(self):
        color = [0x126132, 0x82fc74, 0xfea283, 0x009497, 0x08fad4, 0x6ed843, 0x8005c0]
        await self.get_channel(678083611697872910).purge(limit=1)
        await self.get_channel(678083611697872910).send(embed=self.embed)
        await self.get_channel(722092542249795679).send(
            embed=discord.Embed(description="起動しました。", color=color[random.randint(0, 6)]))

    async def on_guild_channel_create(self, channel):
        if ">" not in channel.category.name and "*" not in channel.category.name:
            return
        if "☆" in channel.name:
            return
        try:
            await asyncio.wait_for(channel.edit(name=f"{channel.name}☆"), timeout=3.0)
        except asyncio.TimeoutError:
            return

    async def on_command_error(self, ctx, error):  # すべてのコマンドで発生したエラーを拾う
        if isinstance(error, commands.CommandInvokeError):  # コマンド実行時にエラーが発生したら
            orig_error = getattr(error, "original", error)
            error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
            error_message = f'```{error_msg}```'
            ch = ctx.guild.get_channel(628807266753183754)
            d = datetime.now()  # 現在時刻の取得
            time = d.strftime("%Y/%m/%d %H:%M:%S")
            embed = Embed(title='Error_log', description=error_message, color=0xf04747)
            embed.set_footer(text=f'channel:{ctx.channel}\ntime:{time}\nuser:{ctx.author.display_name}')
            await ch.send(embed=embed)

    @staticmethod
    def check_role(new_score, user, ctx):
        role1 = discord.utils.get(ctx.guild.roles, name="新星")
        role2 = discord.utils.get(ctx.guild.roles, name="常連")
        role3 = discord.utils.get(ctx.guild.roles, name="金持ち")
        role4 = discord.utils.get(ctx.guild.roles, name="覚醒者")
        role5 = discord.utils.get(ctx.guild.roles, name="登頂者")
        role6 = discord.utils.get(ctx.guild.roles, name="落札王")
        role7 = discord.utils.get(ctx.guild.roles, name="落札神")
        if new_score >= 100:
            before = role6
            after = role7
            embed = discord.Embed(description=f'**{user.display_name}**がランクアップ！``落札王⇒落札神``',
                                  color=0x3efd73)
            embed.set_author(name=user, icon_url=user.avatar_url, )  # ユーザー名+ID,アバターをセット
            if role7 in user.roles:
                embed = None
            return before, after, embed
        elif new_score >= 60:
            before = role5
            after = role6
            embed = discord.Embed(description=f'**{user.display_name}**がランクアップ！``登頂者⇒落札王``',
                                  color=0xfb407c)
            embed.set_author(name=user, icon_url=user.avatar_url, )  # ユーザー名+ID,アバターをセット
            if role6 in user.roles:
                embed = None
            return before, after, embed
        elif new_score >= 30:
            before = role4
            after = role5
            embed = discord.Embed(description=f'**{user.display_name}**がランクアップ！``覚醒者⇒登頂者``',
                                  color=0xf3f915)
            embed.set_author(name=user, icon_url=user.avatar_url, )  # ユーザー名+ID,アバターをセット
            if role5 in user.roles:
                embed = None
            return before, after, embed
        elif new_score >= 10:
            before = role3
            after = role4
            embed = discord.Embed(description=f'**{user.display_name}**がランクアップ！``金持ち⇒覚醒者``',
                                  color=0xe15555)
            embed.set_author(name=user, icon_url=user.avatar_url, )  # ユーザー名+ID,アバターをセット
            if role4 in user.roles:
                embed = None
            return before, after, embed
        elif new_score >= 5:
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
        elif new_score >= 3:
            before = role1
            after = role2
            embed = discord.Embed(description=f'**{user.display_name}**がランクアップ！``新星⇒常連``',
                                  color=0xed8f10)
            embed.set_author(name=user, icon_url=user.avatar_url, )  # ユーザー名+ID,アバターをセット
            if role2 in user.roles:
                embed = None
            return before, after, embed
        elif new_score >= 1:
            before = role1
            after = role1
            embed = discord.Embed(description=f'**{user.display_name}**がランクアップ！``落札初心者⇒新星``',
                                  color=0xeacf13)
            embed.set_author(name=user, icon_url=user.avatar_url, )  # ユーザー名+ID,アバターをセット
            if role1 in user.roles:
                embed = None
            return before, after, embed

    def create_ranking_embed(self):
        # user_dataテーブルには「0:ユーザーID bigint, 1:落札ポイント smallint, 2:警告レベル smallint」で格納されているのでこれを全部、落札ポイント降順になるように出す
        cur.execute("SELECT * FROM user_data ORDER BY bid_score desc;")
        data = cur.fetchall()

        # ランキングを出力する。まずは辞書型の落札ポイントを基準として降順ソートする。メンバーをmem,スコアをscoreとする
        rank = 1
        description = ""
        for i in range(len(data)):
            # 落札ポイント0ptは表示しない
            if data[i][1] == 0:
                continue
            elif self.get_user(data[i][0]):
                description += f"{rank}位: {str(self.get_user(data[i][0]).display_name)} - 落札ポイント -> {str(data[i][1])}\n"
                rank += 1
            else:
                continue

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
    @staticmethod
    def create_high_bid_ranking():
        # bid_rankingテーブルには「0:落札者の名前 text, 1:落札物 text, 2:落札額 bigint, 3:出品者の名前 text」で格納されているのでこれを全部、落札額降順になるように出す
        cur.execute("SELECT * FROM bid_ranking ORDER BY bid_price desc;")
        data = cur.fetchall()

        # embed保管リスト
        embed_list = []
        # データ毎に取り出す
        description = ""

        for i in range(len(data)):
            # 気持ち程度のレイアウト合わせ。1桁と2桁の違い
            if i <= 9:
                description += " "
            # listの中身は[落札者,落札物,落札額,出品者ID]
            description += f"{i + 1}位: 出品者->{data[i][3]}\n" \
                           f"  　　出品物->{data[i][1]}\n" \
                           f"  　　落札額->椎名{bot.stack_check_reverse(int(data[i][2]))}\n" \
                           f"  　　落札者->{data[i][0]}\n\n"

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

        # 表示する
        embed = discord.Embed(description=description, color=0xddc7ff)
        d = datetime.now()  # 現在時刻の取得
        time = d.strftime("%Y/%m/%d %H:%M:%S")
        embed.set_footer(text=f"UpdateTime: {time}")
        embed_list.append(embed)
        return embed_list

    # [a lc + b st + c]がvalueで来ることを想定する(関数使用前に文の構造確認を取る)
    # 少数出来た場合、少数で計算して最後にintぐるみをして値を返す
    @staticmethod
    def stack_check(value) -> int:
        value = str(value).replace("椎名", "").lower()
        stack_frag = False
        lc_frag = False
        calc_result = [0, 0, 0]
        if "lc" in value:
            lc_frag = True
        if "st" in value:
            stack_frag = True
        try:
            data = value.replace("lc", "").replace("st", "").replace("個", "").split("+")
            if lc_frag:
                calc_result[0] = data[0]
                data.pop(0)
            if stack_frag:
                calc_result[1] = data[0]
                data.pop(0)
            try:
                calc_result[2] = data[0]
            except IndexError:
                pass
            a = float(calc_result[0])
            b = float(calc_result[1])
            c = float(calc_result[2])
            d = int(float(a * 3456 + b * 64 + c))
            if d <= 0:
                return 0
            else:
                return d
        except ValueError:
            return 0

    # intがvalueで来ることを想定する
    @staticmethod
    def stack_check_reverse(value: int):
        try:
            value2 = int(value)
            if value2 <= 63:
                if value2 <= 0:
                    return 0
                return value2
            else:
                i, j = divmod(value2, 64)
                k, m = divmod(i, 54)
                calc_result = []
                if k != 0:
                    calc_result.append(f"{k}LC")
                if m != 0:
                    calc_result.append(f"{m}st")
                if j != 0:
                    calc_result.append(f"{j}個")
                return f"{'+'.join(calc_result)}"
        except ValueError:
            return 0

    @staticmethod
    def get_user_auction_count(user_id):
        cur.execute("SELECT count(*) from auction where auction_owner_id = %s", (user_id,))
        a = tuple(cur.fetchone())
        cur.execute("SELECT count(*) from deal where deal_owner_id = %s", (user_id,))
        b = tuple(cur.fetchone())
        return int(a[0]) + int(b[0])

    @staticmethod
    def reset_ch_db(channel_id, mode):
        # SQLにデータ登録
        if mode == "a":
            cur.execute("UPDATE auction SET auction_owner_id = %s, embed_message_id = %s, auction_item = %s, "
                        "auction_start_price = %s, auction_bin_price = %s, auction_end_time = %s, "
                        "unit = %s, notice = %s WHERE ch_id = %s",
                        (0, 0, "undefined", "undefined",
                         "undefined", "undefined", "undefined", "undefined", channel_id))
        elif mode == "d":
            cur.execute("UPDATE deal SET deal_owner_id = %s, embed_message_id = %s, deal_item = %s, "
                        "deal_hope_price = %s, deal_end_time = %s, unit = %s, notice = %s WHERE ch_id = %s",
                        (0, 0, "undefined", "undefined",
                         "undefined", "undefined", "undefined", channel_id))
        db.commit()
        # tendもリセット
        if mode == "a":
            cur.execute("UPDATE tend SET tender_id = ARRAY[0], tend_price = ARRAY[0] WHERE ch_id = %s", (channel_id,))
            db.commit()

    @staticmethod
    def mcid_to_uuid(mcid):
        """
        MCIDをUUIDに変換する関数
        uuidを返す"""

        url = f"https://api.mojang.com/users/profiles/minecraft/{mcid}"
        try:
            res = requests.get(url)
            res.raise_for_status()
            sorp = bs4.BeautifulSoup(res.text, "html.parser")
            try:
                player_data_dict = json.loads(sorp.decode("utf-8"))
            except json.decoder.JSONDecodeError:  # mcidが存在しないとき
                return False
            uuid = player_data_dict["id"]
            return uuid
        except requests.exceptions.HTTPError:  # よくわからん、どのサイト見ても書いてあるからとりあえずtry-exceptで囲っとく
            return False

    @staticmethod
    def uuid_to_mcid(uuid):
        """
        UUIDをMCIDに変換する関数
        mcid(\なし)を返す"""

        url = f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}"
        try:
            res = requests.get(url)
            res.raise_for_status()
            sorp = bs4.BeautifulSoup(res.text, "html.parser")
            player_data_dict = json.loads(sorp.decode("utf-8"))
            mcid = player_data_dict["name"]
            return mcid
        except requests.exceptions.HTTPError:  # よくわからん、どのサイト見ても書いてあるからとりあえずtry-exceptで囲っとく
            return False

    @staticmethod
    def is_auction_category(ctx):
        """チャンネルがオークションカテゴリに入っているかの真偽値を返す関数"""
        auction_category_ids = {c.id for c in ctx.guild.categories if c.name.startswith('>')}
        return ctx.channel.category_id in auction_category_ids

    @staticmethod
    def is_normal_category(ctx):
        """チャンネルがノーマルカテゴリに入っているかの真偽値を返す関数"""
        normal_category_ids = {this.id for this in ctx.guild.categories if this.name.startswith('*')}
        return ctx.channel.category_id in normal_category_ids

    @staticmethod
    def is_siina_category(ctx):
        """チャンネルが椎名カテゴリに入っているかの真偽値を返す関数"""
        siina_channel_ids = {siina.id for siina in ctx.guild.text_channels if "椎名" in siina.name}
        return ctx.channel.id in siina_channel_ids

    @staticmethod
    def is_gacha_category(ctx):
        """チャンネルがガチャ券カテゴリに入っているかの真偽値を返す関数"""
        gacha_channel_ids = {gacha.id for gacha in ctx.guild.text_channels if "ガチャ券" in gacha.name}
        return ctx.channel.id in gacha_channel_ids

    async def dm_send(self, user_id: int, content) -> bool:
        user = self.get_user(int(user_id))
        try:
            if isinstance(content, discord.Embed):
                await user.send(embed=content)
            else:
                await user.send(content)
        except Exception as e:
            return False
        else:
            return True

    @staticmethod
    def list_to_tuple_string(list_1: list) -> str:
        """リストの状態からARRAY型のsqlに代入できる文字列を生成する"""
        tuple_string = str(tuple(list_1))
        tuple_string_format = tuple_string.replace("(", "{").replace(")", "}")
        return tuple_string_format

    async def change_message(self, ch_id: int, msg_id: int, **kwargs) -> discord.Message:
        """メッセージを取得して編集する"""
        ch = self.get_channel(ch_id)
        msg = await ch.fetch_message(msg_id)
        content = kwargs.pop("content", msg.id)
        embed = kwargs.pop("embed", msg.embeds[0] if msg.embeds else None)
        if embed is None:
            return await msg.edit(content=content)
        else:
            return await msg.edit(content=content, embed=embed)


if __name__ == '__main__':
    bot = KGX(prefix="!")
    bot.run(os.environ['TOKEN'])

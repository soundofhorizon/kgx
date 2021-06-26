# coding=utf-8
import asyncio
import json
import random
import os
import traceback
import re
from datetime import datetime
from typing import Union, List

import bs4
import discord
import psycopg2
import requests
from discord import Embed
from discord.ext import commands

SQLpath = os.environ["DATABASE_URL"]
db = psycopg2.connect(SQLpath)  # sqlに接続
cur = db.cursor()  # なんか操作する時に使うやつ


stack_check_pattern = re.compile(r"\s*\d+(\.\d+)?(st|lc|個)?(\s*\+\s*\d+(\.\d+)?(st|lc|個)?)*\s*")

class KGX(commands.Bot):
    stack_check_pattern = stack_check_pattern
    def __init__(self, prefix):
        intents = discord.Intents.all()
        super().__init__(command_prefix=prefix, help_command=None, intents=intents)

        description_1 = "<:shiina_balance:558175954686705664>!start\n\n" \
                      "オークションを始めるためのコマンドです。オークションチャンネルでのみ使用可能です。\n\n" \
                      "-------\n" \
                      "<:siina:558251559394213888>!tend 入札する量\n\n" \
                      "\n\n" \
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
                      "-------\n"

        description_2 = "**ここから以下は運営専用**\n--------\n" \
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
                      "-------\n" \
                      "<:shiina_balance:558251559394213888>!show_bid_ranking\n\n" \
                      "<#832956663908007946>の更新\n\n" \
                      "-------\n" \
                      "<:shiina:558175954686705664>!star_delete\n\n" \
                      "星を強制的に取り外す\n\n" \
                      "-------\n" \
                      "<:shiina_balance:558251559394213888>!execute_sql\n\n" \
                      "引数のSQL文を実行する\n\n" \
                      "-------\n" \
                      "<:siina:558251559394213888>!dbsetup\n\n" \
                      "実行チャンネルをデータベースに登録する\n\n" \
                      "-------\n" 
        self.embed_1 = discord.Embed(description=description_1, color=0x66cdaa)
        self.embed_2 = discord.Embed(description=description_2, color=0x66cdaa)

        self.cur = cur 

        for cog in os.listdir(f"./cogs"):  # cogの読み込み
            if cog.endswith(".py"):
                try:
                    self.load_extension(f"cogs.{cog[:-3]}")
                except Exception:
                    traceback.print_exc()

    async def on_ready(self):
        color = [0x126132, 0x82fc74, 0xfea283, 0x009497, 0x08fad4, 0x6ed843, 0x8005c0]
        await self.get_channel(678083611697872910).purge(limit=10)
        await self.get_channel(678083611697872910).send(embed=self.embed_1)
        await self.get_channel(678083611697872910).send(embed=self.embed_2)
        await self.get_channel(722092542249795679).send(
            embed=discord.Embed(description="起動しました。", color=random.choice(color)))

    async def on_guild_channel_create(self, channel):
        """チャンネルが出来た際に自動で星をつける"""
        if ">" not in channel.category.name and "*" not in channel.category.name:
            return
        if "☆" in channel.name:
            return
        try:
            await asyncio.wait_for(channel.edit(name=f"{channel.name}☆"), timeout=3.0)
        except asyncio.TimeoutError:
            return

    async def on_command_error(self, ctx, error):
        """すべてのコマンドで発生したエラーを拾う"""
        if isinstance(error, commands.CommandInvokeError): # コマンド実行時にエラーが発生したら
            if hasattr(ctx.command, "on_error"): # コマンド別のエラーハンドラが定義されていれば
                return
            orig_error = getattr(error, "original", error)
            error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
            error_message = f'```{error_msg}```'
            ch = ctx.guild.get_channel(628807266753183754)
            d = datetime.now()  # 現在時刻の取得
            time = d.strftime("%Y/%m/%d %H:%M:%S")
            embed = Embed(title='Error_log', description=error_message, color=0xf04747)
            embed.set_footer(text=f'channel:{ctx.channel}\ntime:{time}\nuser:{ctx.author.display_name}')
            await ch.send(embed=embed)

    # これより自作メソッド
    @staticmethod
    def check_role(score: int, ctx):
        """ポイントに応じたroleを判定する"""
        role1 = discord.utils.get(ctx.guild.roles, name="新星")
        role2 = discord.utils.get(ctx.guild.roles, name="常連")
        role3 = discord.utils.get(ctx.guild.roles, name="金持ち")
        role4 = discord.utils.get(ctx.guild.roles, name="覚醒者")
        role5 = discord.utils.get(ctx.guild.roles, name="登頂者")
        role6 = discord.utils.get(ctx.guild.roles, name="落札王")
        role7 = discord.utils.get(ctx.guild.roles, name="落札神")
        if score >= 100:
            before = role6
            after = role7
        elif score >= 60:
            before = role5
            after = role6
        elif score >= 30:
            before = role4
            after = role5
        elif score >= 10:
            before = role3
            after = role4
        elif score >= 5:
            before = role2
            after = role3
        elif score >= 3:
            before = role1
            after = role2
        elif score >= 1:
            before = None
            after = role1
        else:
            raise TypeError("wrong value has passed")

        return before, after

    def create_ranking_embed(self) -> discord.Embed:
        """落札ランキングのemebedを作成"""
        # user_dataテーブルには「0:ユーザーID bigint, 1:落札ポイント smallint, 2:警告レベル smallint」で格納されているのでこれを全部、落札ポイント降順になるように出す
        cur.execute("SELECT user_id, bid_score FROM user_data ORDER BY bid_score desc;")
        data = cur.fetchall()

        # ランキングを出力する。まずは辞書型の落札ポイントを基準として降順ソートする。メンバーをmem,スコアをscoreとする
        description = ""
        for rank, (user_id, bid_score) in enumerate(data, 1):
            # 落札ポイント0pt以下は表示しない
            if bid_score == 0:
                break
            elif user := self.get_user(user_id):
                description += f"{rank}位: {user.display_name} - 落札ポイント -> {bid_score}\n"

        # 表示する
        d = datetime.now()  # 現在時刻の取得
        time = d.strftime("%Y/%m/%d %H:%M:%S")
        embed = Embed(
            title='**落札ポイントランキング**',
            description=description,
            color=0x48d1cc)  # 発言内容をdescriptionにセット
        embed.set_footer(text=f'UpdateTime：{time}')  # チャンネル名,時刻,鯖のアイコンをセット
        return embed

    @staticmethod
    def create_high_bid_ranking() -> List[discord.Embed]:
        """落札額ランキングembed作成 複数のembed情報を詰め込んだリストを返す"""
        # bid_rankingテーブルには「0:落札者の名前 text, 1:落札物 text, 2:落札額 bigint, 3:出品者の名前 text」で格納されているのでこれを全部、落札額降順になるように出す
        cur.execute("SELECT * FROM bid_ranking ORDER BY bid_price desc;")
        data = cur.fetchall()

        # embed保管リスト
        embed_list = []
        # データ毎に取り出す
        description = ""

        for i, (bidder_name, item_name, bid_price, seller_id) in enumerate(data[:300], 1):
            # 気持ち程度のレイアウト合わせ。1桁と2桁の違い
            if i <= 9:
                description += " "
            # listの中身は[落札者,落札物,落札額,出品者ID]
            description += f"{i}位: 出品者->{bidder_name}\n" \
                           f"  　　出品物->{item_name}\n" \
                           f"  　　落札額->椎名{bot.stack_check_reverse(bid_price)}\n" \
                           f"  　　落札者->{bidder_name}\n\n"

            # descriptionの長さが2000を超えるとエラーになる。吐き出してリセット案件
            if len(description) > 1800:
                embed = discord.Embed(title="**落札額ランキング**", description=description, color=0xddc7ff)
                embed_list.append(embed)
                description = ""

        # 表示する
        embed = discord.Embed(description=description, color=0xddc7ff)
        d = datetime.now()  # 現在時刻の取得
        time = d.strftime("%Y/%m/%d %H:%M:%S")
        embed.set_footer(text=f"UpdateTime: {time}")
        embed_list.append(embed)
        return embed_list

    @staticmethod
    def stack_check(value) -> int:
        """
        [a lc + b st + c…]などがvalueで来ることを想定する(正しくない文字列が渡されれば0を返す)
        小数で来た場合、小数で計算して最後にintぐるみをして値を返す
        :param value: [a lc + b st + c…]の形の価格
        :return: 価格をn個にしたもの(小数は丸め込む)
        """
        UNITS = {"lc": 3456, "st": 64, "個": 1} # 単位と対応する値
        value = str(value).lower()

        if stack_check_pattern.fullmatch(value):
            value = re.sub(r"\s", "", value) # 空白文字を削除
            result = 0

            for term in value.split("+"): # 項ごとに分割
                unit_match = re.search(r"(st|lc|個)?$", term)
                unit = UNITS.get(unit_match.group(), 1)
                result += float(term[:unit_match.start()]) * unit

            return int(result)

        else:
            return 0

    @staticmethod
    def stack_check_reverse(value: int) -> Union[int, str]:
        """
        :param value: int型の価格
        :return:　valueをストックされた形に直す
        """
        if value <= 63:
            if value <= 0:
                return 0
            return value
        else:
            st, single = divmod(value, 64)
            lc, st = divmod(st, 54)
            calc_result = []
            if lc != 0:
                calc_result.append(f"{lc}LC")
            if st != 0:
                calc_result.append(f"{st}st")
            if single != 0:
                calc_result.append(f"{single}個")
            return '+'.join(calc_result)

    @staticmethod
    def get_user_auction_count(user_id: int) -> int:
        """ユーザーが開催しているオークションの数を取得"""
        cur.execute("SELECT count(*) from auction where auction_owner_id = %s", (user_id,))
        auction_count, = cur.fetchone()
        cur.execute("SELECT count(*) from deal where deal_owner_id = %s", (user_id,))
        deal_count, = cur.fetchone()
        return auction_count + deal_count

    @staticmethod
    def reset_ch_db(channel_id: int, mode: str) -> None:
        """SQLに登録されているチャンネルのデータを初期化"""
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
    def mcid_to_uuid(mcid) -> Union[str, bool]:
        """
        MCIDをUUIDに変換する関数
        uuidを返す
        """
        url = f"https://api.mojang.com/users/profiles/minecraft/{mcid}"
        try:
            res = requests.get(url)
            res.raise_for_status()
            soup = bs4.BeautifulSoup(res.text, "html.parser")
            try:
                player_data_dict = json.loads(soup.decode("utf-8"))
            except json.decoder.JSONDecodeError:  # mcidが存在しないとき
                return False
            uuid = player_data_dict["id"]
            return uuid
        except requests.exceptions.HTTPError:  # よくわからん、どのサイト見ても書いてあるからとりあえずtry-exceptで囲っとく
            return False

    @staticmethod
    def uuid_to_mcid(uuid) -> str:
        """
        UUIDをMCIDに変換する関数
        mcid(\なし)を返す
        """
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
    def is_auction_category(ctx: commands.Context) -> bool:
        """チャンネルがオークションカテゴリに入っているかの真偽値を返す関数"""
        auction_category_ids = {c.id for c in ctx.guild.categories if c.name.startswith('>')}
        return ctx.channel.category_id in auction_category_ids

    @staticmethod
    def is_normal_category(ctx: commands.Context) -> bool:
        """チャンネルがノーマルカテゴリに入っているかの真偽値を返す関数"""
        normal_category_ids = {this.id for this in ctx.guild.categories if this.name.startswith('*')}
        return ctx.channel.category_id in normal_category_ids

    @staticmethod
    def is_siina_category(ctx: commands.Context) -> bool:
        """チャンネルが椎名カテゴリに入っているかの真偽値を返す関数"""
        siina_channel_ids = {siina.id for siina in ctx.guild.text_channels if "椎名" in siina.name}
        return ctx.channel.id in siina_channel_ids

    @staticmethod
    def is_gacha_category(ctx: commands.Context) -> bool:
        """チャンネルがガチャ券カテゴリに入っているかの真偽値を返す関数"""
        gacha_channel_ids = {gacha.id for gacha in ctx.guild.text_channels if "ガチャ券" in gacha.name}
        return ctx.channel.id in gacha_channel_ids

    async def dm_send(self, user_id: int, content) -> bool:
        """
        指定した対象にdmを送るメソッド
        :param user_id: dmを送る対象のid
        :param content: dmの内容
        :return: dmを送信できたかのbool値
        """

        cur.execute("SELECT dm_flag FROM user_data where user_id = %s", (user_id,))
        dm_flag, = cur.fetchone()

        if not dm_flag:
            return False

        try:
            user = self.get_user(int(user_id))
        except ValueError as e:
            ch = self.get_channel(628807266753183754)
            await ch.send(user_id)
        try:
            if isinstance(content, discord.Embed):
                await user.send(embed=content)
            else:
                await user.send(content)
        except Exception:
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

    @staticmethod
    async def delete_to(ctx, msg_id: int) -> None:
        """特定のメッセージまでのメッセージを削除する"""
        msg = await ctx.fetch_message(msg_id)
        await ctx.channel.purge(limit=None, after=msg)


if __name__ == '__main__':
    bot = KGX(prefix="!")
    bot.run(os.environ['TOKEN'])

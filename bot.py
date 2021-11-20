# coding=utf-8
import asyncio
import bisect
import json
import os
import random
import re
import traceback
from datetime import datetime
from typing import Union, List, Generator, Optional

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
        intents = discord.Intents.all()
        super().__init__(command_prefix=prefix, help_command=None, intents=intents)
        self.cur = cur

        for cog in os.listdir(f"./cogs"):  # cogの読み込み
            if cog.endswith(".py"):
                try:
                    self.load_extension(f"cogs.{cog[:-3]}")
                except Exception:
                    traceback.print_exc()

    async def on_ready(self):
        color = [0x126132, 0x82fc74, 0xfea283, 0x009497, 0x08fad4, 0x6ed843, 0x8005c0]
        await self.get_channel(722092542249795679).send(
            embed=discord.Embed(description="起動しました。", color=random.choice(color)))
        print("ready")

        # コマンドのグローバルチェックを付ける
        @self.check
        def check_for_all_command(ctx):
            if not isinstance(ctx.guild, discord.Guild) or ctx.guild.id != 558125111081697300:
                return False # KGx以外なら弾く
            # MCID報告済みかどうか
            return bool(discord.utils.get(ctx.author.roles, id=558999306204479499))
    

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
        if isinstance(error, commands.CommandInvokeError):  # コマンド実行時にエラーが発生したら
            if hasattr(ctx.command, "on_error"):  # コマンド別のエラーハンドラが定義されていれば
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
    def join_within_limit(texts: List[str], sep: str = "\n", limit: int = 4096) -> Generator[str, None, None]:
        """
        sep.join(texts)のような文字列を生成するジェネレータを返す。各要素はの長さは必ずlimit以下になるようにしている
        textsの1要素がlimitよりも長ければTypeError。
        for description in join_within_limit(text): のような使われ方を想定している
        """
        if not texts:  # 空のリストが与えらたらreturn
            return

        length_sum = len(texts[0])
        before = 0

        if length_sum > limit:
            raise ValueError("one element is too long")

        for i, text in enumerate(texts[1:], 1):
            length_sum += len(sep) + len(text)

            if length_sum > limit:
                yield sep.join(texts[before:i])
                before = i
                length_sum = len(text)

                if length_sum > limit:
                    raise ValueError("one element is too long")

        yield sep.join(texts[before:])

    async def update_bidscore_ranking(self) -> None:
        """落札ポイントランキングを更新"""
        # user_dataテーブルには「0:ユーザーID bigint, 1:落札ポイント smallint, 2:警告レベル smallint」で格納されているので(0, 1)を、落札ポイント降順になるように出す
        kgx_server = self.get_guild(558125111081697300)
        members_id = tuple(member.id for member in kgx_server.members)  # メンバー全員のid
        cur.execute("SELECT user_id, bid_score FROM user_data where user_id in %s ORDER BY bid_score desc;", (members_id,))  # メンバーの情報だけ取得
        data = cur.fetchall()

        # ランキングを出力する。まずは辞書型の落札ポイントを基準として降順ソートする。メンバーをmem,スコアをscoreとする
        description = ""
        for rank, (user_id, bid_score) in enumerate(data, 1):
            # 落札ポイント0pt以下は表示しない
            if bid_score == 0:
                break
            user_name = self.get_user(user_id).display_name
            user_name_formatted = user_name.replace("_", "\_")
            description += f"{rank}位: {user_name_formatted} - 落札ポイント -> {bid_score}\n"

        # 表示する
        d = datetime.now()  # 現在時刻の取得
        time = d.strftime("%Y/%m/%d %H:%M:%S")
        embed = Embed(
            title='**落札ポイントランキング**',
            description=description,
            color=0x48d1cc)  # 発言内容をdescriptionにセット
        embed.set_footer(text=f'UpdateTime：{time}')  # 時刻をセット
        bidscore_ranking_channel = self.get_channel(677905288665235475)
        await bidscore_ranking_channel.purge(limit=10)
        await bidscore_ranking_channel.send(embed=embed)

    async def update_high_bid_ranking(self) -> None:
        """落札額ランキングの更新"""
        # bid_rankingテーブルには「0:落札者の名前 text, 1:落札物 text, 2:落札額 bigint, 3:出品者の名前 text」で格納されているのでこれを全部、落札額降順になるように出す
        cur.execute("SELECT * FROM bid_ranking ORDER BY bid_price desc;")
        data = cur.fetchall()

        # embed保管リスト
        embed_list = []
        bid_ranking = []

        for i, (bidder_name, item_name, bid_price, seller_id) in enumerate(data[:300], 1):
            # 気持ち程度のレイアウト合わせ。1桁と2桁の違い
            bid_info = ""
            if i <= 9:
                bid_info += " "
            seller_name_formatted = seller_id.replace("_", "\_")
            bidder_name_formatted = bidder_name.replace("_", "\_")
            bid_info += f"{i}位: 出品者->{seller_name_formatted}\n" \
                        f"  　　出品物->{item_name}\n" \
                        f"  　　落札額->椎名{bot.stack_check_reverse(bid_price)}\n" \
                        f"  　　落札者->{bidder_name_formatted}"
            bid_ranking.append(bid_info)

        for description in self.join_within_limit(bid_ranking, sep="\n\n"):
            embed = discord.Embed(description=description, color=0xddc7ff)
            embed_list.append(embed)

        embed_list[0].title = " **落札額ランキング**"

        embed_list[-1].color = 0xddc7ff
        d = datetime.now()  # 現在時刻の取得
        time = d.strftime("%Y/%m/%d %H:%M:%S")
        embed_list[-1].set_footer(text=f"UpdateTime: {time}")

        bid_price_ranking_channel = self.get_channel(832956663908007946)
        await bid_price_ranking_channel.purge(limit=10)
        for embed in embed_list:
            await bid_price_ranking_channel.send(embed=embed)
    
    async def update_bidscore_role(self, member: discord.Member, score: int):
        guild_roles = member.guild.roles
        """ポイントに応じてroleを更新する"""
        bidscore_roles = [
            discord.utils.get(guild_roles, name="新星"),
            discord.utils.get(guild_roles, name="常連"),
            discord.utils.get(guild_roles, name="金持ち"),
            discord.utils.get(guild_roles, name="覚醒者"),
            discord.utils.get(guild_roles, name="登頂者"),
            discord.utils.get(guild_roles, name="落札王"),
            discord.utils.get(guild_roles, name="落札神")
        ]
        threshold = [1, 3, 5, 10, 30, 60, 100]

        now = bisect.bisect(threshold, score)-1
        
        after = bidscore_roles[now]
        if after is not None and after not in member.roles:
            await member.add_roles(after)

        before = None
        for role in bidscore_roles[1:]:
            if role in member.roles:
                # 付いていた役職を取得
                before = role
                if role != after:
                    # 該当しない役職が付いていれば外す
                    await member.remove_roles(role)
        
        return before, after

    @staticmethod
    def stack_check(value) -> Optional[int]:
        """
        [a lc + b st + c…]などがvalueで来ることを想定する(正しくない文字列が渡されればNoneを返す)
        小数で来た場合、小数で計算して最後にintぐるみをして値を返す
        :param value: [a lc + b st + c…]の形の価格
        :return: 価格をn個にしたもの(小数は丸め込む)。またはNone
        """
        UNITS = {"lc": 3456, "st": 64}  # 単位と対応する値
        value = str(value).lower()

        if not re.fullmatch(r"\s*\d+((\.\d+)?(st|lc))?(\s*\+\s*\d+((\.\d+)?(st|lc))?)*\s*", value):
            return

        value = re.sub(r"\s", "", value)  # 空白文字を削除
        result = 0

        for term in value.split("+"):  # 項ごとに分割
            unit_match = re.search(r"(st|lc)?$", term)
            unit = UNITS.get(unit_match.group(), 1)
            result += float(term[:unit_match.start()]) * unit

        return int(result)

    @staticmethod
    def stack_check_reverse(value: int) -> str:
        """
        :param value: int型の価格
        :return:　valueをストックされた形に直す
        """
        if value <= 63:
            if value <= 0:
                return "0"
            return str(value)
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
    def insert_auction_info(ch_id: int) -> None:
        """
        ch_idで開催されているオークションをauction_infoに保存し、before_auctionカラムにidを入れる
        """
        cur.execute("SELECT auction_owner_id, auction_item, auction_start_price, auction_bin_price, auction_end_time, unit, notice, embed_message_id FROM auction WHERE ch_id = %s;", (ch_id,))
        owner_id, item, start_price, bin_price, end_time, unit, notice, embed_id = cur.fetchone()
        cur.execute("SELECT tender_id, tend_price FROM tend WHERE ch_id = %s", (ch_id,))
        tend = list(map(list, zip(*cur.fetchone())))[1:]

        start_price = int(start_price)
        bin_price = int(bin_price) if bin_price != "なし" else None
        end_time = datetime.strptime(end_time, "%Y/%m/%d-%H:%M")

        cur.execute("INSERT INTO auction_info (ch_id, owner_id, item, start_price, bin_price, end_time, unit, notice, tend, embed_id) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);",
                    (ch_id, owner_id, item, start_price, bin_price, end_time, unit, notice, tend, embed_id))
        
        cur.execute("SELECT id FROM auction_info ORDER BY id DESC LIMIT 1;")
        auction_id, = cur.fetchone()
        cur.execute("UPDATE auction set before_auction = %s WHERE ch_id = %s;", (auction_id, ch_id))
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
        msg = await ctx.channel.fetch_message(msg_id)
        await ctx.channel.purge(limit=None, after=msg)


if __name__ == '__main__':
    bot = KGX(prefix="!")
    bot.run(os.environ['TOKEN'])

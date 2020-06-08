# coding=utf-8
import redis
from discord.ext import commands
import discord
import os
import traceback
from datetime import datetime
from discord import Embed


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
                      "<:siina:558251559394213888>!checkAllUserID\n\n" \
                      "<#642052474672250880> に、現在このサーバーにいるメンバーのニックネームとユーザーIDをセットで照会します。\n\n" \
                      "-------\n" \
                      "<:shiina_balance:558175954686705664>!bidscoreGS モード ユーザーID 落札ポイント(setモードのみ)\n\n" \
                      "特定の人の落札ポイントを調べたり、変更するために使用します。\n\n" \
                      "<mode:GET>　getモードでは、特定の人の落札ポイントを調べられます。\nコマンドは以下のように使用します。\n\n" \
                      "(例)!bidscoreGS get 251365193127297024\n{これで、EternalHorizonの落札ポイントがわかる}\n\n" \
                      "<mode:SET>　setモードでは、特定の人の落札ポイントを変更できます。\nコマンドは以下のように使用します。\n\n" \
                      "(例)!bidscoreGS set 251365193127297024 10\n{これで、EternalHorizonの落札ポイントが10ポイントに変更される。}\n\n" \
                      "-------\n" \
                      "<:siina:558251559394213888>!bidscoreRanking\n\n" \
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

        self.remove_command('help')  # デフォルトのヘルプコマンドを除外
        for cog in os.listdir(f"./cogs"):  # cogの読み込み
            if cog.endswith(".py"):
                try:
                    self.load_extension(f"cogs.{cog[:-3]}")
                except Exception:
                    traceback.print_exc()

    @staticmethod
    def checkRole(newscore, user, ctx):
        role1 = discord.utils.get(ctx.guild.roles, name="新星")
        role2 = discord.utils.get(ctx.guild.roles, name="常連")
        role3 = discord.utils.get(ctx.guild.roles, name="金持ち")
        role4 = discord.utils.get(ctx.guild.roles, name="覚醒者")
        role5 = discord.utils.get(ctx.guild.roles, name="登頂者")
        role6 = discord.utils.get(ctx.guild.roles, name="落札王")
        role7 = discord.utils.get(ctx.guild.roles, name="落札神")
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

    def createRankingEmbed(self):
        # scoreを抜き出したメンバーのIDのリストで一個一個keyとして突っ込んだ後、それに対応する落札ポイントを引っ張って突っ込む

        # 落札ポイントを入れるリスト
        scoreList = []

        # メンバーを入れるリスト
        memberList = []

        # 上記2つをまとめて辞書型にする
        bidscoreDict = {}

        botCount = 0
        r = redis.from_url(os.environ['REDIS_URL'])  # os.environで格納された環境変数を引っ張ってくる
        for member in range(self.get_guild(558125111081697300).member_count):
            if self.get_guild(558125111081697300).members[member].bot:
                botCount += 1

            memberList.append(self.get_guild(558125111081697300).members[member].display_name)

            key = f"score-{self.get_guild(558125111081697300).members[member].id}"
            scoreList.append(int(r.get(key) or "0"))

            # メンバー : その人のスコア　で　辞書型結合を行う
            bidscoreDict[memberList[member]] = scoreList[member]

            # 全員分確認終わったら今度は出力
            if member == (self.get_guild(558125111081697300).member_count - 1):
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

    # intがvalueで来ることを想定する
    @staticmethod
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

    # 落札額ランキングembed作成 複数のembed情報を詰め込んだリストを返す
    def createHighBidRanking(self):
        i = 0
        r = redis.from_url(os.environ['HEROKU_REDIS_ORANGE_URL'])  # os.environで格納された環境変数を引っ張ってくる
        radis_get_data_list = []

        # データをリストに突っ込む。NoneTypeはifにするとFalseとして解釈されるのを利用する
        # ついでに、ユーザーが存在するかを確かめて、存在しなかったらpass
        while True:
            if r.get(i):
                if self.get_user(int(r.get(i).decode().split(",")[3])):
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
            description += f"{i + 1}位: 出品者->{self.get_user(int(radis_get_data_list[i][3])).display_name}\n" \
                           f"  　　出品物->{radis_get_data_list[i][1]}\n" \
                           f"  　　落札額->{self.siina_check_reverse(int(radis_get_data_list[i][2]))}\n" \
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
    @staticmethod
    def siina_check(value):
        try:
            if "st" in value or "ST" in value:
                if "+" in value:
                    value_new = str(value).replace("椎名", "").replace("st", "").replace("ST", "").replace("個",
                                                                                                         "").split(
                        "+")
                else:
                    value_new = [str(value).replace("椎名", "").replace("st", "").replace("ST", "").replace("個", ""), 0]
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

    @staticmethod
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

    async def on_ready(self):
        await self.get_channel(678083611697872910).purge(limit=1)
        await self.get_channel(678083611697872910).send(embed=help())

    async def on_command_error(self, ctx, error):  # すべてのコマンドで発生したエラーを拾う
        if isinstance(error, commands.CommandInvokeError):  # コマンド実行時にエラーが発生したら
            error_message = f'```{traceback.format_exc()}```'
            ch = ctx.guild.get_channel(628807266753183754)
            d = datetime.now()  # 現在時刻の取得
            time = d.strftime("%Y/%m/%d %H:%M:%S")
            embed = Embed(title='Error_log', description=error_message, color=0xf04747)
            embed.set_footer(text=f'channel:{ctx.channel}\ntime:{time}\nuser:{ctx.author.display_name}')
            await ch.send(embed=embed)


if __name__ == '__main__':
    bot = KGX(prefix="!")
    bot.run(os.environ['TOKEN'])

# coding=utf-8
from discord.ext import commands
import discord
import os
import traceback


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

    async def on_ready(self):
        await self.get_channel(678083611697872910).purge(limit=1)
        await self.get_channel(678083611697872910).send(embed=help())


if __name__ == '__main__':
    bot = KGX(prefix="!")
    bot.run("NTUwNjQyNTQ0MjMzNDE0NjU3.XSrHdg.amSg0hQUvNMAPwCjQiuklJRuXYw")

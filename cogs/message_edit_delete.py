from discord.ext import commands
from datetime import datetime
from discord import Embed


class MessageEditDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
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

    @commands.Cog.listener()  # point付与の術
    async def on_message_edit(self, before, after):
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
        embed.set_author(name=before.author, icon_url=before.author.avatar_url)  # ユーザー名+ID,アバターをセット
        embed.set_footer(text=f'User ID：{before.author.id} Time：{time}',
                         icon_url=before.guild.icon_url, )  # チャンネル名,時刻,鯖のアイコンをセット
        ch = before.guild.get_channel(628807266753183754)
        await ch.send(embed=embed)


def setup(bot):
    bot.add_cog(MessageEditDelete(bot))

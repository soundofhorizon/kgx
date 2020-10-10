import os
import random
import re
import traceback
from datetime import datetime

import bs4
import discord
import psycopg2
import qrcode
import requests
from discord import Embed
from discord.ext import commands

SQLpath = os.environ["DATABASE_URL"]
db = psycopg2.connect(SQLpath)  # sqlに接続
cur = db.cursor()  # なんか操作する時に使うやつ

auction_notice_ch_id = 727333695450775613


class Message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # メッセージ送信者がBotだった場合は無視する
        if message.author.bot:
            return
        try:
            # MCID_check
            if message.channel.id == 558278443440275461:
                mcid = f'{message.content}'.replace('\\', '')
                p = re.compile(r'^[a-zA-Z0-9_]+$')
                if p.fullmatch(mcid):
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
                            try:
                                await message.author.edit(nick=mcid)
                            except discord.errors.Forbidden:
                                await message.channel.send(f"{message.author.mention}権限エラー\nニックネームを申請したMCIDに変更してください。")
                            await message.add_reaction(random.choice(emoji))
                            # uuidを確かめる
                            uuid = self.bot.mcid_to_uuid(mcid)
                            channel = self.bot.get_channel(591244559019802650)
                            color = [0x3efd73, 0xfb407c, 0xf3f915, 0xc60000, 0xed8f10, 0xeacf13, 0x9d9d9d, 0xebb652,
                                     0x4259fb,
                                     0x1e90ff]
                            embed = discord.Embed(description=f'{message.author.display_name}のMCIDの報告を確認したよ！',
                                                  color=random.choice(color))
                            embed.set_author(name=message.author,
                                             icon_url=message.author.avatar_url, )  # ユーザー名+ID,アバターをセット
                            await channel.send(embed=embed)

                            # SQLのuser_dataに新規登録
                            cur.execute("INSERT INTO user_data values (%s, %s, %s, ARRAY[%s]);",
                                        (message.author.id, 0, 0, uuid))
                            db.commit()
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

            # 引用機能
            url_filter = [msg.split("/")[1:] for msg in re.split(
                "https://(ptb.|canary.|)discord(app|).com/channels/558125111081697300((/[0-9]+){2})", message.content)
                          if
                          re.match("(/[0-9]+){2}", msg)]
            if len(url_filter) >= 1:
                for url in url_filter:
                    try:
                        channel_id = int(url[0])
                        message_id = int(url[1])
                        ch = message.guild.get_channel(channel_id)
                        if ch is None:
                            continue
                        msg = await ch.fetch_message(message_id)

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

        except Exception:
            error_message = f'```{traceback.format_exc()}```'
            ch = message.guild.get_channel(628807266753183754)
            d = datetime.now()  # 現在時刻の取得
            time = d.strftime("%Y/%m/%d %H:%M:%S")
            embed = Embed(title='Error_log', description=error_message, color=0xf04747)
            embed.set_footer(text=f'channel:{message.channel}\ntime:{time}\nuser:{message.author.display_name}')
            await ch.send(embed=embed)

    @commands.command()
    async def qr(self, ctx, *, input):
        try:
            img = qrcode.make(f"{input}")
            img.save("./icon.png")
            image = discord.File("./icon.png", filename="icon.png")
            embed = discord.Embed(description=f"作成結果",
                                  color=0x4259fb
                                  )
            embed.set_image(url="attachment://icon.png")
            await ctx.channel.send(file=image, embed=embed)
        except:
            await ctx.send("QRコードに含めるデータ量が大きすぎます")

    @commands.command()
    async def stack_check(self, ctx, amount):
        if self.bot.stack_check_reverse(amount) == 00:
            if self.bot.stack_check(amount) == 0:
                await ctx.channel.send(f"入力した値が0または不正な値です。")
                return
            else:
                await ctx.channel.send(f"{amount}はスタック表記で{self.bot.stack_check_reverse(amount)}です。")
        else:
            await ctx.channel.send(f"{amount}は整数値で{self.bot.stack_check(amount)}です。")


def setup(bot):
    bot.add_cog(Message(bot))

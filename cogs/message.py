import os
import random
import re
import traceback
from datetime import datetime

import discord
import psycopg2
import qrcode
import requests
from discord import Embed
from discord.ext import commands
from discord_slash import cog_ext
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_option, create_permission

SQLpath = os.environ["DATABASE_URL"]
db = psycopg2.connect(SQLpath)  # sqlに接続
cur = db.cursor()  # なんか操作する時に使うやつ

auction_notice_ch_id = 727333695450775613


class Message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    guild_id = [558125111081697300]

    permisson_verified = {
        558125111081697300: [
            create_permission(558999306204479499, SlashCommandPermissionType.ROLE, True),
            create_permission(678502401723990046, SlashCommandPermissionType.ROLE, False)
        ]
    }

    permisson_not_verified = {
        558125111081697300: [
            create_permission(558999306204479499, SlashCommandPermissionType.ROLE, False),
            create_permission(678502401723990046, SlashCommandPermissionType.ROLE, True)
        ]
    }

    @commands.Cog.listener()
    async def on_message(self, message):
        # メッセージ送信者がBotだった場合は無視する
        if message.author.bot:
            return
        try:
            # MCID_check
            if message.channel.id == 558278443440275461:
                mcid = message.content.replace("\\", "")
                if re.fullmatch("[a-zA-Z0-9_]{2,16}", mcid):
                    url = "https://ranking-gigantic.seichi.click/api/search/player"
                    payload = {'lim': '1', 'q': mcid}
                    try:
                        res = requests.get(url, params=payload)
                        # {'result_count': 1, 'query': 'unchama',
                        # 'players': [{'name': 'unchama','uuid': 'b66cc3f6-a045-42ad-b4b8-320f20caf140'}]}
                        res.raise_for_status()
                        res = res.json()

                        if res["result_count"] >= 1 and res["players"][0]["name"].lower() == mcid.lower():
                            # 存在した場合の処理
                            role1 = discord.utils.get(message.guild.roles, name="新人")
                            role2 = discord.utils.get(message.guild.roles, name="MCID報告済み")
                            await message.author.remove_roles(role1)
                            await message.author.add_roles(role2)
                            try:
                                await message.author.edit(nick=mcid)
                            except discord.errors.Forbidden:
                                await message.channel.send(f"{message.author.mention}権限エラー\nニックネームを申請したMCIDに変更してください。")

                            emoji = ['👍', '🙆']
                            await message.add_reaction(random.choice(emoji))
                            channel = self.bot.get_channel(591244559019802650)
                            color = [
                                0x3efd73, 0xfb407c, 0xf3f915, 0xc60000,
                                0xed8f10, 0xeacf13, 0x9d9d9d, 0xebb652,
                                0x4259fb, 0x1e90ff
                            ]
                            embed = discord.Embed(description=f'{message.author.display_name}のMCIDの報告を確認したよ！',
                                                  color=random.choice(color))
                            embed.set_author(name=message.author, icon_url=message.author.avatar_url)
                            await channel.send(embed=embed)

                            # SQLのuser_dataに新規登録
                            uuid = res["players"][0]["uuid"].replace("-", "")
                            cur.execute("INSERT INTO user_data values (%s, %s, %s, ARRAY[%s]);", (message.author.id, 0, 0, uuid))
                            db.commit()
                        else:
                            embed = discord.Embed(
                                description=f'{message.author} さん。\n入力されたMCIDは実在しないか、又はまだ一度も整地鯖にログインしていません。\n'
                                            '続けて間違った入力を行うと規定によりBANの対象になることがあります。',
                                color=0xff0000)
                            await message.channel.send(embed=embed)
                    except requests.exceptions.HTTPError:
                        await message.channel.send("requests.exceptions.HTTPError")
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

    @cog_ext.cog_slash(name="qr",
                       guild_ids=guild_id,
                       description="文字列をQRコードに変換し、そのQR画像を出力します。(それだけです)",
                       options=[
                           create_option(
                               name="qrcode_context",
                               description="お好きな文章を書いてください。長すぎるとエラーになります",
                               option_type=3,
                               required=True
                           )
                       ],
                       permissions=permisson_verified
                       )
    async def qr(self, ctx, qrcode_context: str):
        try:
            img = qrcode.make(f"{qrcode_context}")
            img.save("./icon.png")
            image = discord.File("./icon.png", filename="icon.png")
            embed = discord.Embed(description=f"作成結果",
                                  color=0x4259fb
                                  )
            embed.set_image(url="attachment://icon.png")
            await ctx.send(file=image, embed=embed, hidden=True)
        except Exception:
            await ctx.send("QRコードに含めるデータ量が大きすぎます", hidden=True)

    @cog_ext.cog_slash(name="uuid_report",
                       guild_ids=guild_id,
                       description="uuidを報告するためのコマンドです。(一度報告すると使えなくなります。)",
                       options=[
                           create_option(
                               name="mcid",
                               description="あなたのMCIDを入力してください。",
                               option_type=3,
                               required=True
                           )
                       ],
                       permissions=permisson_not_verified
                       )
    async def uuid_report(self, ctx, mcid: str):
        if discord.utils.get(ctx.author.roles, name="uuid未チェック"):
            uuid = self.bot.mcid_to_uuid(mcid)
            if uuid:
                cur.execute(f"update  user_data set uuid = ARRAY['{uuid}'] where user_id = {ctx.author.id}")
                db.commit()
                await ctx.send(f"{mcid}さんのuuid: {uuid}をシステムに登録しました。")
                role = discord.utils.get(ctx.guild.roles, name="uuid未チェック")
                await ctx.author.remove_roles(role)
                role = discord.utils.get(ctx.guild.roles, id=558999306204479499)  # MCID報告済み
                await ctx.author.add_roles(role)
            else:
                await ctx.send(f"MCID:{mcid}は存在しません。もう一度確認してください。")
        else:
            await ctx.send("貴方のuuidは認証済みです。1アカウントにつき申請できるmcid/uuidは一つです。", hidden=True)

    @cog_ext.cog_slash(name="cs",
                       guild_ids=guild_id,
                       description="スタック表記⇔数字表記の相互変換が可能です。How to use: !cs [検索語] : ex.!cs 128 / !cs 8st+23 / !cs 9LC+82st+1",
                       options=[
                           create_option(
                               name="amount",
                               description="数字かStack表記に対応しています。Stack表記は、9LC+82st+1のように書いて下さい。",
                               option_type=3,
                               required=True
                           )
                       ],
                       permissions=permisson_verified
                       )
    async def cs(self, ctx, amount: str):
        # 数値かどうかで渡す関数を変更する
        if amount.isdecimal():
            await ctx.send(f"{amount}はスタック表記で{self.bot.stack_check_reverse(int(amount))}です。")
        else:
            if self.bot.stack_check(amount) is None:
                await ctx.send(f"入力した値が不正な値です。", hidden=True)
            else:
                await ctx.send(f"{amount}は整数値で{self.bot.stack_check(amount)}です。")

    @cog_ext.cog_slash(name="dm_setting",
                       guild_ids=guild_id,
                       description="botからのDMの受信設定を行えます。基本Trueとなっています。FalseにするとbotからDMが飛んでこなくなります",
                       options=[
                           create_option(
                               name="dm_boolean",
                               description="True: botからのDMを受信する / False: botからのDMを受信しない",
                               option_type=3,
                               required=True
                           )
                       ],
                       permissions=permisson_verified
                       )
    async def dm_setting(self, ctx, dm_boolean: str):
        # 数値かどうかで渡す関数を変更する
        if dm_boolean.lower() in ["true", "false"]:

            cur.execute(f"select dm_flag from user_data where user_id = {ctx.author.id}")

            dm_flag, = cur.fetchone()
            if (dm_boolean.lower() == "true" and dm_flag) or (dm_boolean.lower() == "false" and (not dm_flag)):
                await ctx.send("既に設定された値に変更されています。")
                return

            cur.execute(f"update user_data set dm_flag = {dm_boolean} where user_id = {ctx.author.id}")
            db.commit()

            if dm_boolean.lower() == "true":
                await ctx.send("botからのDMを受け取る設定にしました。", hidden=True)
            else:
                await ctx.send("botからのDMを拒否する設定にしました。", hidden=True)

        else:
            await ctx.send("設定の値が違います。以下のように設定してください。 ``!dm_setting True/False``", hidden=True)


def setup(bot):
    bot.add_cog(Message(bot))

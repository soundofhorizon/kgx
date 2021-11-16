from discord.ext import commands
import discord


class MemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            role = discord.utils.get(member.guild.roles, name="bot")
            await member.add_roles(role)
            return

        newcomer = discord.utils.get(member.guild.roles, name="新人")
        reported = discord.utils.get(member.guild.roles, name="MCID報告済み")

        self.bot.cur.execute("SELECT COUNT(*) FROM user_data WHERE user_id = %s", (member.id,))
        if self.bot.cur.fetchone()[0]:
            await member.add_roles(reported)
        else:
            await member.add_roles(newcomer)


def setup(bot):
    bot.add_cog(MemberJoin(bot))

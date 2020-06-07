from discord.ext import commands
import discord


class MemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.author.bot:
            role = discord.utils.get(member.guild.roles, name="bot")
            await member.add_roles(role)
            return

        role = discord.utils.get(member.guild.roles, name="新人")
        await member.add_roles(role)


def setup(bot):
    bot.add_cog(MemberJoin(bot))
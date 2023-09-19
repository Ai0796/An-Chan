from embeds.OpenSlotsEmbed import OpenSlotsEmbed
from discord.ext import commands


class Toyaify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="toyaify", description="Turns the bot into Toya")
    async def toyaify(self, ctx):
        with open('profiles/Toya.png', 'rb') as f:
            pfp = f.read()
        guild = ctx.guild

        self.bot.config.setRequestType(guild.id, 'Toya')

        await guild.me.edit(nick='冬弥くん')
        await ctx.respond('The bot is now Toya in this server')


def setup(bot):
    bot.add_cog(Toyaify(bot))

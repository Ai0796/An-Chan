from embeds.OpenSlotsEmbed import OpenSlotsEmbed
from discord.ext import commands


class Lemonadeify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="lemonadeify", description="Turns the bot into one compatible with Lemonade")
    async def lemonadify(self, ctx):
        guild = ctx.guild

        self.bot.config.setRequestType(guild.id, 'Lemonade')

        await guild.me.edit(nick='Lemonade')
        await ctx.respond('The bot is now Lemonade in this server')


def setup(bot):
    bot.add_cog(Lemonadeify(bot))
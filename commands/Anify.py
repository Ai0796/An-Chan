from embeds.OpenSlotsEmbed import OpenSlotsEmbed
from discord.ext import commands


class Anify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="anify", description="Turns the bot into An")
    async def anify(self, ctx):
        guild = ctx.guild

        self.bot.config.setRequestType(guild.id, 'An')

        await guild.me.edit(nick='杏ちゃん')
        await ctx.respond('The bot is now An')


def setup(bot):
    bot.add_cog(Anify(bot))
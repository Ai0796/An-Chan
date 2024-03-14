from embeds.OpenSlotsEmbed import OpenSlotsEmbed
from discord.ext import commands


class Ai2ify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="ai2ify", description="Turns the bot into one compatible with Ai2")
    async def ai2ify(self, ctx):
        guild = ctx.guild

        self.bot.config.setRequestType(guild.id, 'Ai2')

        await guild.me.edit(nick='杏ちゃん')
        await ctx.respond('The bot is now An2 in this server')


def setup(bot):
    bot.add_cog(Ai2ify(bot))
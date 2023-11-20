from embeds.OpenSlotsEmbed import OpenSlotsEmbed
from scripts.getCurrentEvent import getCurrentEvent
from discord.ext import commands
import discord


class ManualCheckIn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="manualcheckin", description="Manually runs check in, run this at :50")
    async def manualCheckIn(self, ctx):
        await self.bot.checkInServer(ctx.guild.id, True)
        await ctx.respond("Manual Check In Sent")


def setup(bot):
    bot.add_cog(ManualCheckIn(bot))

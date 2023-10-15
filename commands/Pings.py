from scripts.getCurrentEvent import getCurrentEvent
from discord.ext import commands
import discord
import time
from embeds.PingsEmbed import PingsEmbed

class Pings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="pings", description="Gets all pings for the")
    async def hours(self, ctx):
        start = time.time()

        profile = self.bot.getProfile(ctx.guild.id)
        sheetId = self.bot.config.getSheetId(ctx.guild.id)

        if sheetId == None:
            await ctx.respond('No sheet set for this server')
            return

        await ctx.defer()
        creds = profile.refreshCreds()
        event = getCurrentEvent()
        data = await profile.getPings(creds, sheetId, event)

        timestamps = [x * 3600 + int(event['startAt']/1000)
                      for x in range(len(data))]
        days = [int(event['startAt']/1000 - 3600 * 15)]
        while days[-1] < event['rankingAnnounceAt']/1000:
            days.append(days[-1] + 86400)

        days.append(days[-1] + 86400)

        timestamps = []

        timestamp = int(event['startAt']/1000)
        while timestamp < days[-1]:
            timestamps.append(timestamp)
            timestamp += 3600
            
        data = [data[timestamp] for timestamp in data if timestamp in timestamps]

        indexes = [0] + [i for i, x in enumerate(timestamps) if x in days]
        view = PingsEmbed(indexes, timestamps, data,
                              int(event['startAt']/1000))

        view.set_message(await ctx.edit(embed=view.generateEmbed(), view=view))

def setup(bot):
    bot.add_cog(Pings(bot))

from scripts.getCurrentEvent import getCurrentEvent
from discord.ext import commands
import discord
import time
from embeds.PingsEmbed import PingsEmbed
from datetime import datetime
from pytz import timezone

class Pings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="pings", description="Gets all pings for the")
    async def hours(self, ctx):
        start = time.time()

        profile = self.bot.getProfile(ctx.guild.id)
        sheetId = await self.bot.config.getSheetId(ctx.guild.id)

        if sheetId == None:
            await ctx.respond('No sheet set for this server')
            return

        await ctx.defer()
        creds = profile.refreshCreds()
        event = getCurrentEvent()
        data = await profile.getPings(creds, sheetId, event)
        
        firstTimestamp = min(data.keys())

        timestamps = [x * 3600 + firstTimestamp
                      for x in range(len(data))]
        
        startDate = datetime.fromtimestamp(firstTimestamp)
        startDate = startDate.astimezone(timezone('America/Los_Angeles'))
        startDate = startDate.replace(hour=0, minute=0, second=0, microsecond=0) ## Set to midnight
        startDate = int(startDate.timestamp())
        
        days = [startDate]
        while days[-1] < max(timestamps):
            days.append(days[-1] + 86400)

        days.append(days[-1] + 86400)

        timestamps = []

        timestamp = int(startDate)
        while timestamp < max(data.keys()):
            timestamps.append(timestamp)
            timestamp += 3600
            
        data = [data[timestamp] if timestamp in data else [] for timestamp in timestamps]
        indexes = [0] + [i for i, x in enumerate(timestamps) if x in days and i != 0] + [len(timestamps) - 1]
        
        view = PingsEmbed(indexes, timestamps, data, firstTimestamp)

        view.set_message(await ctx.edit(embed=view.generateEmbed(), view=view))

def setup(bot):
    bot.add_cog(Pings(bot))

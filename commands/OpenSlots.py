from discord.ext import commands
from scripts.getCurrentEvent import getCurrentEvent
from embeds.OpenSlotsEmbed import OpenSlotsEmbed

class OpenSlots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
            
    @commands.slash_command(name="openslots", description="Gets the number of open slots for the current event")
    async def openSlots(self, ctx):

        await ctx.defer()

        profile = self.bot.getProfile(ctx.guild.id)
        sheetId = self.bot.config.getSheetId(ctx.guild.id)

        if sheetId == None:
            await ctx.edit('No sheet set for this server')
            return

        creds = profile.refreshCreds()

        eventData = getCurrentEvent()

        data, event = await profile.getAllOpenSlots(creds, sheetId, eventData)

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

        indexes = [0] + [i for i, x in enumerate(timestamps) if x in days]
        view = OpenSlotsEmbed(indexes, timestamps, data, int(event['startAt']/1000))

        view.set_message(await ctx.edit(embed=view.generateEmbed(), view=view))


def setup(bot):
    bot.add_cog(OpenSlots(bot))

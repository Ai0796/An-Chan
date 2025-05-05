from discord.ext import commands
from scripts.getCurrentEvent import getCurrentEvent
from embeds.OpenSlotsEmbed import OpenSlotsEmbed
from discord import Option, SlashCommandOptionType
from datetime import datetime, timezone
import pytz

class OpenSlots(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
            
    @commands.slash_command(name="openslots", description="Gets the number of open slots for the current event")
    async def openSlots(self, ctx, standby: Option(
            SlashCommandOptionType.boolean,
            description="show standby hours",
            default=False)
    ):
        await ctx.defer()

        profile = self.bot.getProfile(ctx.guild.id)
        sheetId = await self.bot.config.getSheetId(ctx.guild.id)

        if sheetId == None:
            await ctx.edit('No sheet set for this server')
            return

        creds = profile.refreshCreds()

        eventData = getCurrentEvent()

        data, event = await profile.getAllOpenSlots(creds, sheetId, eventData)

        timestamps = [x * 3600 + int(event['startAt']/1000)
                    for x in range(len(data))]
        
        start = datetime.fromtimestamp(int(event['startAt']/1000))
        start = start.astimezone(pytz.timezone('America/Los_Angeles'))
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        start = start.astimezone(timezone.utc)
        
        days = [int(start.timestamp())]
        while days[-1] < event['rankingAnnounceAt']/1000:
            days.append(days[-1] + 86400)
            
        days.append(days[-1] + 86400)
        
        timestamps = []
        
        timestamp = int(event['startAt']/1000)
        while timestamp < days[-1]:
            timestamps.append(timestamp)
            timestamp += 3600

        indexes = [0] + [i for i, x in enumerate(timestamps) if x in days and i != 0]
        view = OpenSlotsEmbed(indexes, timestamps, data, int(event['startAt']/1000), standby)

        view.set_message(await ctx.edit(embed=view.generateEmbed(), view=view))


def setup(bot):
    bot.add_cog(OpenSlots(bot))

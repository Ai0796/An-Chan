from discord.ext import commands
import time
from embeds.CheckInButtons import CheckInButtons

class ViewCheckIn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="viewcheckin", description="Previews the next check in message")
    async def viewcheckin(self, ctx):
        """Previews the next check in message"""

        await ctx.defer(ephemeral=True)

        profile = self.bot.getProfile(ctx.guild.id)
        sheetId = self.bot.config.getSheetId(ctx.guild.id)

        if sheetId == None:
            await ctx.respond('No sheet set for this server', ephemeral=True)
            return

        creds = profile.refreshCreds()
        data = await profile.main(creds, sheetId=sheetId)

        timestamps = [key for key in data.keys()]
        timestamp = int(time.time())

        index = min(self.bot.getNextIndex(timestamps, timestamp),
                    len(timestamps) - 1)
        
        channelID = self.bot.config.getCheckInChannel(ctx.guild.id)

        if len(timestamps) == 0 or timestamp > timestamps[-1]:
            await ctx.followup.send('No Check Ins Found', ephemeral=True)
            return
        for i, roomData in enumerate(data[timestamps[index]].checkIns):
            view = CheckInButtons()
            await view.asyncinit(roomData, timestamps[index], i + 1, self.bot.checkInPrompts[ctx.guild.id], True)
            if timestamp + 2700 < timestamps[index]:
                await ctx.followup.send(f'Next scheduled hour in Room {i + 1} <t:{timestamps[index]}:R>',
                                        embed=view.comingUp(),
                                        ephemeral=True)
                continue
            if len(view.users) == 0:
                await ctx.followup.send(f'No room changes next hour in room {i+1}',
                                        ephemeral=True)
                continue
            await ctx.followup.send(embed=view.generateEmbed(), ephemeral=True)
            
        if channelID == None:
            await ctx.followup.send('**ALERT** No check-in channel set for the server', ephemeral=True)


def setup(bot):
    bot.add_cog(ViewCheckIn(bot))

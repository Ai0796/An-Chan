from scripts.getCurrentEvent import getCurrentEvent
from discord.ext import commands
import discord
import time
from bisect import bisect_left

class Hours(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="hours", description="Gets your scheduled hours or the hours of a specified user")
    async def hours(self, ctx,
                    user: discord.Option(
                        discord.SlashCommandOptionType.user,
                        required=False,
                        description="A user to get the hours of"
                    )
                    ):
        start = time.time()
        if user is None:
            user = ctx.author

        profile = self.bot.getProfile(ctx.guild.id)
        sheetId = self.bot.config.getSheetId(ctx.guild.id)

        if sheetId == None:
            await ctx.respond('No sheet set for this server')
            return

        await ctx.defer()
        creds = profile.refreshCreds()
        event = getCurrentEvent()
        data = await profile.getUserVals(creds, sheetId, user.id, event)

        eventStart = int(event['startAt']/1000)
        timestamps = [x * 3600 + eventStart for x in range(len(data))]

        index = bisect_left(timestamps, start - 3600)

        timestamps = timestamps[index:]
        data = data[index:]

        returnStr = ''

        i = 0

        combinedTimes = []

        while i < len(data) - 1:
            j = i + 1

            currentTime = data[i]
            nextTime = data[j]
            if currentTime < 0:
                i += 1
                continue
            while currentTime == nextTime and nextTime >= 0:
                j += 1
                nextTime = data[j]

            combinedTimes.append((i, j - i))
            i = j

        HOUR = 3600

        for i in combinedTimes:
            room = data[i[0]]
            if room < 0:
                continue
            startUnixTime = int(timestamps[i[0]])
            endUnixTime = int(startUnixTime + i[1] * HOUR)
            startTimestamp = f'<t:{startUnixTime}:D> <t:{startUnixTime}:t>'
            endTimestamp = f'<t:{endUnixTime}:D> <t:{endUnixTime}:t>'

            returnStr += f'`G{room + 1}` - {startTimestamp} to {endTimestamp}\r'

        if returnStr != '':
            embed = discord.Embed(
                title=f'{user.display_name}\'s hours', description=returnStr, color=0x00ff00)
            await ctx.respond(embeds=[embed])
        else:
            embed = discord.Embed(
                title=f'{user.display_name} has no hours scheduled', color=0x00ff00)
            await ctx.respond(embeds=[embed])

        elapsed_time = time.time() - start
        print('/hours Execution time:', elapsed_time, 'seconds')


def setup(bot):
    bot.add_cog(Hours(bot))

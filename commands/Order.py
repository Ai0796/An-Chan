from discord.ext import commands
import time
from embeds.OrderEmbed import OrderEmbed
from discord import File


class Order(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="order", description="Get current order from a hyperspecific sheet")
    async def order(self, ctx):

        start = time.time()
        
        await ctx.defer()

        profile = self.bot.getProfile(ctx.guild.id)
        sheetId = await self.bot.config.getSheetId(ctx.guild.id)

        if sheetId == None:
            await ctx.edit('No sheet set for this server')
            return

        creds = profile.refreshCreds()
        data = await profile.main(creds, sheetId)

        if data is None:
            await ctx.edit('No Orders Found or Error occured, please try again later.')
            return

        timestamp = int(time.time())
        timestamps = [key for key in data]

        index = min(self.bot.getNextIndex(timestamps, timestamp - 2700),
                    len(timestamps) - 1)

        if len(timestamps) == 0 or timestamp > timestamps[-1] + 3600:
            await ctx.edit('No Orders Found')
            return
        
        runners = await self.bot.config.getRunners(str(ctx.guild.id))

        view = OrderEmbed(data, timestamps, index, runners)
        view.generateEmbed(timestamps[index])

        if view.file:
            await ctx.edit(embeds=view.generateEmbed(timestamps[index]), view=view, 
                files=[view.file])
        else:
            await ctx.edit(embed=view.generateEmbed(timestamps[index]), view=view)
            
        view.message = ctx

        elapsed_time = time.time() - start
        print('Execution time:', elapsed_time, 'seconds')


def setup(bot):
    bot.add_cog(Order(bot))
from discord.ext import commands
import time
from embeds.OrderEmbed import OrderEmbed


class Order(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="order", description="Get current order from a hyperspecific sheet")
    async def order(self, ctx):

        start = time.time()

        profile = self.bot.getProfile(ctx.guild.id)
        sheetId = self.bot.config.getSheetId(ctx.guild.id)

        if sheetId == None:
            await ctx.respond('No sheet set for this server')
            return

        await ctx.defer()
        creds = profile.refreshCreds()
        data = await profile.main(creds, sheetId)

        if data is None:
            await ctx.respond('No Orders Found or Error occured, please try again later.')
            return

        timestamp = int(time.time())
        timestamps = [key for key in data]

        index = min(self.bot.getNextIndex(timestamps, timestamp - 2700),
                    len(timestamps) - 1)

        if len(timestamps) == 0 or timestamp > timestamps[-1] + 3600:
            await ctx.respond('No Orders Found')
            return

        view = OrderEmbed(data, timestamps, index)

        await ctx.edit(embed=view.generateEmbed(timestamps[index]), view=view)
        view.message = ctx

        elapsed_time = time.time() - start
        print('Execution time:', elapsed_time, 'seconds')


def setup(bot):
    bot.add_cog(Order(bot))

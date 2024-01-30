from discord.ext import commands
from discord import default_permissions
from embeds.StandbyButtons import StandbyButtons

class Standby(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="standby", description="Creates a standby queue in this channel")
    @default_permissions(manage_messages=True)
    async def removecheckin(self, ctx):

        embed = StandbyButtons()

        await ctx.respond(embed=embed.generateEmbed(), view=embed)

    @removecheckin.error
    async def removecheckin_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You don't have permission to do that", ephemeral=True)


def setup(bot):
    bot.add_cog(Standby(bot))

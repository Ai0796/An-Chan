from discord.ext import commands
from discord.ext.commands import has_permissions

class RemoveCheckIn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @has_permissions(manage_messages=True)
    @commands.slash_command(name="removecheckin", description="Removes the check in channel")
    async def removecheckin(self, ctx):

        self.bot.config.setCheckInChannel(ctx.guild.id, None)

        await ctx.respond("Check In Channel removed, use /changecheckin to re-enable check-ins", ephemeral=True)

    @removecheckin.error
    async def removecheckin_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You don't have permission to do that", ephemeral=True)


def setup(bot):
    bot.add_cog(RemoveCheckIn(bot))

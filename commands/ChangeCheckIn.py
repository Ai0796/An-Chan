from discord.ext import commands
from discord import default_permissions

class ChangeCheckIn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="changecheckin", description="Changes the channel the bot uses for checkins")
    @default_permissions(manage_messages=True)
    async def changecheckin(self, ctx):
        """Changes the check in channel"""
        channel = str(ctx.channel.id)
        
        self.bot.config.setCheckInChannel(ctx.guild.id, channel)

        await ctx.respond("Check In Channel changed to " + channel, ephemeral=True)
        
    @changecheckin.error
    async def changecheckin_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You don't have permission to do that", ephemeral=True)


def setup(bot):
    bot.add_cog(ChangeCheckIn(bot))

from discord.ext import commands
from discord import default_permissions, Option, SlashCommandOptionType
import discord

class Manager(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
    manager = discord.SlashCommandGroup('manager', 
                                      'Commands related to the manager ping',
                                      checks=[commands.has_permissions(manage_messages=True)])

    @manager.command(name='channel', description='Changes the manager channel')
    @default_permissions(manage_messages=True)
    async def changeManagerChannel(self, ctx):
        """Changes the manager in channel"""
        if not ctx.channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.respond("An cannot message in this channel, please change permissions or use a different channel", ephemeral=True)
            return
        
        channel = str(ctx.channel.id)
        
        self.bot.config.setManagerCheckInChannel(ctx.guild.id, channel)

        await ctx.respond(f"Manage Ping Channel changed to <#{channel}>", ephemeral=True)
        
    @changeManagerChannel.error
    async def changecheckin_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You don't have permission to do that", ephemeral=True)
            
    @manager.command(name='role', description='Changes the manager role')
    @default_permissions(manage_messages=True)
    async def changeManagerRole(self, ctx, role: Option(
        SlashCommandOptionType.role,
        description="The role to ping"
    )):
        """Changes the manager in channel"""
        role = f'<@&{role.id}>'
        
        self.bot.config.setManagerPing(ctx.guild.id, role)

        await ctx.respond("Manage Ping Role changed to " + role, ephemeral=True)


def setup(bot):
    bot.add_cog(Manager(bot))
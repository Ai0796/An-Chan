from embeds.OpenSlotsEmbed import OpenSlotsEmbed
from discord.ext import commands
import discord

class Runner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    runner = discord.SlashCommandGroup('runner', 
        'Commands related to the runner',
        checks=[commands.has_permissions(manage_messages=True)])
    
    @runner.command(name="add", description="Adds the runner to list of runners")
    async def add(self, ctx, user: discord.Option(
        discord.SlashCommandOptionType.string,
        required=True,
        description="Name to set as runner, this hides their ISV/BP"
    )):
        
        guildid = str(ctx.guild.id)

        runners = self.bot.config.addRunner(guildid, user)

        await ctx.respond(f'Runner added: {user}')
        
        runnerStr = '```\n' + '\n'.join(runners) + '```'
        await ctx.followup.send(runnerStr)
        
    @runner.command(name="remove", description="Removes the runner from list of runners")
    async def remove(self, ctx, user: discord.Option(
        discord.SlashCommandOptionType.string,
        required=True,
        description="Name to remove as runner"
    )):
        
        guildid = str(ctx.guild.id)

        runners = self.bot.config.removeRunner(guildid, user)

        await ctx.respond(f'Runner removed: {user}')
        
        runnerStr = '```\n' + '\n'.join(runners) + '```'
        await ctx.followup.send(runnerStr)
        
    @runner.command(name="list", description="Lists the runners")
    async def list(self, ctx):
        guildid = str(ctx.guild.id)
        runners = self.bot.config.getRunners(guildid)
        
        runnerStr = '```\n' + '\n'.join(runners) + '```'
        await ctx.respond(runnerStr)

def setup(bot):
    bot.add_cog(Runner(bot))

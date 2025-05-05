from scripts.getCurrentEvent import getCurrentEvent
from discord.ext import commands
import discord
from embeds.FillersEmbed import FillersEmbed

from discord import default_permissions, Option, SlashCommandOptionType

class Fillers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    filler = discord.SlashCommandGroup('filler', 
            'Commands related to fillers',
            checks=[commands.has_permissions(manage_messages=True, manage_roles=True)])

    @filler.command(name='list', description='Lists out all Fillers')
    @default_permissions(manage_messages=True, manage_roles=True)
    async def view(self, ctx, role: Option(
        SlashCommandOptionType.role,
        description="The role to give",
        required=True
    )):

        profile = self.bot.getProfile(ctx.guild.id)
        sheetId = await self.bot.config.getSheetId(ctx.guild.id)

        if sheetId == None:
            await ctx.respond('No sheet set for this server')
            return

        await ctx.defer()
        creds = profile.refreshCreds()
        event = getCurrentEvent()
        data = await profile.getPings(creds, sheetId, event)
        
        allPings = set()
        for key in data:
            for user in data[key]:
                allPings.add(user)
        
        view = FillersEmbed(allPings, role)

        view.set_message(await ctx.edit(embed=view.generateEmbed(), view=view))

    @view.error
    async def view_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You don't have permission to do that", ephemeral=True)

def setup(bot):
    bot.add_cog(Fillers(bot))

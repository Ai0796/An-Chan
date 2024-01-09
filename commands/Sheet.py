from discord.ext import commands
import discord

class Sheet(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
    sheet = discord.SlashCommandGroup('sheet', 
                                      'Commands related to the sheet',
                                      checks=[commands.has_permissions(manage_messages=True)])

    @sheet.command(name='change', description='Changes the sheet the bot uses')
    async def change(self, ctx, url: discord.Option(
        discord.SlashCommandOptionType.string,
        description="The sheet URL or sheet ID"
    )):
        """Changes the sheet the bot uses"""
        if '/' in url:
            url = url.split('/')
            index = url.index('d')
            url = url[index + 1]
        url = url.strip()

        if url == '':
            self.bot.config.setSheetId(ctx.guild.id, None)
        else:
            self.bot.config.setSheetId(ctx.guild.id, url)

        await ctx.respond("Sheet id changed to " + url, ephemeral=True)


    @change.error
    async def change_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You don't have permission to do that", ephemeral=True)


def setup(bot):
    bot.add_cog(Sheet(bot))

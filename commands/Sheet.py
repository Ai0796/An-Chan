from discord.ext import commands
import discord

class Sheet(commands.Cog):
    
    ID_DIC = {
        "An_template": "An",
        "Ai2_Template": "Ai2"
    }
    
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
            await ctx.respond("Sheet id removed", ephemeral=True)
            return

        self.bot.config.setSheetId(ctx.guild.id, url)
        profile = self.bot.getProfile(ctx.guild.id)
        sheetTemplateID = await profile.getID(profile.refreshCreds(), url)
        
        await ctx.respond("Sheet id changed to " + url, ephemeral=True)
        
        if sheetTemplateID == None or sheetTemplateID not in self.ID_DIC:
            sendStr = "Sheet not recognized, make sure you're using a compatible sheet listed below and that commands work properly:\n" + \
                "- [Universal Schedule (Recommended)](<https://docs.google.com/spreadsheets/d/1wVstbFdtUqCfKRixVm2ZvvJBg8wlRuiBhT-9dnUA0X4/copy?usp=sharing>)\n" + \
                "- [ET Schedule Marathon](<https://docs.google.com/spreadsheets/d/1bJwD4zV1e8Kxbth1iD2GC8z6T0_EeUrblaT7vi7A4aA/copy?usp=sharing>)\n" + \
                "- [PT Schedule Marathon](<https://docs.google.com/spreadsheets/d/1r5EeZ-Kz2Sg-R3zOYCusuTMPPNXlgBprT3ZOVINyMMI/copy?usp=sharing>)\n" + \
                "- [ET Schedule CC](<https://docs.google.com/spreadsheets/d/1yCN0G7ZYGLSYkA_Jk3VOGz8hsx9eURkXKJoBn8c2SO0/copy?usp=sharing>)\n" + \
                "- [PT Schedule CC](<https://docs.google.com/spreadsheets/d/1QA85weZ92sulNhSpHNO1udVGV9CjzQKBlJqM5Qm8JEc/copy?usp=sharing>)\n"
            await ctx.followup.send(sendStr, ephemeral=True)
            
        else:
            await ctx.followup.send(f'Sheet template recognized, automatically changed to {self.ID_DIC[sheetTemplateID]} profile', ephemeral=True)
            self.bot.config.setRequestType(ctx.guild.id, self.ID_DIC[sheetTemplateID])

    @change.error
    async def change_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You don't have permission to do that", ephemeral=True)


def setup(bot):
    bot.add_cog(Sheet(bot))

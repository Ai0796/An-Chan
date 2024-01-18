from discord.ext import commands
from discord import Embed

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="help", description="Gives instructions for use of bot")
    async def help(self, ctx):
        embed = Embed(
            title="Help", 
            description="Usage Instructions of bot.",
            color = 0x00BBDC
        )
        
        embed.add_field(
            name="Summary",
            value="This bot is used as a helper bot to assist in tiering in the game Project Sekai." +
            "It interfaces with a Google Sheet and allows automation of check ins, ordering, and open slots."
        )
        
        embed.add_field(
            name="Sheets",
            value="The bot uses a Google Sheet to store data. " +
            "The sheet must be set using `/sheet change [sheet id]`." +
            "Sample sheets for every event can be found below:\n" +
            "- [Universal Schedule (Recommended)](https://docs.google.com/spreadsheets/d/1wVstbFdtUqCfKRixVm2ZvvJBg8wlRuiBhT-9dnUA0X4/copy?usp=sharing)\n" +
            "- [ET Schedule Marathon](https://docs.google.com/spreadsheets/d/1bJwD4zV1e8Kxbth1iD2GC8z6T0_EeUrblaT7vi7A4aA/copy?usp=sharing)\n" +
            "- [PT Schedule Marathon](https://docs.google.com/spreadsheets/d/1r5EeZ-Kz2Sg-R3zOYCusuTMPPNXlgBprT3ZOVINyMMI/copy?usp=sharing)\n" +
            "- [ET Schedule CC](https://docs.google.com/spreadsheets/d/1yCN0G7ZYGLSYkA_Jk3VOGz8hsx9eURkXKJoBn8c2SO0/copy?usp=sharing)\n" + 
            "- [PT Schedule CC](https://docs.google.com/spreadsheets/d/1QA85weZ92sulNhSpHNO1udVGV9CjzQKBlJqM5Qm8JEc/copy?usp=sharing)\n"
        )
        
        secondEmbed = Embed(
            title="Help (cont.)",
            description="Usage Instructions of bot.",
            color = 0x00BBDC
        )
        
        secondEmbed.add_field(
            name="Setup",
            value="To setup the bot, there are 3 steps\n" +
            "1. Set the sheet using `/sheet change [sheet id]`\n" +
            "2. Set the check in channel using `/changecheckin` in the channel you want check in pings to be sent\n" +
            "3. Setup the sample sheet from above with your event"
        )
        
        secondEmbed.add_field(
            name="Commands",
            value="The bot has the following commands for managers:\n" +
            "- `/manualcheckin` - Used in case the check in doesn't work\n" +
            "- `/viewcheckin` - Previews the next check in message\n" +
            "- `/openslots` shows the open slots for a given day on the sheet\n" +
            "- `/hours` - Shows the hours signed up for a given user\n" +
            "- `/pings` - Gets all signed up users for a given day\n" +
            "- `/checkinprompt add` - Adds a prompt for the next check in message that will be sent\n" +
            "- `/manager channel` - Changes the channel the manager ping is sent in, the ping is sent 10 minutes after check in if there are missing users\n" +
            "- `/manager role` - Changes the role that is pinged in the manager ping\n"
        )

        await ctx.respond(embed=embed)
        await ctx.followup.send(embed=secondEmbed)

def setup(bot):
    bot.add_cog(Help(bot))
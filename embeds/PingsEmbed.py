import discord
from bisect import bisect_left
import time


class PingsEmbed(discord.ui.View):

    def __init__(self, dayindexes, timestamps, users, start):
        super().__init__(timeout=30)
        self.dayindexes = dayindexes
        self.timestamps = timestamps
        self.users = users
        self.start = start
        self.day = min(bisect_left(self.dayindexes, bisect_left(
            self.timestamps, time.time())), len(self.dayindexes) - 2)
        self.message = None

    def set_message(self, message):
        self.message = message

    def generateEmbed(self):

        HOUR = 3600

        timestamps = self.timestamps[self.dayindexes[self.day]:self.dayindexes[self.day + 1]]
        data = self.users[self.dayindexes[self.day]
            :self.dayindexes[self.day + 1]]
        returnStr = ''
        
        userSet = set()

        for users in data:
            userSet.update(users)
            
        returnStr += f'<t:{timestamps[0]}:D> <t:{timestamps[0]}:t> to <t:{timestamps[-1]}:D> <t:{timestamps[-1]}:t>'
        
        returnStr += '\r```'
            
        for user in userSet:
            returnStr += f'<@{user}>'
            
        returnStr += '```'

        if userSet:
            embed = discord.Embed(
                title=f'Pings Day {self.day + 1}', 
                description=returnStr, 
                color = 0x00BBDC)
        else:
            embed = discord.Embed(
                title=f'Pings Day {self.day + 1}', 
                description='No found Users for the day', 
                color = 0x00BBDC)

        return embed

    async def on_timeout(self):
        embed = self.generateEmbed()
        await self.message.edit(embed=embed, view=None)

    @discord.ui.button(label='Previous Day', style=discord.ButtonStyle.primary, emoji='🌇')
    async def previousDay(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.day = max(self.day - 1, 0)
        await interaction.response.edit_message(embed=self.generateEmbed(), view=self)

    @discord.ui.button(label='Next Day', style=discord.ButtonStyle.primary, emoji='🌄')
    async def nextDay(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.day = min(self.day + 1, len(self.dayindexes) - 2)
        await interaction.response.edit_message(embed=self.generateEmbed(), view=self)
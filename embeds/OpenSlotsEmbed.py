import discord
from bisect import bisect_left
import time

class OpenSlotsEmbed(discord.ui.View):
    
    def __init__(self, dayindexes, timestamps, slots, start):
        super().__init__(timeout=30)
        self.dayindexes = dayindexes
        self.timestamps = timestamps
        self.slots = slots
        self.start = start
        self.day = min(bisect_left(self.dayindexes, bisect_left(self.timestamps, time.time())), len(self.dayindexes) - 2)
        self.message = None
        
    def set_message(self, message):
        self.message = message
        
    def generateEmbed(self):
        
        HOUR = 3600
        
        data = self.slots[self.dayindexes[self.day]:self.dayindexes[self.day + 1]]
        timestamps = self.timestamps[self.dayindexes[self.day]:self.dayindexes[self.day + 1]]
    
        returnStr = ''
        
        for slots, timestamp in zip(data, timestamps):
            if slots > 0:
                startUnixTime = int(timestamp)
                endUnixTime = int(startUnixTime + HOUR)
                startTimestamp = f'<t:{startUnixTime}:D> <t:{startUnixTime}:t>'
                endTimestamp = f'<t:{endUnixTime}:t>'
                
                hourIndex = round((startUnixTime - self.start) / HOUR)
        
                returnStr += f'H{hourIndex + 1}: {startTimestamp} to {endTimestamp} `+{slots}`\r'
            
        if returnStr != '':
            embed = discord.Embed(title=f'Open Slots Day {self.day + 1}', description=returnStr, color=0x00ff00)
        else:
            embed = discord.Embed(title=f'Open Slots Day {self.day + 1}', description='No open slots on this day', color=0x00ff00)
            
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
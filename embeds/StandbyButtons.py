import random
import discord
from discord.ext import commands
import re
import asyncio

class StandbyButtons(discord.ui.View):

    def __init__(self):
        
        super().__init__(timeout=None)
        self.users = set()

    async def on_timeout(self):
        embed = self.generateEmbed()
        await self.message.edit(embed=embed, view=None)
        
        if self.managerRole is None or self.managerChannel is None or len(self.users) == 0:
            return
        
        if len(self.checkedIn) < len(self.users):
            channel = commands.Bot.get_channel(self.bot, int(self.managerChannel))
            await channel.send(f'Room {self.room} has {len(self.users) - len(self.checkedIn)} missing check ins {self.managerRole}')
        
    def addCtx(self, ctx):
        self.ctx = ctx

    def getPings(self):
        pingStr = '```'

        for user in self.users:
            pingStr += f'<@{user}>\n'
            
        pingStr += '```'

        return pingStr

    def generateEmbed(self):

        embedStr = ''
        
        for user in self.users:
            embedStr += f'- <@{user}>\n'

        return discord.Embed(
            title=f'Standby List', 
            description=embedStr, 
            color = 0x00BBDC)

    @discord.ui.button(label='Add', style=discord.ButtonStyle.primary, emoji='🌸')
    async def add(self, button: discord.ui.Button, interaction: discord.Interaction):

        self.users.add(interaction.user.id)
        await interaction.response.edit_message(embed=self.generateEmbed(), view=self)
        
    @discord.ui.button(label='Remove', style=discord.ButtonStyle.red, emoji='🏵️')
    async def remove(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id in self.users:
            self.users.remove(interaction.user.id)
        await interaction.response.edit_message(embed=self.generateEmbed(), view=self)
        
    @discord.ui.button(label='Pings', style=discord.ButtonStyle.primary, emoji='🔔')
    async def pings(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message(self.getPings(), ephemeral=True)
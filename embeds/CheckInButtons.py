import random
import discord
from discord.ext import commands
import re
import asyncio

class CheckInButtons(discord.ui.View):
    
    checkInSections = [
        'Please check in or Kohane will cry.',
        'Make sure you pray to Kohane and check in.',
        'Kohane is sad that you haven\'t checked in yet.',
        # 'Pocket put down the 2nd phone please.',
        # 'Hi Lemo Hey Lemo Hi Lemo Hey Lemo.',
        # 'Hi Annie Hey Annie Hi Annie Hey Annie.',
        'Saa anyo anyo kocchi oide.',
        'nyaa~',
        'It\'s ebi slapping time.',
        'Ai0 is tired of writing random messages for this.',
        'Did you shower your leader yet?',
        'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA',
    ]
    
    proudQuotes = [
        "Congrats on checking in everyone!",
        "Did you remember to pray to Kohane?",
        "Don't grief runner",
        "Everyone check your leads",
        "Have you considered just filling the next 72 hours?"
    ]

    def __init__(self):
        
        super().__init__(timeout=300)
        
    async def asyncinit(self, bot, checkInMessage, timestamps, room, prompts, managerChannel, managerPing, test=False):
        self.bot = bot
        self.message = checkInMessage
        self.timestamp = timestamps
        self.users = set()
        self.checkedIn = set()
        self.room = room
        self.ctx = None
        self.count = 0
        self.managerChannel = managerChannel
        self.managerRole = managerPing
        
        self.sentMessage = False
        
        if len(prompts) > 0:
            if test:
                self.quote = prompts[0]
            else:
                self.quote = prompts.pop(0)
        else:
            self.quote = self.checkInSections[random.randint(
                0, len(self.checkInSections) - 1)]
            
        self.quote += ' '

        result = re.findall(r'<@[0-9]*>', self.message)

        for user in result:
            self.users.add(user[2:-1])
            
        if len(self.users) == 0:
            return
        
        self.channel = re.findall(r'<#[0-9]*>', self.message)[0]

    async def on_timeout(self):
        embed = self.generateEmbed()
        await self.message.edit(embed=embed, view=None)
        
        if self.managerRole is None or self.managerChannel is None or len(self.users) == 0:
            return
        
        try:
            if len(self.checkedIn) < len(self.users):
                channel = commands.Bot.get_channel(self.bot, int(self.managerChannel))
                await channel.send(f'Room {self.room} has {len(self.users) - len(self.checkedIn)} missing check ins {self.managerRole}')
        except:
            pass
        
    def addCtx(self, ctx):
        self.ctx = ctx

    def pings(self):
        pingStr = ''

        for user in self.users:
            pingStr += f'<@{user}>\n'

        return pingStr

    def generateEmbed(self):
        
        if len(self.users) == 0:
            return discord.Embed(
                title=f'Coming Up (Room {self.room})', 
                description=self.quote + self.message, 
                color = 0x00BBDC)

        embedStr = ''

        embedStr += self.quote
        embedStr += f'Click the button or react to this message to check in, then go to room {self.channel} <t:{self.timestamp}:R>'

        embedStr += '\n\n'
        embedStr += f'{self.count} out of {len(self.users)} have checked in.\n\n'

        for user in self.users:
            if user in self.checkedIn:
                embedStr += f'Checked In: <@{user}>\n'
            else:
                embedStr += f'Not Checked In: <@{user}>\n'

        return discord.Embed(
            title=f'Check In (Room {self.room})', 
            description=embedStr, 
            color = 0x00BBDC)

    def comingUp(self):
        if len(self.users) == 0:
            return discord.Embed(
                title=f'Coming Up (Room {self.room})', 
                description=self.quote + self.message, 
                color = 0x00BBDC)

        embedStr = ''

        embedStr += self.quote
        embedStr += f'Room {self.channel} <t:{self.timestamp}:R>'

        embedStr += '\n\n'

        for user in self.users:
            embedStr += f'<@{user}>\n'

        return discord.Embed(
            title=f'Check In (Room {self.room})', 
            description=embedStr, 
            color = 0x00BBDC)
        
    async def sendRoomReminder(self):
        if not self.sentMessage and len(self.checkedIn) == len(self.users):
            try:
                self.sentMessage = True
                channelid = self.channel[2:-1]
                channel = self.bot.get_channel(int(channelid))
                quote = self.proudQuotes[random.randint(0, len(self.proudQuotes) - 1)]
                await channel.send(f'{quote}\n\nEveryone has checked in, just get in (unless a monitor says something else).')
            except:
                pass

    @discord.ui.button(label=f'Check In', style=discord.ButtonStyle.primary, emoji='🌸')
    async def checkIn(self, button: discord.ui.Button, interaction: discord.Interaction):

        if str(interaction.user.id) in self.users:
            self.count += 1
            self.checkedIn.add(str(interaction.user.id))
            
            await self.sendRoomReminder()
            
        await interaction.response.edit_message(embed=self.generateEmbed(), view=self)
        
    async def checkInReaction(self, user):
        if str(user.id) in self.users:
            self.count += 1
            self.checkedIn.add(str(user.id))
            
            await self.sendRoomReminder()
            
        await self.ctx.edit(embed=self.generateEmbed(), view=self)

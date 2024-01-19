import discord
from discord.ext import commands, tasks
import rapidjson
from datetime import datetime, timedelta
import time
import asyncio
from pytz import timezone
from Config import Config
from embeds.CheckInButtons import CheckInButtons
from glob import glob

import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

with open('config/config.json', 'r', encoding='utf8') as f:
    configData = rapidjson.load(f)

token = configData['token']

EVENTPATH = '../RoboNene/sekai_master/events.json'
DCSPATH = 'config/dcs.json'

# checkInMessages = []
# checkInPrompts = {}
DCs = {}

# config = Config()

DCCommands = discord.SlashCommandGroup('dc', 'Commands related to DCing')
    
from requestsTypes.ai0 import ai0
import requestsTypes.haikurequest as haikurequest
from requestsTypes.ai2 import ai2
    
class An(commands.Bot):
    
    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        
        self.checkIn.start()
        
        self.checkInMessages = []
        self.checkInPrompts = {}
        self.DCs = {}
        
        self.config = Config()
        
        self.DCCommands = discord.SlashCommandGroup('dc', 'Commands related to DCing')
        
        self.profiles = {
            "An": ai0('token.json'),
            "Toya": haikurequest,
            "Ai2": ai2('token.json')
        }
        
        with open(EVENTPATH, 'r', encoding='utf8') as f:
            self.eventData = rapidjson.load(f)
            
        with open(DCSPATH, 'r', encoding='utf8') as f:
            self.DCs = rapidjson.load(f)
    
    async def on_ready(self):
        for guild in bot.guilds:
            print(f'{guild.name} - {guild.id}')
            self.config.createServer(guild.id)
            self.checkInPrompts[guild.id] = []

        print('Starting bot...')
        
    def getProfile(self, serverid):
        return self.profiles[self.config.getRequestType(serverid)]
    
    def getNextIndex(self, timestamps, wantedTimestamp):
        index = 0
        for timestamp in timestamps:
            if wantedTimestamp < timestamp:
                return index
            else:
                index += 1

        return index
    
    async def on_reaction_add(self, reaction, user):
        message = reaction.message  # our embed
        for checkInMessage in self.checkInMessages:
            if checkInMessage.ctx.id == message.id:
                await checkInMessage.checkInReaction(user)

    async def checkInServer(self, serverid, manual=False):
        try:
            
            lastPing = self.config.getTime(serverid)
            if lastPing + 2700 > time.time() and not manual:
                return

            profile = self.getProfile(serverid)
            sheetId = self.config.getSheetId(serverid)

            if sheetId == None or sheetId.lower() == "none":
                return

            channelID = self.config.getCheckInChannel(serverid)

            if channelID == None:
                return

            channel = commands.Bot.get_channel(self, int(channelID))
            managerChannel, managerPing = self.config.getManagerCheckInChannel(serverid), self.config.getManagerPing(serverid)

            creds = profile.refreshCreds()
            data = await profile.main(creds, sheetId=sheetId)

            if data == None:
                return

            timestamps = [key for key in data.keys()]
            timestamp = int(time.time())

            index = min(self.getNextIndex(timestamps, timestamp),
                        len(timestamps) - 1)

            p = []

            if len(timestamps) == 0 or timestamp > timestamps[-1]:
                print('No Check Ins Found')
                return
            
            print('Checking in server ' + str(serverid))
            
            for i, roomData in enumerate(data[timestamps[index]].checkIns):
                view = CheckInButtons()
                await view.asyncinit(self, roomData, timestamps[index], i + 1, 
                                     self.checkInPrompts[int(serverid)], 
                                     managerChannel, managerPing)
                if timestamp + 2700 < timestamps[index]:
                    await channel.send(f'Next scheduled hour in Room {i + 1} <t:{timestamps[index]}:R>')
                    await channel.send(embed=view.comingUp())
                    continue
                if len(view.users) == 0:
                    await channel.send(f'No room changes next hour in room {i+1}')
                    continue
                ctx = await channel.send(view.pings(), embed=view.generateEmbed(), view=view)
                view.addCtx(ctx)
                self.checkInMessages.append(view)
                # p.append(view.managerPing())

            self.config.setLastPing(serverid, int(time.time()))
            await asyncio.gather(*p)
            
            
        except Exception as e:
            print(e)
            print('Error in check in ping')

            channelID = self.config.getCheckInChannel(serverid)

            if channelID == None:
                return
            print(serverid)
            try:
                await channel.send('Something went wrong with the check in ping')
            except Exception as e:
                print(e)

    @tasks.loop(hours=1)
    async def checkIn(self, loops=5):
        tz = timezone('America/New_York')
        for i in range(loops):
            print('Checking in at ' + str(datetime.now(tz)))

            processes = []

            for serverid in self.config.getServers():

                # Checks if the last update was more than 15 days ago
                if self.config.getTime(serverid) + 86400 * 15 > time.time():
                    processes.append(self.checkInServer(serverid))

            await asyncio.gather(*processes)
            
            await asyncio.sleep(60)

    @checkIn.before_loop
    async def waitUntilCheckIn(self):
        minute = 45
        await bot.wait_until_ready()
        now = datetime.now()
        future = datetime(now.year, now.month, now.day, now.hour, minute, 0, 0)
        if now.hour == now.hour and now.minute >= 45 and now.minute <= 55:
            await self.checkIn(55 - now.minute)
            
            ## reset date times since awaited
            now = datetime.now()
            future = datetime(now.year, now.month, now.day,
                              now.hour, minute, 0, 0)
        if now.hour >= now.hour and now.minute > minute:
            future += timedelta(hours=1)
        print('Sleeping for ' + str((future-now).seconds/60) + ' minutes')
        await asyncio.sleep((future-now).seconds)

    async def on_guild_join(self, guild):
        self.config.createServer(guild.id)
        self.checkInPrompts[guild.id] = []
    
# class CheckInButtons(CheckInButtons):
#     async def managerPing(self):
#         await asyncio.sleep(600)
#         if (self.room in checkInMessages):
#             checkInMessages.remove(self.room)
#         if len(self.checkedIn) < len(self.users):
#             channel = commands.Bot.get_channel(bot, CHANNEL_ID)
#             await channel.send(f'Room {self.room} has missing check ins.')

# @sheet.command(name='get', description='Gets the current sheet url')
# async def get(ctx):
#     """Gets the current sheet url"""
#     await ctx.respond('https://docs.google.com/spreadsheets/d/' + SHEETID + '/edit?usp=sharing')
    
def writeDCs():
    with open(DCSPATH, 'w') as f:
        try:
            rapidjson.dump(DCs, f)
        except:
            print('Error occured while writing DCs')
    
@DCCommands.command(name='add', description='Adds user to DC')
async def add(ctx, user: discord.Option(discord.SlashCommandOptionType.user, desciptions='the user to add to the DC list', required=False)):
    if user is None:
        user = ctx.author
        
    uid = str(user.id)
        
    if uid in DCs:
        DCs[uid].append(int(time.time()))
        
    else:
        DCs[uid] = [int(time.time())]
        
    for i in DCs[uid]:
        if time.time() - i > 3600 * 2:
            DCs[uid].remove(i)
        
    writeDCs()
    await ctx.respond(f'{user.display_name} has been added to the DC list, they have {len(DCs[uid])} DCs')
    
@DCCommands.command(name='list', description='Lists current rooms DC counts')
async def list(ctx):
    returnStr = ''
    
    for key in DCs.keys():
        for timestamp in DCs[key]:
            if time.time() - timestamp > 3600 * 2:
                DCs[key].remove(timestamp)
        if len(DCs[key]) == 0:
            del DCs[key]
            continue
        
    for key in DCs.keys():
        returnStr += f'<@{key}> `\t\t`{len(DCs[key])} DCs\n'
    
    if returnStr == '':
        returnStr = 'No DCs in the last two hours'
    
    embed = discord.Embed(title='DCs in last two hours', description=returnStr)
    
    writeDCs()
    await ctx.respond(embeds=[embed])

class RemindButtons(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=900)
        self.checkedIn = set()
        self.count = 0

        self.users = ['133693715398000640']

    async def on_timeout(self):
        embed = self.generateEmbed()
        await self.message.edit(embed=embed, view=None)

    def pings(self):
        pingStr = ''

        for user in self.users:
            pingStr += f'<@{user}>\n'

        return pingStr

    def generateEmbed(self):
        
        refilled = len(self.checkedIn) == len(self.users)
        if refilled:
            text = 'Congrats you refilled, /statistics just in case'
        else:
            text = 'ueueueueueueueueueueueueueueueueueueueue'

        return discord.Embed(title=f'HAVE YOU REFILLED ENERGY', description=text, color=discord.Color.blurple())
   
    @discord.ui.button(label=f'Refill', style=discord.ButtonStyle.primary, emoji='🌸')
    async def checkIn(self, button: discord.ui.Button, interaction: discord.Interaction):

        if str(interaction.user.id) in self.users:
            self.count += 1
            self.checkedIn.add(str(interaction.user.id))
        await interaction.response.edit_message(embed=self.generateEmbed(), view=self)

    async def checkInReaction(self, user):
        if str(user.id) in self.users:
            self.count += 1
            self.checkedIn.add(str(user.id))
        await self.ctx.edit(embed=self.generateEmbed(), view=self)
    
# @tasks.loop(minutes=20)
# async def remindPing():
#     channel = commands.Bot.get_channel(bot, int(HAIKU_REMIND_CHANNEL_ID))
#     view = RemindButtons()
    
#     await channel.send(view.pings(), embed=view.generateEmbed(), view=view)
    

# @remindPing.before_loop
# async def waitUntilPing():
#     minute = 40
#     await bot.wait_until_ready()
#     now = datetime.now()
#     future = datetime(now.year, now.month, now.day, now.hour, minute, 0, 0)
#     if now.hour >= now.hour and now.minute > minute:
#         future += timedelta(hours=1)
#     print('Sleeping for ' + str((future-now).seconds/60) + ' minutes until ping')
#     await asyncio.sleep((future-now).seconds)

from commands.Sheet import Sheet

if __name__ == "__main__":
    bot = An(command_prefix='/')
    for fp in glob('commands/*.py'):
        if fp.endswith('__init__.py'):
            continue
        print("Loading: ", fp.replace('/', '.')[:-3])
        bot.load_extension(fp.replace('/', '.')[:-3])
    bot.add_application_command(DCCommands)
    bot.activity = discord.Activity(name='with こはね', type=discord.ActivityType.playing)
    # remindPing.start()
    bot.run(token)

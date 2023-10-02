import random
import discord
from discord.ext import commands, tasks
import rapidjson
from datetime import datetime, timedelta
import time
import re
import asyncio
from requestsTypes.haikurequest import main, refreshCreds, getUserVals
import traceback
import aiohttp
from bisect import bisect_left
from embeds.CheckInButtons import CheckInButtons
from embeds.OpenSlotsEmbed import OpenSlots

bot = commands.Bot()

with open('config/configToya.json', 'r', encoding='utf8') as f:
    configData = rapidjson.load(f)

token = configData['token']

CHANNEL_ID = '1039473652640514049'
EMERGENCY_CHANNEL_ID = '422851664781770753'
# HAIKU_REMIND_CHANNEL_ID = '1033352019060199484'

checkInMessages = []

SHEETID = ''
with open('config/sheetId.txt', 'r') as f:
    SHEETID = f.read()

with open('config/events.json', 'r', encoding='utf8') as f:
    eventData = rapidjson.load(f)
    f.close()
    
class CheckInButtons(CheckInButtons):
    async def managerPing(self):
        await asyncio.sleep(600)
        if len(self.checkedIn) < len(self.users):
            channel = commands.Bot.get_channel(bot, int(EMERGENCY_CHANNEL_ID))
            await channel.send(f'Room {self.room} has missing check ins')
    
class EmbedButtons(discord.ui.View):
    def __init__(self, data, timestamps, index):

        super().__init__(timeout=60)
        self.timestamps = timestamps
        self.data = data
        self.index = index
        self.p1encore = False
        self.mobile = False
        self.roomIndex = 0
        self.team = 0

    async def on_timeout(self):
        embed = self.generateEmbed(self.timestamps[self.index])
        await self.message.edit(embed=embed, view=None)

    def generateEmbed(self, timestamp):

        orders = self.data[timestamp].getOrders()
        players = orders[min(self.roomIndex, len(orders) - 1)]
        if (self.team * 5 >= len(players)):
            self.team = 0
        players = players[self.team * 5: self.team * 5 + 5]
        p1encore = self.p1encore
        mobile = self.mobile

        EnvyOrder = [3, 2, 1, 4, 5]
        EncoreOrder = [3, 2, 4, 5]

        event = getCurrentEvent()
        if event != None:
            if event['id'] % 3 == 0:
                EnvyOrder = [2, 1, 4, 5, 3]
                EncoreOrder = [2, 4, 5, 3]

        runnerBP = 0
        encoreIndex = -1
        linkedOrder = []
        totalisv = sum([player.isv / 100.0 + 1.0 for player in players])
        avgbp = sum([player.bp for player in players]) / len(players)

        players.sort(key=lambda x: x.isv)

        for player in players:
            if ('event' in player.name.lower()):
                runnerBP = max(runnerBP, player.bp)

        for i in range(len(players)):
            player = players[i]

            if player.name == 'Lemo':
                encoreIndex = i

            if ('encore' in player.name.lower()):
                encoreIndex = i
                break

        if (not p1encore or encoreIndex == -1):
            for i in range(len(EnvyOrder)):
                linkedOrder.append([EnvyOrder[i], players[i]])
        else:
            encoreUser = players.pop(encoreIndex)
            for i in range(len(EncoreOrder)):
                linkedOrder.append([EncoreOrder[i], players[i]])
            linkedOrder.append([1, encoreUser])
            players.append(encoreUser)

        linkedOrder = sorted(linkedOrder, key=lambda x: x[0])

        maxLength = 0
        for name in [x[1].name for x in linkedOrder]:
            maxLength = max(maxLength, len(name))

        Order1 = linkedOrder[0][1].tostr(mobile, maxLength)
        Order2 = linkedOrder[1][1].tostr(mobile, maxLength)
        Order3 = linkedOrder[2][1].tostr(mobile, maxLength)
        Order4 = linkedOrder[3][1].tostr(mobile, maxLength)
        Order5 = linkedOrder[4][1].tostr(mobile, maxLength)

        order = f'<t:{timestamp}:f>\r```P1: {Order1} \rP2: {Order2} \rP3: {Order3} \rP4: {Order4} \rP5: {Order5}\r\rISV: {totalisv:.2f} | BP: {avgbp / 1000:.0f}k```\rSwap <t:{timestamp}:R>'

        return discord.Embed(title=f'Room Order {min(self.roomIndex, len(orders) - 1) + 1}', description=order, color=discord.Color.blurple())

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.primary, emoji='⬅️')
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        if (self.index > 0):
            self.index -= 1
        embed = self.generateEmbed(self.timestamps[self.index])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.primary, emoji='➡️')
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if (self.index < len(self.timestamps) - 1):
            self.index += 1
        embed = self.generateEmbed(self.timestamps[self.index])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='P1 Encore', style=discord.ButtonStyle.primary, emoji='🔄')
    async def encore(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.p1encore = not self.p1encore
        embed = self.generateEmbed(self.timestamps[self.index])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Mobile', style=discord.ButtonStyle.primary, emoji='📱')
    async def mobile(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.mobile = not self.mobile
        embed = self.generateEmbed(
            self.timestamps[self.index])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Change Rooms', style=discord.ButtonStyle.primary, emoji='1️⃣')
    async def changeRoom(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.roomIndex = (
            self.roomIndex + 1) % len(self.data[self.timestamps[self.index]].orders)
        embed = self.generateEmbed(
            self.timestamps[self.index])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Switch BP', style=discord.ButtonStyle.primary, emoji='🔀', row=2)
    async def switchBP(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.team += 1
        embed = self.generateEmbed(
            self.timestamps[self.index])
        await interaction.response.edit_message(embed=embed, view=self)

def getNextIndex(timestamps, wantedTimestamp):
    index = 0
    for timestamp in timestamps:
        if wantedTimestamp < timestamp:
            return index
        else:
            index += 1

    return index


def getCurrentEvent():
    timestamp = int(time.time() * 1000)
    for i, event in enumerate(eventData):
        if event['startAt'] < timestamp and event['closedAt'] > timestamp:
            if timestamp > event['aggregateAt']:
                if i < len(eventData) - 1:
                    return eventData[i + 1]
            return event

    return None

# @bot.slash_command(name="openslots", description="Gets the number of open slots for the current event")
# async def openSlots(ctx):
#     start = time.time()
#     await ctx.defer()
#     creds = refreshCreds()
#     event = getCurrentEvent()
#     data = await getAllOpenSlots(creds, SHEETID, event)
    
#     timestamps = [x * 3600 + int(event['startAt']/1000) for x in range(len(data))]
#     days = [event['startAt']/1000 - 3600 * 18]
#     while days[-1] < event['rankingAnnounceAt']/1000:
#         days.append(days[-1] + 86400)
    
#     indexes = [0] + [i for i, x in enumerate(timestamps) if x in days]
    
#     index = bisect_left(timestamps, start - 3600)
    
#     view = OpenSlots(indexes, timestamps, data)
    
#     await ctx.edit(embed=view.generateEmbed(), view=view)
    
    

@bot.slash_command(name="order", description="Get current order from a hyperspecific sheet")
async def order(ctx):
    start = time.time()
    await ctx.defer()
    creds = refreshCreds()
    data = await main(creds, SHEETID)

    timestamp = int(time.time())
    timestamps = list(data.keys())

    index = min(getNextIndex(data.keys(), timestamp - 2700),
                len(timestamps) - 1)

    view = EmbedButtons(data, timestamps, index)

    await ctx.edit(embed=view.generateEmbed(timestamps[index]), view=view)
    view.message = ctx

    elapsed_time = time.time() - start
    print('Execution time:', elapsed_time, 'seconds')
    
@bot.slash_command(name="hours", description="Gets your scheduled hours or the hours of a specified user")
async def hours(ctx,
                user: discord.Option(
                    discord.SlashCommandOptionType.user,
                    required=False,
                    description="A user to get the hours of"
                    )
                ):
    if user is None:
        user = ctx.author
    start = time.time()
    await ctx.defer()
    creds = refreshCreds()
    event = getCurrentEvent()
    data = await getUserVals(creds, SHEETID, user.id, event)

    timestamps = [x * 3600 + int(event['startAt']/1000) for x in range(len(data))]
    
    index = bisect_left(timestamps, start - 3600)
    
    timestamps = timestamps[index:]
    data = data[index:]
    
    returnStr = ''
    
    i = 0
    
    combinedTimes = []
    
    while i < len(data) - 1: 
        j = i + 1
        
        currentTime = data[i]
        nextTime = data[j]
        if currentTime < 0:
            i += 1
            continue
        while currentTime == nextTime and nextTime >= 0:
            j += 1
            nextTime = data[j]
            
        combinedTimes.append((i, j - i))
        i = j
        
    HOUR = 3600
    
    for i in combinedTimes:
        room = data[i[0]]
        if room < 0:
            continue
        startUnixTime = int(timestamps[i[0]])
        endUnixTime = int(startUnixTime + i[1] * HOUR)
        startTimestamp = f'<t:{startUnixTime}:D> <t:{startUnixTime}:t>'
        endTimestamp = f'<t:{endUnixTime}:D> <t:{endUnixTime}:t>'
        
        returnStr += f'`G{room + 1}` - {startTimestamp} to {endTimestamp}\r'
        
    if returnStr != '':
        embed = discord.Embed(title=f'{user.display_name}\'s hours', description=returnStr, color=0x00ff00)
        await ctx.respond(embeds=[embed])
    else:
        embed = discord.Embed(title=f'{user.display_name} has no hours scheduled', color=0x00ff00)
        await ctx.respond(embeds=[embed])

sheet = discord.SlashCommandGroup('sheet', 'Commands related to the sheet')

@sheet.command(name='get', description='Gets the current sheet url')
async def get(ctx):
    """Gets the current sheet url"""
    await ctx.respond('https://docs.google.com/spreadsheets/d/' + SHEETID + '/edit?usp=sharing')

@sheet.command(name='change', description='Changes the sheet the bot uses')
async def change(ctx, url: discord.Option(
                    discord.SlashCommandOptionType.string, 
                    required=True, 
                    description="The sheet URL or sheet ID"
                    )):
    """Changes the sheet the bot uses"""
    if '/' in url:
        url = url.split('/')
        index = url.index('d')
        url = url[index + 1]
    url = url.strip()
    with open('sheetId.txt', 'w') as f:
        f.write(url)
    global SHEETID
    SHEETID = url

    await ctx.respond("Sheet id changed to " + url)

@tasks.loop(hours=6)
async def getEventData():
    print('Getting event data')
    async with aiohttp.ClientSession() as session:
        async with session.get('https://raw.githubusercontent.com/Sekai-World/sekai-master-db-en-diff/main/events.json') as resp:
            data = await resp.json()
            global eventData
            eventData = data
            with open('events.json', 'w') as f:
                rapidjson.dump(data, f)
                f.close()
                
            print('Got event data')


@bot.event
async def on_reaction_add(reaction, user):
    message = reaction.message  # our embed
    for checkInMessage in checkInMessages:
        if checkInMessage.ctx.id == message.id:
            await checkInMessage.checkInReaction(user)

@tasks.loop(hours=1)
async def checkIn():
    print('Checking in')
    channel = commands.Bot.get_channel(bot, int(CHANNEL_ID))
    try:

        creds = refreshCreds()
        data = await main(creds, sheetId=SHEETID)

        if data == None:
            await asyncio.sleep(60)
            checkIn()
            return

        timestamps = list(data.keys())
        timestamp = int(time.time())

        index = min(getNextIndex(timestamps, timestamp),
                    len(timestamps) - 1)

        p = []

        if len(timestamps) == 0 or timestamp > timestamps[-1]:
            return
        for i, roomData in enumerate(data[timestamps[index]].checkIns):
            view = CheckInButtons()
            await view.asyncinit(roomData, timestamps[index], i + 1)
            if timestamp + 2700 < timestamps[index]:
                await channel.send(f'Next scheduled hour in Room {i + 1} <t:{timestamps[index]}:R>')
                await channel.send(embed=view.comingUp())
                continue
            if len(view.users) == 0:
                await channel.send(f'No room changes next hour in room {i+1}')
                continue
            ctx = await channel.send(view.pings(), embed=view.generateEmbed(), view=view)
            view.addCtx(ctx)
            checkInMessages.append(view)
            p.append(view.managerPing())
            
        await asyncio.gather(*p)
    except:
        traceback.print_exc()
        print('Error in check in ping')

        await channel.send('<@178294808429723648> fucked up something in the bot, manual ping this hour')


@checkIn.before_loop
async def waitUntilCheckIn():
    minute = 45
    await bot.wait_until_ready()
    now = datetime.now()
    future = datetime(now.year, now.month, now.day, now.hour, minute, 0, 0)
    if now.hour >= now.hour and now.minute > minute:
        future += timedelta(hours=1)
    print('Sleeping for ' + str((future-now).seconds/60) + ' minutes')
    await asyncio.sleep((future-now).seconds)
    

class RemindButtons(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=900)
        self.checkedIn = set()
        self.count = 0

        self.users = ['133693715398000640']

    async def managerPing(self):
        await asyncio.sleep(600)
        if len(self.checkedIn) < len(self.users):
            channel = commands.Bot.get_channel(bot, int(EMERGENCY_CHANNEL_ID))
            await channel.send(f'Room {self.room} has missing check ins')

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

if __name__ == "__main__":
    checkIn.start()
    bot.add_application_command(sheet)
    # remindPing.start()
    bot.run(token)

    print('Starting bot...')

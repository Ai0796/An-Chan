import discord
from discord.ext import commands, tasks
import rapidjson
from datetime import datetime, timedelta
import time
import asyncio
import traceback
from bisect import bisect_left
from classes.checkinButtons import CheckInButtons
from classes.openslots import OpenSlots
from pytz import timezone
from meiyarequest import main, refreshCreds, getUserVals, getAllOpenSlots
import re

bot = commands.Bot()

with open('configLemo/config.json', 'r', encoding='utf8') as f:
    configData = rapidjson.load(f)

token = configData['token']

CHANNEL_ID = '1039473652640514049'
EMERGENCY_CHANNEL_ID = '422851664781770753'
SHEETIDPATH = 'configLemo/sheetId.txt'
CHECKINPATH = 'configLemo/checkIn.txt'
EVENTPATH = '../RoboNene/sekai_master/events.json'
DCSPATH = 'configLemo/dcs.json'
PROFILEPATH = 'configLemo/profile.txt'
# HAIKU_REMIND_CHANNEL_ID = '1033352019060199484'

checkInMessages = []
checkInPrompts = []
DCs = {}

DCCommands = discord.SlashCommandGroup('dc', 'Commands related to DCing')
sheet = discord.SlashCommandGroup('sheet', 'Commands related to the sheet')

SHEETID = ''
with open(SHEETIDPATH, 'r') as f:
    SHEETID = f.read()
    
with open(CHECKINPATH, 'r') as f:
    CHANNEL_ID = f.read()

with open(EVENTPATH, 'r', encoding='utf8') as f:
    eventData = rapidjson.load(f)
    
with open(DCSPATH, 'r', encoding='utf8') as f:
    DCs = rapidjson.load(f)
    

    
class CheckInButtons(CheckInButtons):
    async def managerPing(self):
        await asyncio.sleep(600)
        if len(self.checkedIn) < len(self.users):
            channel = commands.Bot.get_channel(bot, int(EMERGENCY_CHANNEL_ID))
            await channel.send(f'Room {self.room} has missing check ins')
    
class EmbedButtons(discord.ui.View):
    
    CCMULTIPLIERS = [
        0.8561771017814248,
        0.8655341690522911,
        1.225714646826631,
        0.9301984550432184,
        1.042237531812819,
        1.0801380954836162
    ]
    
    MAXLENGTH = 100
    MOBILEMAXLENGTH = 31
    
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
        
    def formatName(self, name, maxLength):
        if (len(name) > maxLength):
            name = name[:maxLength]
        else:
            name += ' ' * (maxLength - len(name))
        return name
    
    def formatOrder(self, order, maxLength):
        if (len(order) > maxLength):
            order = order[:maxLength]
        else:
            order = ' ' * (maxLength - len(order)) + order
        return order
    
    def getLength(self):
        if self.mobile:
            return self.MOBILEMAXLENGTH
        else:
            return self.MAXLENGTH

    def generateEmbed(self, timestamp):

        orders = self.data[timestamp].getOrders()
        order = orders[min(self.roomIndex, len(orders) - 1)]
        splitOrder = order.splitlines()
        
        timestamps = re.findall(r'<t:(\d+):R>', splitOrder[0])
        timestamps = [x[3:-3] for x in timestamps]
        
        names = []
        isvs = []
        
        for line in order.splitlines()[3:-2]:
            line = line.split('|')
            names.append(line[0])
            isvs.append(line[1])
            
        strlength = self.getLength()
        
        nameLength = max([len(x) for x in names])
        isvLength = max([len(x) for x in isvs])
        nameLength += min(0, strlength - nameLength - isvLength)
        
        strOrders = []
        for name, isv in zip(names, isvs):
            strOrders.append(f'{self.formatName(name, nameLength)}|{self.formatOrder(isv, isvLength)}')

        Order1 = strOrders[0]
        Order2 = strOrders[1]
        Order3 = strOrders[2]
        Order4 = strOrders[3]
        Order5 = strOrders[4]

        order = f'<t:{timestamp}:f>\r' + \
                f'```{Order1} \r{Order2} \r{Order3} \r{Order4} \r{Order5}```'
        
        order += f'\rSwap <t:{timestamp}:R>'
        
        return discord.Embed(title=f'Room Order {min(self.roomIndex, len(orders) - 1) + 1}', description=order, color=discord.Color.blurple())

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.primary, emoji='⬅️')
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        if (self.index > 0 and len(self.data[self.timestamps[self.index - 1]].getOrders()) > 0):
            self.index -= 1
        embed = self.generateEmbed(self.timestamps[self.index])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.primary, emoji='➡️')
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if (self.index < len(self.timestamps) - 1 and len(self.data[self.timestamps[self.index + 1]].getOrders()) > 0):
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
    global eventData
    with open(EVENTPATH, 'r', encoding='utf8') as f:
        eventData = rapidjson.load(f)
        f.close()
    for i, event in enumerate(eventData):
        if event['startAt'] < timestamp and event['closedAt'] > timestamp:
            if timestamp > event['aggregateAt']:
                if i < len(eventData) - 1:
                    return eventData[i + 1]
            return event

    return None

# @bot.slash_command(name="toyaify", description="Turns the bot into Toya")
# async def toyaify(ctx):
#     with open('profiles/Toya.png', 'rb') as f:
#         pfp = f.read()
#     with open(PROFILEPATH, 'w') as f:
#         f.write('Toya')
#     await bot.user.edit(username='冬弥くん', avatar=pfp)
#     await ctx.respond('The bot is now Toya')
    
#     exit()
    
# @bot.slash_command(name="anify", description="Turns the bot into An")
# async def anify(ctx):
#     with open('profiles/An.png', 'rb') as f:
#         pfp = f.read()
#     with open(PROFILEPATH, 'w') as f:
#         f.write('An')
#     await bot.user.edit(username='杏ちゃん', avatar=pfp)
#     await ctx.respond('The bot is now An')
    
#     exit()

@bot.slash_command(name="openslots", description="Gets the number of open slots for the current event")
async def openSlots(ctx):
    start = time.time()
    await ctx.defer()
    creds = refreshCreds()
    global eventData
    data, event = await getAllOpenSlots(creds, SHEETID, eventData)
    
    timestamps = [x * 3600 + int(event['startAt']/1000) for x in range(len(data))]
    days = [event['startAt']/1000 - 3600 * 15]
    while days[-1] < event['rankingAnnounceAt']/1000:
        days.append(days[-1] + 86400)
    
    indexes = [0] + [i for i, x in enumerate(timestamps) if x in days]
    
    index = bisect_left(timestamps, start - 3600)
    
    view = OpenSlots(indexes, timestamps, data, int(event['startAt']/1000))
    
    view.set_message(ctx)
    await ctx.edit(embed=view.generateEmbed(), view=view)
    
    

@bot.slash_command(name="order", description="Get current order from a hyperspecific sheet")
async def order(ctx):
    start = time.time()
    await ctx.defer()
    creds = refreshCreds()
    data = await main(creds, SHEETID)
    
    if data is None:
        await ctx.respond('No Orders Found or Error occured, please try again later.')
        return

    timestamp = int(time.time())
    timestamps = [key for key in data]

    index = min(getNextIndex(timestamps, timestamp - 2700),
                len(timestamps) - 1)
    
    if len(timestamps) == 0 or timestamp > timestamps[-1] + 3600:
        await ctx.respond('No Orders Found')
        return

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
    start = time.time()
    if user is None:
        user = ctx.author
    start = time.time()
    await ctx.defer()
    creds = refreshCreds()
    event = getCurrentEvent()
    data = await getUserVals(creds, SHEETID, user.id, event)

    eventStart = int(event['startAt']/1000)
    timestamps = [x * 3600 + eventStart for x in range(len(data))]
    
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
        
    elapsed_time = time.time() - start
    print('/hours Execution time:', elapsed_time, 'seconds')

# @sheet.command(name='get', description='Gets the current sheet url')
# async def get(ctx):
#     """Gets the current sheet url"""
#     await ctx.respond('https://docs.google.com/spreadsheets/d/' + SHEETID + '/edit?usp=sharing')

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
    with open(SHEETIDPATH, 'w') as f:
        f.write(url)
    global SHEETID
    SHEETID = url

    await ctx.respond("Sheet id changed to " + url, ephemeral=True)
    
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
        

@bot.slash_command(name="changecheckin", description="Changes the channel the bot uses for checkins")
async def changecheckin(ctx):
    """Changes the check in channel"""
    channel = str(ctx.channel.id)
    with open(CHECKINPATH, 'w') as f:
        f.write(channel)
    global CHANNEL_ID
    CHANNEL_ID = channel

    await ctx.respond("Check In Channel changed to " + CHANNEL_ID, ephemeral=True)
    
@bot.slash_command(name="checkinprompt", description="Adds a check in prompt to the queue")
async def checkinprompt(ctx, prompt: discord.Option(
                    discord.SlashCommandOptionType.string, 
                    required=True, 
                    description="The prompt (max 1000 characters)"
                    )):
    """Adds a check in prompt to the queue"""
    prompt = prompt[:1000]
    prompt += f'\r\r- {ctx.author.display_name}\r\r'
    checkInPrompts.append(prompt)
    await ctx.respond(f"Check In Prompt added to queue, current position: {len(checkInPrompts)}", ephemeral=True)

@bot.slash_command(name="manualcheckin", description="Manually runs check in, run this at :50")
async def manualCheckIn(ctx):
    await checkIn()
    await ctx.respond("Manual Check In Sent")
   
@bot.slash_command(name="viewcheckin", description="Previews the next check in message")
async def viewcheckin(ctx):
    """Previews the next check in message"""
    creds = refreshCreds()
    data = await main(creds, sheetId=SHEETID)

    timestamps = [key for key in data.keys()]
    timestamp = int(time.time())

    index = min(getNextIndex(timestamps, timestamp),
                len(timestamps) - 1)

    if len(timestamps) == 0 or timestamp > timestamps[-1]:
        await ctx.respond('No Check Ins Found', ephemeral=True)
        return
    for i, roomData in enumerate(data[timestamps[index]].checkIns):
        view = CheckInButtons()
        await view.asyncinit(roomData, timestamps[index], i + 1, checkInPrompts, True)
        if timestamp + 2700 < timestamps[index]:
            await ctx.respond(f'Next scheduled hour in Room {i + 1} <t:{timestamps[index]}:R>', 
                              embed=view.comingUp(),
                              ephemeral=True)
            continue
        if len(view.users) == 0:
            await ctx.respond(f'No room changes next hour in room {i+1}',
                              ephemeral=True)
            continue
        await ctx.respond(embed=view.generateEmbed(), ephemeral=True)

@bot.event
async def on_reaction_add(reaction, user):
    message = reaction.message  # our embed
    for checkInMessage in checkInMessages:
        if checkInMessage.ctx.id == message.id:
            await checkInMessage.checkInReaction(user)

@tasks.loop(hours=1)
async def checkIn():
    tz = timezone('America/New_York')
    print('Checking in at ' + str(datetime.now(tz)))
    channel = commands.Bot.get_channel(bot, int(CHANNEL_ID))
    try:

        creds = refreshCreds()
        data = await main(creds, sheetId=SHEETID)

        if data == None:
            await asyncio.sleep(60)
            checkIn()
            return

        timestamps = [key for key in data.keys()]
        timestamp = int(time.time())

        index = min(getNextIndex(timestamps, timestamp),
                    len(timestamps) - 1)

        p = []

        if len(timestamps) == 0 or timestamp > timestamps[-1]:
            print('No Check Ins Found')
            return
        for i, roomData in enumerate(data[timestamps[index]].checkIns):
            view = CheckInButtons()
            await view.asyncinit(roomData, timestamps[index], i + 1, checkInPrompts)
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
    bot.add_application_command(DCCommands)
    # remindPing.start()
    bot.run(token)

    print('Starting bot...')

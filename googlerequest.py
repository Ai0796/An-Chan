import asyncio
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os 
import re
from bisect import bisect_left
import numpy as np
import itertools
import rapidjson

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
EVENTPATH = 'config/events.json'

def excel_cols(n):
    if n < 1:
        raise ValueError("Number must be positive")
    result = ""
    while True:
        if n > 26:
            n, r = divmod(n - 1, 26)
            result = chr(r + ord('A')) + result
        else:
            return chr(n + ord('A') - 1) + result

async def lookup(spreadsheet, query, sheetId):
    return spreadsheet.values().get(spreadsheetId=sheetId,
                                        range=query).execute()
async def lookupBatch(spreadsheet, queries, sheetId):
    return spreadsheet.values().batchGet(spreadsheetId=sheetId,
                                        ranges=queries).execute()    

def parseBp(bp):
    if (str == ''):
        return 0
    filteredStr = re.sub('[^0-9]', '', bp);
    val = int(filteredStr);
    if (val < 1000):
        val *= 1000
    return val;

class Player:
    
    maxLength = 40
    mobileLength = 31
    
    def __init__(self, name, lead, team, bp):
        self.name = name.strip()
        self.lead = int(lead)
        self.team = int(team)
        self.isv = lead + (team - lead)/5.0
        self.bp = bp
        
    def __str__(self):
        return f'{self.name} | {self.lead}/{self.team}/{self.bp/1000:.0f}k'
    
    def tostr(self, mobile, maxLength):
        str = f' | {self.lead}/{self.team}/{self.bp/1000:.0f}k'
        if 'event' in self.name.lower():
            str = f' | Event'
        length = len(str) + maxLength
        
        if (mobile):
            padding = self.mobileLength - length + 1
        else:
            padding = self.maxLength - length + 1

        str = f'{self.name}' + ' ' * (maxLength - len(self.name))
        
        if padding < 0:
            str = str[:padding]
            
        
        str += f' | {self.lead}/{self.team}/{self.bp/1000:.0f}k'
            
        return str 
    
class TimeData:
    """
    Contains information for a single timestamp
    """
    
    def __init__(self, timestamp, players, checkIns):
        self.timestamp = timestamp
        self.orders = players
        self.checkIns = checkIns
        
    def addPlayer(self, player):
        self.orders.append(player)
        
    def addCheckIn(self, player):
        self.checkIns.append(player)
        
    def getOrders(self):
        return self.orders
        
    def getCheckIns(self):
        return self.checkIns
    
    def add(self, timeData):
        self.orders.extend(timeData.orders)
        self.checkIns.extend(timeData.checkIns)
        
    
def refreshCreds():
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    
    creds = None
    
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        print('refreshing creds')
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
    print('returning creds')
            
    return creds


def getCurrentEvent(timestamp):
    timestamp = int(timestamp * 1000)
    print(timestamp)
    with open(EVENTPATH, 'r', encoding='utf8') as f:
        eventData = rapidjson.load(f)[::]
    f.close()
    for i, event in enumerate(eventData):
        if event['startAt'] <= timestamp and event['closedAt'] >= timestamp:
            if timestamp > event['aggregateAt']:
                if i < len(eventData) - 1:
                    return eventData[i + 1]
            return event

    return None

async def getAllOpenSlots(creds, sheetId, eventData):
    """
    Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    
    Returns:
    List [index]
    """

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        spreadsheet = service.spreadsheets()
        sheet_metadata = spreadsheet.get(spreadsheetId=sheetId).execute()
        sheets = sheet_metadata.get('sheets', '')

        # Q4:Q27
        # P4:P27

        teams = None
        days = []
        for sheet in sheets:
            if sheet['properties']['title'].lower().strip() == 'teams':
                teams = sheet['properties']['title']

            if sheet['properties']['title'].lower().strip().startswith('day'):
                days.append(sheet['properties']['title'])

        queue = []
        
        hours = await getOpenSlots(spreadsheet, days, sheetId)
        
        event = getCurrentEvent(hours[0][0])
        
        hourDic = {
            timestamp: 0 for timestamp in np.arange(int(event['startAt']/1000), int(event['rankingAnnounceAt']/1000), 3600)}
        
        for hour in hours:
            hourDic[hour[0]] += hour[1]

        return list(hourDic.values()), event

    except HttpError as err:
        print(err)
        
async def getOpenSlots(spreadsheet, titles, sheetId):

    column = '3:3'
    lookups = []
    for title in titles:
        lookups.append(f'{title}!{column}')
    result = await lookupBatch(spreadsheet, lookups, sheetId)
    values = result.get('valueRanges', 0)
    values = [x['values'] for x in values]
    
    lookups = []
    timestampIndexes = []
    playerIndexesList = []
    
    for valueSets, title in zip(values, titles):
        
        valueSets = valueSets[0]

        valueSets = '|'.join(valueSets).lower().split('|')

        indexes = [i for i, x in enumerate(valueSets) if x in [
            'p1', 'p2', 'p3', 'p4', 'p5', 'timestamp']]
        
        playerIndexes = [i for i, x in enumerate(valueSets) if x in [
            'p1', 'p2', 'p3', 'p4', 'p5']]

        minVal = min(indexes)
        maxVal = max(indexes)

        timestampIndex = valueSets.index('timestamp') - minVal

        minColumn = excel_cols(minVal + 1)
        maxColumn = excel_cols(maxVal + 1)

        combinedLookup = f'{title}!{minColumn}4:{maxColumn}36'
        
        lookups.append(combinedLookup)
        timestampIndexes.append(timestampIndex)
        playerIndexesList.append(playerIndexes)

    result = await lookupBatch(spreadsheet, lookups, sheetId)

    values = result.get('valueRanges', 0)
    values = [x['values'] for x in values]

    hours = []

    for table, timestampIndex, playerIndexes in zip(values, timestampIndexes, playerIndexesList):
        for row in table:
            values = [x for i, x in enumerate(row) if x != '' and i + minVal in playerIndexes]
            if len(values) == 0 or (timestampIndex >= len(row)):
                continue
            hours.append([int(row[timestampIndex]), 5 - len(values)])

    return hours

async def getNames(spreadsheet, title, sheetId, userid):

    names = []
    userid = str(userid).strip()
    query = '1:1'
    result = await lookup(spreadsheet, f'{title}!{query}', sheetId)
    values = result.get('values', [])[0]

    values = '|'.join(values).lower().split('|')

    nameIndex = values.index('name')
    idIndex = values.index('discord id')

    minVal = min(nameIndex, idIndex)
    maxVal = max(nameIndex, idIndex)

    minColumn = excel_cols(minVal + 1)
    maxColumn = excel_cols(maxVal + 1)

    combinedLookup = f'{title}!{minColumn}2:{maxColumn}1001'

    result = await lookup(spreadsheet, combinedLookup, sheetId)

    values = result.get('values', [])

    for row in values:
        if len(row) < maxVal - minVal + 1:
            continue
        if row[nameIndex - minVal] and str(row[idIndex - minVal]).strip() == userid:
            names.append(row[nameIndex - minVal])

    names = [x for x in names]
    return names

async def getUsers(spreadsheet, titles, sheetId, names):

    query = '3:3'
    lookups = []
    for title in titles:
        lookups.append(f'{title}!{query}')
    
    result = await lookupBatch(spreadsheet, lookups, sheetId)
    values = result.get('valueRanges', 0)
    values = [x['values'] for x in values]

    lookups = []
    timestampIndexes = []

    for valueSets, title in zip(values, titles):

        valueSets = valueSets[0]

        valueSets = '|'.join(valueSets).lower().split('|')

        playerIndexes = [i for i, x in enumerate(valueSets) if x in [
            'p1', 'p2', 'p3', 'p4', 'p5']]

        minVal = min(playerIndexes)
        maxVal = max(playerIndexes)
        
        timestampIndex = valueSets.index('timestamp')

        combinedLookup = f'{title}!{excel_cols(minVal + 1)}4:{excel_cols(maxVal + 1)}27'
        timestampLookup = f'{title}!{excel_cols(timestampIndex + 1)}4:{excel_cols(timestampIndex + 1)}27'
        
        lookups.append(combinedLookup)
        lookups.append(timestampLookup)
        timestampIndexes.append(timestampIndex)

    result = await lookupBatch(spreadsheet, lookups, sheetId)
    
    values = result.get('valueRanges', 0)
    hours = []
    for i in range(0, len(values), 2):
        if 'values' in values[i] and 'values' in values[i + 1]:
            for players, timestamp in zip(values[i]['values'], values[i + 1]['values']):
                if len(players) <= 0:
                    continue
                if len(np.intersect1d(players, names)) > 0:
                    hours.append([int(timestamp[-1]), 0])
                
    return hours

async def getUserVals(creds, sheetId, userid, eventData):
    """
    Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    
    Returns:
    List [index]
    """

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        spreadsheet = service.spreadsheets()
        sheet_metadata = spreadsheet.get(spreadsheetId=sheetId).execute()
        sheets = sheet_metadata.get('sheets', '')

        # Q4:Q27
        # P4:P27

        teams = None
        days = []
        for sheet in sheets:
            if sheet['properties']['title'].lower().strip() == 'teams':
                teams = sheet['properties']['title']

            if sheet['properties']['title'].lower().strip().startswith('day'):
                days.append(sheet['properties']['title'])

        queue = []

        names = await getNames(spreadsheet, teams, sheetId, userid)
        
        if len(names) < 1:
            return [-1]
        
        hours = await getUsers(spreadsheet, days, sheetId, names)
        
        hourDic = {
            timestamp: -1 for timestamp in np.arange(int(eventData['startAt']/1000), int(eventData['rankingAnnounceAt']/1000), 3600)}
        
        for hour in hours:
            if hour[0] not in hourDic:
                continue
            val = max(hour[1], hourDic[hour[0]])
            hourDic[hour[0]] = val
            
        hourDic = {k: v for k, v in sorted(hourDic.items(), key=lambda item: item[0])}
        return list(hourDic.values())

    except HttpError as err:
        print(err)

async def getLookups(spreadsheet, titles, sheetId) -> list:
    query = '3:3'
    lookups = []
    for title in titles:
        lookups.append(f'{title}!{query}')
    result = await lookupBatch(spreadsheet, lookups, sheetId)
    valueRanges = result.get('valueRanges', [])
    
    combinedLookup = []
    timestampCols = []
    orderCols = []
    checkInCols = []

    for title, values in zip(titles, valueRanges):
        values = values.get('values', [])[0]
        values = '|'.join(values).lower().split('|')
        
        if 'timestamp' not in values:
            return None
        
        timestampIndex = values.index('timestamp')
        orderIndex = values.index('room order')
        checkInIndex = values.index('check in ping')
        
        minColumn = min(timestampIndex, orderIndex, checkInIndex)
        maxColumn = max(timestampIndex, orderIndex, checkInIndex)
        
        combinedLookup += [
            f'{title}!{excel_cols(minColumn + 1)}3:{maxColumn + 1}27',
        ]
        
        timestampCols.append(timestampIndex - minColumn)
        orderCols.append(orderIndex - minColumn)
        checkInCols.append(checkInIndex - minColumn)
    
    return combinedLookup, [timestampCols, orderCols, checkInCols]

async def getVals(spreadsheet, combinedLookup, colIndexes, sheetId) -> dict:
    timestampDict = {}
    result = await lookupBatch(spreadsheet, combinedLookup, sheetId)

    values = result.get('valueRanges', 0)
    values = [x['values'] if 'values' in x else [] for x in values]
    
    timestampCols = colIndexes[0]
    orderCols = colIndexes[1]
    checkInCols = colIndexes[2]
    
    timestamps = []
    orders = []
    checkIns = []
    
    for table, timestampCol, orderCol, checkInCol in zip(values, timestampCols, orderCols, checkInCols):
        maxCol = max(timestampCol, orderCol, checkInCol)
        for row in table:
            if len(row) <= maxCol:
                continue
            timestamps.append(row[timestampCol])
            orders.append(row[orderCol])
            checkIns.append(row[checkInCol])

    values = zip(timestamps, orders, checkIns)
    pattern = re.compile('^P[0-9]:')

    for timestamp, order, checkIn in values:

        if (len(order) > 0 and order.startswith('New Room Order:')):

            players = []
            for line in order.splitlines():
                if not pattern.match(line):
                    continue
                strsplit = line[4:].split('|')
                name = strsplit[0]
                vals = strsplit[1].split('/')
                try:
                    player = Player(name, int(vals[0]), int(
                        vals[1]), parseBp(vals[2]))
                    players.append(player)
                except:
                    player = Player(name, 0, 0, 0)
                    players.append(player)

            if timestamp == 'Timestamp':
                print(order.splitlines(), order.startswith('New Room Order:'))
            if int(timestamp) in timestampDict:
                timestampDict[int(timestamp)].addPlayer(players)
                timestampDict[int(timestamp)].addCheckIn(checkIn)
            else:
                timestampDict[int(timestamp)] = TimeData(
                    int(timestamp), [players], [checkIn])
        else:
            pass

    return timestampDict

async def main(creds, sheetId) -> dict:
    """
    Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    
    Returns:
    Dict {timestamp: {orders: [], checkIns: []}}
    """
    timestampDict = {}

    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        spreadsheet = service.spreadsheets()
        sheet_metadata = spreadsheet.get(spreadsheetId=sheetId).execute()
        sheets = sheet_metadata.get('sheets', '')
        
        # Q4:Q27
        # P4:P27
        titles = []
        for sheet in sheets:
            if 'day' in sheet['properties']['title'].lower().strip():
                titles.append(sheet['properties']['title'])
                
        queue = []
        
        lookups, colIndexes = await getLookups(spreadsheet, titles, sheetId)
        timestampDict = await getVals(spreadsheet, lookups, colIndexes, sheetId)
                    
        ##Sorts keys
        myKeys = list(timestampDict.keys())
        myKeys.sort()
        return {i: timestampDict[i] for i in myKeys}  
    
    except HttpError as err:
        print(err)
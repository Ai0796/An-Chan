import asyncio
import math
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os 
import re
from bisect import bisect_left

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

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
        if row[nameIndex - minVal] and str(row[idIndex - minVal]).strip() == userid:
            names.append(row[nameIndex - minVal])

    return names

async def getUsers(spreadsheet, title, sheetId, names):

    query = '2:2'
    result = await lookup(spreadsheet, f'{title}!{query}', sheetId)
    values = result.get('values', [])[0]

    values = '|'.join(values).lower().split('|')

    indexes = [i for i, x in enumerate(values) if x in ['a', 'b', 'c', 'd', 'e']]

    minVal = min(indexes)
    maxVal = max(indexes)
    
    indexLength = [i - minVal - 1 for i, x in enumerate(values) if x == 'a']

    minColumn = excel_cols(minVal + 1)
    maxColumn = excel_cols(maxVal + 1)

    combinedLookup = f'{title}!{minColumn}3:{maxColumn}1001'

    result = await lookup(spreadsheet, combinedLookup, sheetId)

    values = result.get('values', [])

    hours = []

    for row in values:
        values = [i for i, x in enumerate(row) if x in names]
        if values:

            hours.append(bisect_left(indexLength, values[0]) - 1)
        else:
            hours.append(-1)

    return hours

async def getUserVals(creds, sheetId, userid):
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
        schedule = None
        for sheet in sheets:
            if sheet['properties']['title'].lower().strip() == 'teams':
                teams = sheet['properties']['title']
                
            if 'scheduling' in sheet['properties']['title'].lower().strip():
                schedule = sheet['properties']['title']

        names = await getNames(spreadsheet, teams, sheetId, userid)
        hours = await getUsers(spreadsheet, schedule, sheetId, names)
        
        return hours

    except HttpError as err:
        print(err)
       

async def getAllOpenSlots(creds, sheetId, eventData):
    return None

async def getVals(spreadsheet, title, sheetId):
    timestampDict = {}
    query = '2:2'
    result = await lookup(spreadsheet, f'{title}!{query}', sheetId)
    values = result.get('values', [])[0]

    values = '|'.join(values).lower().split('|')

    CIindexes = [i for i, x in enumerate(values) if x == 'ci']
    ROindexes = [i for i, x in enumerate(values) if x == 'ro']

    minVal = min(CIindexes + ROindexes)
    maxVal = max(CIindexes + ROindexes)

    minColumn = excel_cols(minVal + 1)
    maxColumn = excel_cols(maxVal + 1)

    combinedLookup = f'{title}!{minColumn}3:{maxColumn}1001'

    result = await lookup(spreadsheet, combinedLookup, sheetId)

    values = result.get('values', [])

    orders = []
    checkIns = []
    for row in values:
        for i in CIindexes:
            if (len(row) > i - minVal):
                checkIns.append(row[i - minVal])

            else:
                checkIns.append('')
        for i in ROindexes:
            if (len(row) > i - minVal):
                orders.append(row[i - minVal])
            else:
                orders.append('')

    values = zip(orders, checkIns)
    pattern = re.compile('^P[0-9] -')

    for order, checkIn in values:

        order = order.strip()
        checkIn = checkIn.strip()
        if checkIn == 'No swaps this hour':
            checkIn = ''
        timestamp = None

        if (len(order) > 0):

            if len(order) > 0:
                
                players = []
                timestamp = re.findall(r'<t:\d*:.>', order)[0]

                for line in order.splitlines():
                    line = line.strip('`').strip()
                    if not pattern.match(line):
                        continue
                    substr = line[line.index('ISV: '):]

                    name = line[5:line.index('(ISV: ')].strip()
                    vals = re.sub(r'[^\d]', ' ', substr).split()

                    try:
                        if len(vals) < 3:
                            bp = 0
                        else:
                            bp = parseBp(vals[2])
                        player = Player(name, int(vals[0]), int(vals[1]), bp)
                        players.append(player)
                    except:
                        player = Player(name, 0, 0, 0)
                        players.append(player)

            if len(checkIn) > 0:
                reoutput = re.findall(r'<t:\d*:.>', checkIn)
                if len(reoutput) > 0:
                    timestamp = reoutput[0]

            timestamp = timestamp.split(':')[1]

            if int(timestamp) in timestampDict:
                timestampDict[int(timestamp)].addPlayer(players)
                timestampDict[int(timestamp)].addCheckIn(checkIn)
            else:
                timestampDict[int(timestamp)] = TimeData(
                    int(timestamp[0]), [players], [checkIn])
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
            if 'scheduling' in sheet['properties']['title'].lower().strip():
                titles.append(sheet['properties']['title'])
                
        queue = []
        for title in titles:
            
            p = getVals(spreadsheet, title, sheetId)
            queue.append(p)
            
        results = await asyncio.gather(*queue)
        
        for result in results:
            for key in result.keys():
                if key in timestampDict:
                    timestampDict[key].add(result[key])
                else:
                    timestampDict[key] = result[key]
                    # orderList.append('Break Time!')
                    
        ##Sorts keys
        myKeys = list(timestampDict.keys())
        myKeys.sort()
        return {i: timestampDict[i] for i in myKeys}  
    
    except HttpError as err:
        print(err)

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
from classes.Player import Player
from classes.TimeData import TimeData
from classes.BaseRequest import BaseRequest
import numpy as np

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

class haiku(BaseRequest):
    
    def getTeams(self, sheets):
        for sheet in sheets:
            if sheet['properties']['title'].lower().strip() == 'teams':
                return sheet['properties']['title']
            
    def getScheduleSheets(self, sheets):
        scheduleSheets = []
        for sheet in sheets:
            if 'scheduling' in sheet['properties']['title'].lower().strip():
                scheduleSheets.append(sheet['properties']['title'])
        return scheduleSheets

    def excel_cols(self, n):
        if n < 1:
            raise ValueError("Number must be positive")
        result = ""
        while True:
            if n > 26:
                n, r = divmod(n - 1, 26)
                result = chr(r + ord('A')) + result
            else:
                return chr(n + ord('A') - 1) + result

    async def lookup(self, spreadsheet, query, sheetId):
        return spreadsheet.values().get(spreadsheetId=sheetId,
                                            range=query).execute()
    def parseBp(self, bp):
        if (str == ''):
            return 0
        filteredStr = re.sub('[^0-9]', '', bp)
        val = int(filteredStr)
        if (val < 1000):
            val *= 1000
        return val
        
    def refreshCreds(self):
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
                
        return creds


    async def getNames(self, spreadsheet, title, sheetId, userid):
        
        names = []
        userid = str(userid).strip()
        query = '1:1'
        result = await self.lookup(spreadsheet, f'{title}!{query}', sheetId)
        values = result.get('values', [])[0]

        values = '|'.join(values).lower().split('|')

        nameIndex = values.index('name')
        idIndex = values.index('discord id')

        minVal = min(nameIndex, idIndex)
        maxVal = max(nameIndex, idIndex)

        minColumn = self.excel_cols(minVal + 1)
        maxColumn = self.excel_cols(maxVal + 1)

        combinedLookup = f'{title}!{minColumn}2:{maxColumn}1001'

        result = await self.lookup(spreadsheet, combinedLookup, sheetId)

        values = result.get('values', [])

        for row in values:
            if row[nameIndex - minVal] and str(row[idIndex - minVal]).strip() == userid:
                names.append(row[nameIndex - minVal])

        return names

    async def getUsers(self, spreadsheet, title, sheetId, names):

        query = '2:2'
        result = await self.lookup(spreadsheet, f'{title}!{query}', sheetId)
        values = result.get('values', [])[0]

        values = '|'.join(values).lower().split('|')

        indexes = [i for i, x in enumerate(values) if x in ['a', 'b', 'c', 'd', 'e']]

        minVal = min(indexes)
        maxVal = max(indexes)
        
        indexLength = [i - minVal - 1 for i, x in enumerate(values) if x == 'a']

        minColumn = self.excel_cols(minVal + 1)
        maxColumn = self.excel_cols(maxVal + 1)

        combinedLookup = f'{title}!{minColumn}3:{maxColumn}1001'

        result = await self.lookup(spreadsheet, combinedLookup, sheetId)

        values = result.get('values', [])

        hours = []

        for row in values:
            values = [i for i, x in enumerate(row) if x in names]
            if values:

                hours.append(bisect_left(indexLength, values[0]) - 1)
            else:
                hours.append(-1)

        return hours

    async def getUserVals(self, creds, sheetId, userid, event):
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

            names = await self.getNames(spreadsheet, teams, sheetId, userid)
            hours = await self.getUsers(spreadsheet, schedule, sheetId, names)
            
            return hours

        except HttpError as err:
            print(err)
        

    async def getAllOpenSlots(self, creds, sheetId, eventData):
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

            scheduleSheet  = self.getScheduleSheets(sheets)
            
            hours = await self.getOpenSlots(spreadsheet, scheduleSheet, sheetId)
            
            event = self.getCurrentEvent(hours[0][0])
            if event is None:
                return 
                        
            hourDic = {
                timestamp: -1 for timestamp in np.arange(int(event['startAt']/1000), int(event['rankingAnnounceAt']/1000), 3600)}
            
            for hour in hours:
                if len(hour) < 2:
                    continue
                hourDic[hour[0]] = max(0, hourDic[hour[0]]) + hour[1]

            return list(hourDic.values()), event

        except HttpError as err:
            print(err)
                
    async def getOpenSlots(self, spreadsheet, titles, sheetId):

        lookups = []
        for title in titles:
            lookups.append(f'{title}!{self.headerRow}')
        result = await self.lookupBatch(spreadsheet, lookups, sheetId)
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

            minColumn = self.excel_cols(minVal + 1)
            maxColumn = self.excel_cols(maxVal + 1)

            combinedLookup = f'{title}!{minColumn}3:{maxColumn}300'
            
            lookups.append(combinedLookup)
            timestampIndexes.append(timestampIndex)
            playerIndexesList.append(playerIndexes)

        result = await self.lookupBatch(spreadsheet, lookups, sheetId)

        values = result.get('valueRanges', 0)
        values = [x['values'] for x in values]

        hours = []

        for table, timestampIndex, playerIndexes in zip(values, timestampIndexes, playerIndexesList):
            for row in table:
                values = [x for i, x in enumerate(row) if len(x) > 0 and i + minVal in playerIndexes]
                if len(values) == 0 or (timestampIndex >= len(row)):
                    continue
                hours.append([int(row[timestampIndex]), 5 - len(values)])

        return hours

    async def getVals(self, spreadsheet, title, sheetId):
        timestampDict = {}
        query = '2:2'
        result = await self.lookup(spreadsheet, f'{title}!{query}', sheetId)
        values = result.get('values', [])[0]

        values = '|'.join(values).lower().split('|')

        CIindexes = [i for i, x in enumerate(values) if x == 'ci']
        ROindexes = [i for i, x in enumerate(values) if x == 'ro']

        minVal = min(CIindexes + ROindexes)
        maxVal = max(CIindexes + ROindexes)

        minColumn = self.excel_cols(minVal + 1)
        maxColumn = self.excel_cols(maxVal + 1)

        combinedLookup = f'{title}!{minColumn}3:{maxColumn}1001'

        result = await self.lookup(spreadsheet, combinedLookup, sheetId)

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

            if len(order) == 0:
                continue
                
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
                        bp = self.parseBp(vals[2])
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


        return timestampDict

    async def main(self, creds, sheetId) -> dict:
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
            titles = self.getScheduleSheets(sheets)
                    
            queue = []
            for title in titles:
                
                p = self.getVals(spreadsheet, title, sheetId)
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

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os 
import re
import numpy as np
from classes.Player import Player
from classes.TimeData import TimeData
from classes.BaseRequest import BaseRequest

class ai2(BaseRequest):
    
    headerRow = "1:1"
    
    def getTeamSheet(self, sheets):
        for sheet in sheets:
            if sheet['properties']['title'].lower().strip() == 'teams':
                return sheet['properties']['title']
            
    def getScheduleSheets(self, sheets):
        scheduleSheets = []
        for sheet in sheets:
            if sheet['properties']['title'].lower().strip() == 'schedule':
                return [sheet['properties']['title']]

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
                timestamp: 0 for timestamp in np.arange(int(event['startAt']/1000), int(event['rankingAnnounceAt']/1000), 3600)}
            
            for hour in hours:
                if len(hour) < 2:
                    continue
                hourDic[hour[0]] += hour[1]

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

    async def getNames(self, spreadsheet, title, sheetId, userid):

        names = []
        userid = str(userid).strip()
        query = '1:1'
        result = await self.lookup(spreadsheet, f'{title}!{query}', sheetId)
        print(result)
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
            if len(row) < maxVal - minVal + 1:
                continue
            if row[nameIndex - minVal] and str(row[idIndex - minVal]).strip() == userid:
                names.append(row[nameIndex - minVal])

        names = [x for x in names]
        return names

    async def getUsers(self, spreadsheet, titles, sheetId, names):

        lookups = []
        for title in titles:
            lookups.append(f'{title}!{self.headerRow}')
        
        result = await self.lookupBatch(spreadsheet, lookups, sheetId)
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

            combinedLookup = f'{title}!{self.excel_cols(minVal + 1)}3:{self.excel_cols(maxVal + 1)}300'
            timestampLookup = f'{title}!{self.excel_cols(timestampIndex + 1)}3:{self.excel_cols(timestampIndex + 1)}300'
            
            lookups.append(combinedLookup)
            lookups.append(timestampLookup)
            timestampIndexes.append(timestampIndex)

        result = await self.lookupBatch(spreadsheet, lookups, sheetId)
        
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
    
    async def getNameDic(self, spreadsheet, title, sheetId):

        nameDic = {}
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
            if len(row) < maxVal - minVal + 1:
                continue
            if row[nameIndex - minVal]:
                nameDic[row[nameIndex - minVal]] = row[idIndex - minVal]

        return nameDic
    
    async def getUserIds(self, spreadsheet, titles, sheetId, nameDic):

        lookups = []
        for title in titles:
            lookups.append(f'{title}!{self.headerRow}')

        result = await self.lookupBatch(spreadsheet, lookups, sheetId)
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

            combinedLookup = f'{title}!{self.excel_cols(minVal + 1)}3:{self.excel_cols(maxVal + 1)}300'
            timestampLookup = f'{title}!{self.excel_cols(timestampIndex + 1)}3:{self.excel_cols(timestampIndex + 1)}300'

            lookups.append(combinedLookup)
            lookups.append(timestampLookup)
            timestampIndexes.append(timestampIndex)

        result = await self.lookupBatch(spreadsheet, lookups, sheetId)

        values = result.get('valueRanges', 0)
        pings = []
        for i in range(0, len(values), 2):
            if 'values' in values[i] and 'values' in values[i + 1]:
                for players, timestamp in zip(values[i]['values'], values[i + 1]['values']):
                    if len(players) <= 0:
                        continue
                    pings.append([int(timestamp[-1]), [nameDic[x] for x in players if x in nameDic]])

        return pings
    
    async def getPings(self, creds, sheetId, eventData):
        try:
            service = build('sheets', 'v4', credentials=creds)

            # Call the Sheets API
            spreadsheet = service.spreadsheets()
            sheet_metadata = spreadsheet.get(spreadsheetId=sheetId).execute()
            sheets = sheet_metadata.get('sheets', '')

            teams = None
            days = []
            for sheet in sheets:
                if sheet['properties']['title'].lower().strip() == 'teams':
                    teams = sheet['properties']['title']

                if sheet['properties']['title'].lower().strip().startswith('day'):
                    days.append(sheet['properties']['title'])

            nameDic = await self.getNameDic(spreadsheet, teams, sheetId)

            if len(nameDic) < 1:
                return []

            hours = await self.getUserIds(spreadsheet, days, sheetId, nameDic)
            
            hourDic = {
                timestamp: set() for timestamp in np.arange(int(eventData['startAt']/1000), int(eventData['rankingAnnounceAt']/1000), 3600)}

            for hour in hours:
                if hour[0] not in hourDic:
                    continue
                hourDic[hour[0]].update(hour[1])

            hourDic = {k: v for k, v in sorted(
                hourDic.items(), key=lambda item: item[0])}
            return hourDic

        except HttpError as err:
            print(err)

    async def getUserVals(self, creds, sheetId, userid, eventData):
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

            teams = self.getTeamSheet(sheets)
            days = self.getScheduleSheets(sheets)

            names = await self.getNames(spreadsheet, teams, sheetId, userid)
            
            print(names, teams, days, userid)
            
            if len(names) < 1:
                return [-1]
            
            hours = await self.getUsers(spreadsheet, days, sheetId, names)
            
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

    async def getLookups(self, spreadsheet, titles, sheetId) -> list:
        lookups = []
        for title in titles:
            lookups.append(f'{title}!{self.headerRow}')
        result = await self.lookupBatch(spreadsheet, lookups, sheetId)
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
            orderIndex = values.index('order')
            checkInIndex = values.index('check in')
            
            minColumn = min(timestampIndex, orderIndex, checkInIndex)
            maxColumn = max(timestampIndex, orderIndex, checkInIndex)
            
            combinedLookup += [
                f'{title}!{self.excel_cols(minColumn + 1)}3:{self.excel_cols(maxColumn + 1)}300',
            ]
            
            timestampCols.append(timestampIndex - minColumn)
            orderCols.append(orderIndex - minColumn)
            checkInCols.append(checkInIndex - minColumn)
        
        return combinedLookup, [timestampCols, orderCols, checkInCols]

    async def getOrderVals(self, spreadsheet, combinedLookup, colIndexes, sheetId) -> dict:
        timestampDict = {}
        result = await self.lookupBatch(spreadsheet, combinedLookup, sheetId)

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
                            vals[1]), self.parseBp(vals[2]))
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
            
            lookups, colIndexes = await self.getLookups(spreadsheet, titles, sheetId)
            timestampDict = await self.getOrderVals(spreadsheet, lookups, colIndexes, sheetId)
                        
            ##Sorts keys
            myKeys = list(timestampDict.keys())
            myKeys.sort()
            return {i: timestampDict[i] for i in myKeys}  
        
        except HttpError as err:
            print(err)
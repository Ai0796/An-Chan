from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
import numpy as np
from classes.TimeData import TimeData
from classes.Player import Player
from classes.BaseRequest import BaseRequest

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
EVENTPATH = '../RoboNene/sekai_master/events.json'

class Lemonade(BaseRequest):
    
    ROOMS = ["g1", "g2"]
    TEAMS = ["player db"]
    
    def getTeamSheet(self, sheets) -> str:
        for sheet in sheets:
            if sheet['properties']['title'].lower().strip() in self.TEAMS:
                return sheet['properties']['title']
            
    def getScheduleSheets(self, sheets) -> list:
        scheduleSheets = []
        for sheet in sheets:
            if sheet['properties']['title'].lower().strip() in self.ROOMS:
                scheduleSheets.append(sheet['properties']['title'])
                
        return scheduleSheets

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

            teams = self.getTeamSheet(sheets)
            days = self.getScheduleSheets(sheets)

            hours = await self.getOpenSlots(spreadsheet, days, sheetId)
            
            print(hours)

            event = self.getCurrentEvent(hours[0][0])

            hourDic = {
                timestamp: 0 for timestamp in np.arange(int(event['startAt']/1000), int(event['rankingAnnounceAt']/1000), 3600)}

            for hour in hours:
                hourDic[hour[0]] += hour[1]

            return list(hourDic.values()), event

        except HttpError as err:
            print(err)


    async def getOpenSlots(self, spreadsheet, titles, sheetId):

        column = '1:1'
        lookups = []
        for title in titles:
            lookups.append(f'{title}!{column}')
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
                'p1', 'p2', 'p3', 'p4', 'p5', 'epoch']]

            playerIndexes = [i for i, x in enumerate(valueSets) if x in [
                'p1', 'p2', 'p3', 'p4', 'p5']]

            minVal = min(indexes)
            maxVal = max(indexes)

            timestampIndex = valueSets.index('epoch') - minVal

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
                if len(row[0]) > 0 and row[0][0] == ' ':
                    continue
                values = [x for i, x in enumerate(
                    row) if x != '' and i + minVal in playerIndexes]
                if len(values) == 0 or (timestampIndex >= len(row)):
                    continue
                hours.append([int(row[timestampIndex]), 5 - len(values)])

        return hours


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
            if len(row) < maxVal - minVal + 1:
                continue
            if row[nameIndex - minVal] and str(row[idIndex - minVal]).strip() == userid:
                names.append(row[nameIndex - minVal])

        names = [x for x in names]
        return names


    async def getUsers(self, spreadsheet, titles, sheetId, names):

        query = '1:1'
        lookups = []
        for title in titles:
            lookups.append(f'{title}!{query}')

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

            timestampIndex = valueSets.index('epoch')

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

            # Q4:Q27
            # P4:P27

            teams = self.getTeamSheet(sheets)
            days = self.getScheduleSheets(sheets)

            names = await self.getNames(spreadsheet, teams, sheetId, userid)

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

            hourDic = {k: v for k, v in sorted(
                hourDic.items(), key=lambda item: item[0])}
            return list(hourDic.values())

        except HttpError as err:
            print(err)


    async def getLookups(self, spreadsheet, titles, sheetId) -> list:
        query = '1:1'
        lookups = []
        for title in titles:
            lookups.append(f'{title}!{query}')
        result = await self.lookupBatch(spreadsheet, lookups, sheetId)
        valueRanges = result.get('valueRanges', [])

        combinedLookup = []

        for title, values in zip(titles, valueRanges):
            values = values.get('values', [])[0]
            values = '|'.join(values).lower().split('|')

            if 'epoch' not in values:
                return None

            timestampIndex = values.index('epoch')
            checkInIndex = values.index('check-in')

            combinedLookup += [
                f'{title}!{self.excel_cols(timestampIndex + 1)}3:{self.excel_cols(timestampIndex + 1)}300',
                f'{title}!{self.excel_cols(checkInIndex + 1)}3:{self.excel_cols(checkInIndex + 1)}300'
            ]

        return combinedLookup


    async def getVals(self, spreadsheet, combinedLookup, titles, sheetId) -> dict:
        timestampDict = {}
        result = await self.lookupBatch(spreadsheet, combinedLookup, sheetId)

        values = result.get('valueRanges', 0)
        values = [x['values'] if 'values' in x else [] for x in values]
        
        timestamps = []
        checkIns = []
        
        for i in range(0, len(values), 2):
            timestampLookup = values[i]
            checkInLookup = values[i + 1]
            
            for i, timestamp in enumerate(timestampLookup):
                timestamps.append(timestamp[0])
                if i >= len(checkInLookup):
                    checkIns.append('')
                elif len(checkInLookup[i]) < 1:
                    checkIns.append('')
                else:
                    checkIns.append(checkInLookup[i][0])
                

        values = zip(timestamps, checkIns)

        for timestamp, checkIn in values:

            if checkIn != '':

                if int(timestamp) in timestampDict:
                    timestampDict[int(timestamp)].addCheckIn(checkIn)
                else:
                    timestampDict[int(timestamp)] = TimeData(
                        int(timestamp), [], [checkIn])
            else:
                pass
            
        ##Don't Ask
        pattern = re.compile("^P[0-5].+$")
        numPattern = re.compile('[0-9]+')
        
        for title in titles:
            result = await self.lookupBatch(spreadsheet, [f'{title}!AC17', f'{title}!AC22'], sheetId)
            values = result.get('valueRanges', 0)
            values = [x['values'] if 'values' in x else [] for x in values]
            
            for value in values:
                value = value[0][0]
                timestamps = re.findall(r'<t:[0-9]+:R>', value.replace('\r', ''))
                if len(timestamps) == 0:
                    continue
                try:
                    timestamp = int(timestamps[0][3:-3])
                    players = []
                    for line in value.split('\r'):
                        if not pattern.match(line):
                            continue
                        
                        name = f'{line[4:line.index("|")].strip()}'
                        if line[line.index("|") + 1:line.rfind("-")].strip():
                            name += f' - {line[line.index("|") + 1:line.rfind("-")].strip()}'
                        nums = numPattern.findall(line[line.rfind('-'):])
                        
                        lead = 0 if len(nums) < 1 else nums[0]
                        team = 0 if len(nums) < 2 else nums[1]
                        bp = 0 if len(nums) < 3 else nums[2]
                        player = Player(name, lead, team, bp)
                        players.append(player)

                    if timestamp in timestampDict:
                        timestampDict[timestamp].addPlayer(players)
                    else:
                        timestampDict[timestamp] = TimeData(
                        timestamp, [players], [])
                except Exception as e:
                    print(e)

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

            lookups = await self.getLookups(spreadsheet, titles, sheetId)
            timestampDict = await self.getVals(spreadsheet, lookups, titles, sheetId)

            # Sorts keys
            myKeys = list(timestampDict.keys())
            myKeys.sort()
            return {i: timestampDict[i] for i in myKeys if timestampDict[i].hasPlayers()}

        except HttpError as err:
            print(err)
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
from classes.Player import Player
from classes.TimeData import TimeData

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
EVENTPATH = '../RoboNene/sekai_master/events.json'

ROOMS = ["g1", "g2"]
TEAMS = ["player db"]


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
    filteredStr = re.sub('[^0-9]', '', bp)
    val = int(filteredStr)
    if (val < 1000):
        val *= 1000
    return val

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
            if sheet['properties']['title'].lower().strip() in TEAMS:
                teams = sheet['properties']['title']

            if sheet['properties']['title'].lower().strip() in ROOMS:
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

    column = '1:1'
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
            'p1', 'p2', 'p3', 'p4', 'p5', 'epoch']]

        playerIndexes = [i for i, x in enumerate(valueSets) if x in [
            'p1', 'p2', 'p3', 'p4', 'p5']]

        minVal = min(indexes)
        maxVal = max(indexes)

        timestampIndex = valueSets.index('epoch') - minVal

        minColumn = excel_cols(minVal + 1)
        maxColumn = excel_cols(maxVal + 1)

        combinedLookup = f'{title}!{minColumn}3:{maxColumn}300'

        lookups.append(combinedLookup)
        timestampIndexes.append(timestampIndex)
        playerIndexesList.append(playerIndexes)

    result = await lookupBatch(spreadsheet, lookups, sheetId)

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

    query = '1:1'
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

        timestampIndex = valueSets.index('epoch')

        combinedLookup = f'{title}!{excel_cols(minVal + 1)}3:{excel_cols(maxVal + 1)}300'
        timestampLookup = f'{title}!{excel_cols(timestampIndex + 1)}3:{excel_cols(timestampIndex + 1)}300'

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
            if sheet['properties']['title'].lower().strip() in TEAMS:
                teams = sheet['properties']['title']

            if sheet['properties']['title'].lower().strip() in ROOMS:
                days.append(sheet['properties']['title'])

        queue = []

        names = await getNames(spreadsheet, teams, sheetId, userid)
        
        print(names)

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

        hourDic = {k: v for k, v in sorted(
            hourDic.items(), key=lambda item: item[0])}
        return list(hourDic.values())

    except HttpError as err:
        print(err)


async def getLookups(spreadsheet, titles, sheetId) -> list:
    query = '1:1'
    lookups = []
    for title in titles:
        lookups.append(f'{title}!{query}')
    result = await lookupBatch(spreadsheet, lookups, sheetId)
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
            f'{title}!{excel_cols(timestampIndex + 1)}3:{excel_cols(timestampIndex + 1)}300',
            f'{title}!{excel_cols(checkInIndex + 1)}3:{excel_cols(checkInIndex + 1)}300'
        ]

    return combinedLookup


async def getVals(spreadsheet, combinedLookup, titles, sheetId) -> dict:
    timestampDict = {}
    result = await lookupBatch(spreadsheet, combinedLookup, sheetId)

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
    for title in titles:
        result = await lookupBatch(spreadsheet, [f'{title}!AC17', f'{title}!AC22'], sheetId)
        values = result.get('valueRanges', 0)
        values = [x['values'] if 'values' in x else [] for x in values]
        
        for value in values:
            value = value[0][0]
            timestamps = re.findall(r'<t:[0-9]+:R>', value)
            if len(timestamps) > 0:
                try:
                    timestamp = int(timestamps[0][3:-3])
                    if timestamp in timestampDict:
                        timestampDict[timestamp].addOrder(value)
                    else:
                        timestampDict[timestamp] = TimeData(
                            timestamp, [value], [])
                except Exception as e:
                    print(e)
                    continue ##Don't Ask Again

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
            if sheet['properties']['title'].lower().strip() in ROOMS:
                titles.append(sheet['properties']['title'])

        lookups = await getLookups(spreadsheet, titles, sheetId)
        timestampDict = await getVals(spreadsheet, lookups, titles, sheetId)

        # Sorts keys
        myKeys = list(timestampDict.keys())
        myKeys.sort()
        return {i: timestampDict[i] for i in myKeys}

    except HttpError as err:
        print(err)

import asyncio
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os 
import re
import numpy as np
import rapidjson


class BaseRequest:
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    EVENTPATH = 'config/events.json'
    
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
        val = int(filteredStr);
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
        Gets all open slots for the current event
        
        Returns:
        List [index]
        """

        return None
        
async def getOpenSlots(spreadsheet, titles, sheetId):
    """
    Gets open slots for a specific page in the spreadsheet

    Args:
        spreadsheet (_type_): _description_
        titles (_type_): _description_
        sheetId (_type_): _description_
    """
    return None

async def getNames(spreadsheet, title, sheetId, userid):

    """
    Gets all names from the "teams" page of a spreadsheet
    """
    return None

async def getUsers(spreadsheet, titles, sheetId, names):
    """
    Gets all users from the schedule that matches the given list of names

    Args:
        spreadsheet (_type_): _description_
        titles (_type_): _description_
        sheetId (_type_): _description_
        names (_type_): _description_
    """
    return None

async def getUserVals(creds, sheetId, userid, eventData):
    """
    Gets all placements of a specific user from all pages of a spreadsheet
    
    Returns:
    List [index]
    """
    
    return None

async def getLookups(spreadsheet, titles, sheetId) -> list:
    """Gets required lookups for checkin and order lookups

    Args:
        spreadsheet (_type_): _description_
        titles (_type_): _description_
        sheetId (_type_): _description_

    Returns:
        list: _description_
    """

async def getVals(spreadsheet, combinedLookup, colIndexes, sheetId) -> dict:
    """
    Gets all order and check in values for all given lookups
    """

async def main(creds, sheetId) -> dict:
    """
    Gets all orders and check ins for all users
    
    Returns:
    Dict {timestamp: {orders: [], checkIns: []}}
    """
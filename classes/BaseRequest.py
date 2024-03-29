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


class BaseRequest():
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    EVENTPATH = '../RoboNene/sekai_master/events.json'
    CLIENT_COUNT = 3
    CURRENT_CLIENT = 0
    CLIENTS = ['token1.json', 'token2.json', 'token3.json']
    TOKEN_FP = 'tokens'
    
    def __init__(self):
        pass
        
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
        
    async def lookupBatch(self, spreadsheet, queries, sheetId):
        return spreadsheet.values().batchGet(spreadsheetId=sheetId,
                                        ranges=queries).execute()
        
    def getTeamSheet(self, sheets):
        return None
    
    def getScheduleSheets(self, sheets):
        return None

    def parseBp(self, bp):
        if (str == ''):
            return 0
        filteredStr = re.sub('[^0-9]', '', bp)
        val = int(filteredStr);
        if (val < 1000):
            val *= 1000
        return val
        
    
    def refreshCreds(self):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        
        client = self.CLIENTS[self.CURRENT_CLIENT]
        client = f"{self.TOKEN_FP}/{client}"
        self.CURRENT_CLIENT += 1
        self.CURRENT_CLIENT %= self.CLIENT_COUNT
        
        creds = None
        
        if os.path.exists(client):
            creds = Credentials.from_authorized_user_file(client, self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            print('refreshing creds')
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(client, 'w') as token:
                token.write(creds.to_json())
                
        creds = Credentials.from_authorized_user_file(client, self.SCOPES)
                
        return creds


    def getCurrentEvent(self, timestamp):
        timestamp = int(timestamp * 1000)
        print(timestamp)
        with open(self.EVENTPATH, 'r', encoding='utf8') as f:
            eventData = rapidjson.load(f)[::]
        f.close()
        for i, event in enumerate(eventData):
            if event['startAt'] <= timestamp and event['closedAt'] >= timestamp:
                if timestamp > event['aggregateAt']:
                    if i < len(eventData) - 1:
                        return eventData[i + 1]
                return event

        return None
    
    async def getID(self, creds, sheetId):
        """
        Gets the ID of the sheet (if exists)
        
        Returns:
        String
        """

        try:
            service = build('sheets', 'v4', credentials=creds)

            # Call the Sheets API
            spreadsheet = service.spreadsheets()
            sheet_metadata = spreadsheet.get(spreadsheetId=sheetId).execute()
            sheets = sheet_metadata.get('sheets', '')
            
            # Q4:Q27
            # P4:P27
            if 'id' not in [sheet['properties']['title'] for sheet in sheets]:
                return None
            
            result = await self.lookup(spreadsheet, 'id!A1', sheetId)
            myKeys = result.get('values', [])
            if not myKeys:
                return None
            
            return myKeys[0][0]
        
        except HttpError as err:
            print(err)

    async def getAllOpenSlots(self, creds, sheetId, eventData):
        """
        Gets all open slots for the current event
        
        Returns:
        List [index]
        """

        return None
        
    async def getOpenSlots(self, spreadsheet, titles, sheetId):
        """
        Gets open slots for a specific page in the spreadsheet

        Args:
            spreadsheet (_type_): _description_
            titles (_type_): _description_
            sheetId (_type_): _description_
        """
        return None

    async def getNames(self, spreadsheet, title, sheetId, userid):

        """
        Gets all names from the "teams" page of a spreadsheet
        """
        return None

    async def getUsers(self, spreadsheet, titles, sheetId, names):
        """
        Gets all users from the schedule that matches the given list of names

        Args:
            spreadsheet (_type_): _description_
            titles (_type_): _description_
            sheetId (_type_): _description_
            names (_type_): _description_
        """
        return None

    async def getUserVals(self, creds, sheetId, userid, eventData):
        """
        Gets all placements of a specific user from all pages of a spreadsheet
        
        Returns:
        List [index]
        """
        
        return None
    
    async def getDiscordID(self, creds, sheetId, username):
        """
        Gets the discord ID of a user from the "teams" page of a spreadsheet
        
        Returns:
        String
        """
        
        return None

    async def getLookups(self, spreadsheet, titles, sheetId) -> list:
        """Gets required lookups for checkin and order lookups

        Args:
            spreadsheet (_type_): _description_
            titles (_type_): _description_
            sheetId (_type_): _description_

        Returns:
            list: _description_
        """

    async def getVals(self, spreadsheet, combinedLookup, colIndexes, sheetId) -> dict:
        """
        Gets all order and check in values for all given lookups
        """

    async def main(self, creds, sheetId) -> dict:
        """
        Gets all orders and check ins for all users
        
        Returns:
        Dict {timestamp: {orders: [], checkIns: []}}
        """
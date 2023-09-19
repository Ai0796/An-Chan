import time
import rapidjson
import os

class Config():
    def __init__(self, path = 'config/serverconfig.json'):
        self.data = {}
        self.path = path
        self.load()

    def load(self):
        try:
            if os.path.exists(self.path) == False:
                self.data = {}
                return
            
            with open(self.path, 'r', encoding='utf8') as f:
                self.data = rapidjson.load(f)
                f.close()
        except:
            self.data = {}

    def save(self):
        print('Saving config')
        with open(self.path, 'w', encoding='utf8') as f:
            rapidjson.dump(self.data, f, indent=4)
            f.close()

    def get(self, serverid):
        serverid = str(serverid)
        return self.data[serverid]

    def set(self, serverid, key, value):
        serverid = str(serverid)
        self.data[serverid][key] = value
        
        ## Update last update time
        self.data[serverid]['lastUpdate'] = int(time.time())
        
        self.save()

    def createServer(self, serverid):
        
        serverid = str(serverid)
        
        if serverid in self.data.keys():
            return
        
        self.data[serverid] = {
            'checkIn': None,
            'requestType': 'An',
            'sheetId': None,
            'lastUpdate': int(time.time())
        }
        self.save()

    def getCheckInChannel(self, serverid):
        return self.get(serverid)['checkIn']

    def setCheckInChannel(self, serverid, channelid):
        self.set(serverid, 'checkIn', channelid)

    def getRequestType(self, serverid):
        return self.get(serverid)['requestType']

    def setRequestType(self, serverid, requestType):
        self.set(serverid, 'requestType', requestType)

    def getSheetId(self, serverid):
        return self.get(serverid)['sheetId']

    def setSheetId(self, serverid, sheetId):
        self.set(serverid, 'sheetId', sheetId)

    def getTime(self, serverid):
        return self.get(serverid)['lastUpdate']
    
    def getServers(self):
        return list(self.data.keys())
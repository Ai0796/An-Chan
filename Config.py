import time
import rapidjson
import os

import sqlalchemy
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

DEFAULT_CONFIG = {
    'checkIn': None,
    'requestType': 'An',
    'sheetId': None,
    'managerCheckIn': None,
    'managerPing': None,
    'lastUpdate': int(time.time()),
    'runners': [],
}

Base = declarative_base()

class Server(Base):
    __tablename__ = 'Server'
    serverid = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    checkIn = sqlalchemy.Column(sqlalchemy.BigInteger)
    requestType = sqlalchemy.Column(sqlalchemy.String)
    sheetId = sqlalchemy.Column(sqlalchemy.String)
    managerCheckIn = sqlalchemy.Column(sqlalchemy.BigInteger)
    managerPing = sqlalchemy.Column(sqlalchemy.BigInteger)
    lastUpdate = sqlalchemy.Column(sqlalchemy.BigInteger)
    lastPing = sqlalchemy.Column(sqlalchemy.BigInteger)
    
    runners = relationship('Runner', back_populates='server')
    
class Runner(Base):
    __tablename__ = 'Runner'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    serverid = sqlalchemy.Column(sqlalchemy.String, sqlalchemy.ForeignKey('Server.serverid'))
    runner = sqlalchemy.Column(sqlalchemy.String)
    
    server = relationship('Server', back_populates='runners')

class Config():
    def __init__(self, path = 'config/serverconfig.json'):
        self.data = {}
        self.path = path
        
        engine = sqlalchemy.create_engine('sqlite:///config/serverconfig.db')
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        self.session = Session()
        
    def createServer(self, serverID):
        
        if self.get(serverID) != None:
            return -1
        
        server = Server(
            serverid = serverID,
            checkIn = None,
            requestType = 'An',
            sheetId = None,
            managerCheckIn = None,
            managerPing = None,
            lastUpdate = int(time.time())
        )
        
        self.session.add(server)
        return 0
    
    def get(self, serverid):
        serverid = str(serverid)
        return self.session.query(Server).filter(Server.serverid == serverid).first()
    
    def set(self, serverid, key, value):
        serverid = str(serverid)
        server = self.get(serverid)
        setattr(server, key, value)
        self.session.commit()
        
        return 0
        
    def pruneServers(self, idSet):
        for server in self.session.query(Server).all():
            if server.serverid not in idSet:
                instance = self.session.query(Server).filter(Server.serverid == server.serverid).first()
                self.session.delete(instance)

    def getCheckInChannel(self, serverid):
        return self.get(serverid).checkIn

    def setCheckInChannel(self, serverid, channelid):
        self.set(serverid, 'checkIn', channelid)
        
    def setManagerCheckInChannel(self, serverid, channelid):
        self.set(serverid, 'managerCheckIn', channelid)
        
    def getManagerCheckInChannel(self, serverid):
        return self.get(serverid).managerCheckIn
    
    def setManagerPing(self, serverid, roleID):
        self.set(serverid, 'managerPing', roleID)
        
    def getManagerPing(self, serverid):
        return self.get(serverid).managerPing

    def getRequestType(self, serverid):
        return self.get(serverid).requestType

    def setRequestType(self, serverid, requestType):
        self.set(serverid, 'requestType', requestType)

    def getSheetId(self, serverid):
        return self.get(serverid).sheetId

    def setSheetId(self, serverid, sheetId):
        self.set(serverid, 'sheetId', sheetId)

    def getTime(self, serverid):
        return self.get(serverid).lastUpdate
    
    def getServers(self):
        return [server.serverid for server in self.session.query(Server).all()]
    
    def getLastPing(self, serverid):
        if 'lastPing' not in self.get(serverid):
            return 0
        return self.get(serverid).lastPing
    
    def setLastPing(self, serverid, pingTime):
        self.set(serverid, 'lastPing', pingTime)
        
    def addRunner(self, serverID, runner):
        serverID = str(serverID)
        arr = self.session.query(Runner).filter(Runner.serverid == serverID).all()
        for run in arr:
            if run.runner == runner:
                return -1
        
        runner = Runner(serverid = serverID, runner = runner)
        self.session.add(runner)
        
        arr = self.session.query(Runner).filter(Runner.serverid == serverID).all()
        
        return [run.runner for run in arr]
        
    def getRunners(self, serverID):
        serverID = str(serverID)
        arr = self.session.query(Runner).filter(Runner.serverid == serverID).all()
        return [run.runner for run in arr]
    
    def removeRunner(self, serverID, runner):
        serverID = str(serverID)
        arr = self.session.query(Runner).filter(Runner.serverid == serverID).all()

        for run in arr:
            if run.runner == runner:
                self.session.delete(run)
                break
            
    def commit(self):
        self.session.commit()
            
if __name__ == '__main__':
    ## Testing
    config = Config()
    
    instance = config.session.query(Server).filter(Server.sheetId == '1lt6ni5bF1bacV9wS9S_NDgtjBZqijLR5UG4BW1b3FHM').all()
    for i in instance:
        if i.serverid == '422851664236642307' or i.serverid == '1075866706578264107':
            continue
        config.session.delete(i)
    config.session.commit()
    # config.session.delete(instance)
    # config.session.commit()
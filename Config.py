import time
import rapidjson
import os

import sqlalchemy
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import PendingRollbackError, SQLAlchemyError
from sqlalchemy import select

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
    def __init__(self, path='config/serverconfig.json'):
        self.data = {}
        self.path = path

        self.engine = create_async_engine('sqlite+aiosqlite:///config/serverconfig.db')
        self.async_session = async_sessionmaker(bind=self.engine, expire_on_commit=False)

    async def createServer(self, serverID):
        async with self.async_session() as session:
            async with session.begin():
                result = await session.execute(select(Server).where(Server.serverid == str(serverID)))
                server = result.scalars().first()
                if server:
                    return -1
                server = Server(serverid=str(serverID), lastUpdate=int(time.time()))
                session.add(server)
            await session.commit()
            return 0

    async def get(self, serverid):
        async with self.async_session() as session:
            try:
                result = await session.execute(select(Server).where(Server.serverid == str(serverid)))
                return result.scalars().first()
            except SQLAlchemyError:
                return None

    async def set(self, serverid, key, value):
        async with self.async_session() as session:
            try:
                result = await session.execute(select(Server).where(Server.serverid == str(serverid)))
                server = result.scalars().first()
                if server:
                    setattr(server, key, value)
                    setattr(server, 'lastUpdate', int(time.time()))
                    await session.commit()
            except SQLAlchemyError:
                await session.rollback()

    async def pruneServers(self, idSet):
        async with self.async_session() as session:
            result = await session.execute(select(Server))
            for server in result.scalars().all():
                if server.serverid not in idSet:
                    await session.delete(server)
            await session.commit()

    async def getCheckInChannel(self, serverid):
        server = await self.get(serverid)
        return server.checkIn if server else None

    async def setCheckInChannel(self, serverid, channelid):
        await self.set(serverid, 'checkIn', channelid)

    async def setManagerCheckInChannel(self, serverid, channelid):
        await self.set(serverid, 'managerCheckIn', channelid)

    async def getManagerCheckInChannel(self, serverid):
        server = await self.get(serverid)
        return server.managerCheckIn if server else None

    async def setManagerPing(self, serverid, roleID):
        await self.set(serverid, 'managerPing', roleID)

    async def getManagerPing(self, serverid):
        server = await self.get(serverid)
        return server.managerPing if server else None

    async def getRequestType(self, serverid):
        server = await self.get(serverid)
        return server.requestType if server else None

    async def setRequestType(self, serverid, requestType):
        await self.set(serverid, 'requestType', requestType)

    async def getSheetId(self, serverid):
        server = await self.get(serverid)
        return server.sheetId if server else None

    async def setSheetId(self, serverid, sheetId):
        await self.set(serverid, 'sheetId', sheetId)

    async def getTime(self, serverid):
        server = await self.get(serverid)
        return server.lastUpdate if server else None

    async def getServers(self):
        async with self.async_session() as session:
            result = await session.execute(select(Server))
            return [server.serverid for server in result.scalars().all()]

    async def getLastPing(self, serverid):
        server = await self.get(serverid)
        return server.lastPing if server else None

    async def setLastPing(self, serverid, pingTime):
        await self.set(serverid, 'lastPing', pingTime)

    async def addRunner(self, serverID, runner):
        serverID = str(serverID)
        async with self.async_session() as session:
            result = await session.execute(select(Runner).where(Runner.serverid == serverID))
            existing = result.scalars().all()
            if any(r.runner == runner for r in existing):
                return -1
            new_runner = Runner(serverid=serverID, runner=runner)
            session.add(new_runner)
            await session.commit()
            result = await session.execute(select(Runner).where(Runner.serverid == serverID))
            return [r.runner for r in result.scalars().all()]

    async def getRunners(self, serverID):
        serverID = str(serverID)
        async with self.async_session() as session:
            result = await session.execute(select(Runner).where(Runner.serverid == serverID))
            return [r.runner for r in result.scalars().all()]

    async def removeRunner(self, serverID, runner):
        serverID = str(serverID)
        async with self.async_session() as session:
            result = await session.execute(select(Runner).where(Runner.serverid == serverID))
            runners = result.scalars().all()
            for run in runners:
                if run.runner == runner:
                    await session.delete(run)
                    break
            await session.commit()

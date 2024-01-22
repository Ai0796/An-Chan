class TimeData:
    """
    Contains information for a single timestamp
    """
    
    def __init__(self, timestamp, players, checkIns, managers=[]):
        self.timestamp = timestamp
        self.orders = players
        self.checkIns = checkIns
        self.managers = managers
        
    def addPlayer(self, player):
        self.orders.append(player)
        
    def addCheckIn(self, player):
        self.checkIns.append(player)
        
    def addManager(self, manager):
        self.managers.append(manager)
        
    def getOrders(self):
        return self.orders
        
    def getCheckIns(self):
        return self.checkIns
    
    def getManagers(self):
        return self.managers
    
    def add(self, timeData):
        self.orders.extend(timeData.orders)
        self.checkIns.extend(timeData.checkIns)
        self.managers.extend(timeData.managers)
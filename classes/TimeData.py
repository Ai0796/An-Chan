class TimeData:
    """
    Contains information for a single timestamp
    """
    
    def __init__(self, timestamp, players, checkIns):
        self.timestamp = timestamp
        self.orders = players
        self.checkIns = checkIns
        
    def addPlayer(self, player):
        self.orders.append(player)
        
    def addCheckIn(self, player):
        self.checkIns.append(player)
        
    def getOrders(self):
        return self.orders
        
    def getCheckIns(self):
        return self.checkIns
    
    def add(self, timeData):
        self.orders.extend(timeData.orders)
        self.checkIns.extend(timeData.checkIns)
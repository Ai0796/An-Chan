class Player:
    
    maxLength = 40
    mobileLength = 31
    
    def __init__(self, name, lead, team, bp):
        self.name = name.strip()
        self.lead = int(lead)
        self.team = int(team)
        self.isv = lead + (team - lead)/5.0
        self.bp = bp
        
    def __str__(self):
        return f'{self.name} | {self.lead}/{self.team}/{self.bp/1000:.0f}k'
    
    def tostr(self, mobile, maxLength):
        str = f' | {self.lead}/{self.team}/{self.bp/1000:.0f}k'
        length = len(str) + maxLength
        
        if (mobile):
            padding = self.mobileLength - length + 1
        else:
            padding = self.maxLength - length + 1

        str = f'{self.name}' + ' ' * (maxLength - len(self.name))
        
        if padding < 0:
            str = str[:padding]
            
        
        str += f' | {self.lead}/{self.team}/{self.bp/1000:.0f}k'
            
        return str 
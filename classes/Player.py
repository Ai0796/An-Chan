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
    
    def tostr(self, mobile, maxLength, runners=[]):
        
        if 'event' in self.name.lower():
            str = f' | Event'
        else:
            str = f' | {self.lead}/{self.team}/{self.bp/1000:.0f}k'
        
        if 'event' in self.name.lower():
            str = f' | Event'
        
        length = len(str) + maxLength
        
        if (mobile):
            padding = self.mobileLength - length + 1
        else:
            padding = self.maxLength - length + 1

        str = f'{self.name}' + ' ' * (maxLength - len(self.name))
        
        if padding < 0:
            str = str[:padding]
        
        if 'event' in self.name.lower() or any(runner.lower() in self.name.lower() for runner in runners):
            str += f' | Event'
        else:
            str += f' | {self.lead}/{self.team}/{self.bp/1000:.0f}k'
            
        return str 
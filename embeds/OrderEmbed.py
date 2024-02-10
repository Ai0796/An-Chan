import discord
from scripts.getCurrentEvent import getCurrentEvent

class OrderEmbed(discord.ui.View):
    
    CCMULTIPLIERS = [
        0.8561771017814248,
        0.8655341690522911,
        1.225714646826631,
        0.9301984550432184,
        1.042237531812819,
        1.0801380954836162
    ]
    
    def __init__(self, data, timestamps, index, runners):

        super().__init__(timeout=60)
        self.timestamps = timestamps
        self.data = data
        self.index = index
        self.runners = runners
        self.p1encore = False
        self.mobile = False
        self.roomIndex = 0
        self.team = 0

    async def on_timeout(self):
        embed = self.generateEmbed(self.timestamps[self.index])
        await self.message.edit(embed=embed, view=None)

    def generateEmbed(self, timestamp):

        orders = self.data[timestamp].getOrders()
        players = orders[min(self.roomIndex, len(orders) - 1)]
        if (self.team * 5 >= len(players)):
            self.team = 0
        players = players[self.team * 5: self.team * 5 + 5]
        p1encore = self.p1encore
        mobile = self.mobile

        EnvyOrder = [3, 2, 1, 4, 5]
        EncoreOrder = [3, 2, 4, 5]

        event = getCurrentEvent()
        if event != None:
            if event['id'] % 3 == 0:
                EnvyOrder = [2, 1, 4, 5, 3]
                EncoreOrder = [2, 4, 5, 3]

        runnerBP = 0
        runnerISV = 0
        encoreIndex = -1
        encoreBP = 0
        linkedOrder = []
        totalisv = 0
        avgbp = sum([player.bp for player in players]) / len(players)

        players.sort(key=lambda x: x.isv)

        for player in players:
            if ('event' in player.name.lower()):
                runnerBP = max(runnerBP, player.bp)
                runnerISV = max(runnerISV, player.isv)
                continue
                
            for runner in self.runners:
                if (runner.lower() in player.name.lower()):
                    runnerBP = max(runnerBP, player.bp)
                    runnerISV = max(runnerISV, player.isv)

        for i in range(len(players)):
            player = players[i]

            if ('encore' in player.name.lower()):
                encoreIndex = i
                break
            
            if player.bp > runnerBP and player.bp > encoreBP:
                encoreBP = player.bp
                encoreIndex = i

        if (not p1encore or encoreIndex == -1):
            for i in range(len(EnvyOrder)):
                linkedOrder.append([EnvyOrder[i], players[i]])
            maxBP = max([x.bp for x in players])
            encoreISV = [x.isv for x in players if x.bp == maxBP][0]
            totalisv += ((encoreISV / 100.0) + 1) * self.CCMULTIPLIERS[5]
        else:
            encoreUser = players.pop(encoreIndex)
            for i in range(len(EncoreOrder)):
                linkedOrder.append([EncoreOrder[i], players[i]])
            linkedOrder.append([1, encoreUser])
            players.append(encoreUser)
            totalisv += ((encoreUser.isv / 100.0) + 1) * self.CCMULTIPLIERS[5]

        linkedOrder = sorted(linkedOrder, key=lambda x: x[0])
        
        for i in range(len(linkedOrder)):
            player = linkedOrder[i][1]
            totalisv += ((player.isv / 100.0) + 1) * self.CCMULTIPLIERS[i]

        maxLength = 0
        for name in [x[1].name for x in linkedOrder]:
            maxLength = max(maxLength, len(name))

        Order1 = linkedOrder[0][1].tostr(mobile, maxLength, self.runners)
        Order2 = linkedOrder[1][1].tostr(mobile, maxLength, self.runners)
        Order3 = linkedOrder[2][1].tostr(mobile, maxLength, self.runners)
        Order4 = linkedOrder[3][1].tostr(mobile, maxLength, self.runners)
        Order5 = linkedOrder[4][1].tostr(mobile, maxLength, self.runners)

        order = f'<t:{timestamp}:f>\r```P1: {Order1} \rP2: {Order2} \rP3: {Order3} \rP4: {Order4} \rP5: {Order5}\r\rISV: {totalisv:.2f} | BP: {avgbp / 1000:.0f}k```'

        if (getCurrentEvent()['id'] % 3 == 0):
            playerNames = [x.name for x in players]
            playerNames = sorted(playerNames, key=lambda x: x.lower())
            oldPlayerNames = []
            
            if (timestamp - 3600 in self.data):
                orders = self.data[timestamp - 3600].getOrders()
                players = orders[min(self.roomIndex, len(orders) - 1)]
                if (self.team * 5 >= len(players)):
                    self.team = 0
                players = players[self.team * 5: self.team * 5 + 5]
                oldPlayerNames = [x.name for x in players]
                
            existingNames = []
            for name in playerNames:
                if (name in oldPlayerNames):
                    existingNames.append(name)
                    
            for name in existingNames:
                playerNames.remove(name)
                playerNames.append(name)
            
            order += f'\r```DC Order:\r{" > ".join(playerNames)}```'
        
        order += f'\rSwap <t:{timestamp}:R>'
        
        return discord.Embed(
            title=f'Room Order {min(self.roomIndex, len(orders) - 1) + 1}', 
            description=order, 
            color = 0x00BBDC)

    @discord.ui.button(label='Previous', style=discord.ButtonStyle.primary, emoji='⬅️')
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        if (self.index > 0):
            self.index -= 1
        embed = self.generateEmbed(self.timestamps[self.index])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.primary, emoji='➡️')
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if (self.index < len(self.timestamps) - 1):
            self.index += 1
        embed = self.generateEmbed(self.timestamps[self.index])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='P1 Encore', style=discord.ButtonStyle.primary, emoji='🔄')
    async def encore(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.p1encore = not self.p1encore
        embed = self.generateEmbed(self.timestamps[self.index])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Mobile', style=discord.ButtonStyle.primary, emoji='📱')
    async def mobile(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.mobile = not self.mobile
        embed = self.generateEmbed(
            self.timestamps[self.index])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Change Rooms', style=discord.ButtonStyle.primary, emoji='1️⃣')
    async def changeRoom(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.roomIndex = (
            self.roomIndex + 1) % len(self.data[self.timestamps[self.index]].orders)
        embed = self.generateEmbed(
            self.timestamps[self.index])
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label='Switch BP', style=discord.ButtonStyle.primary, emoji='🔀', row=2)
    async def switchBP(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.team += 1
        embed = self.generateEmbed(
            self.timestamps[self.index])
        await interaction.response.edit_message(embed=embed, view=self)
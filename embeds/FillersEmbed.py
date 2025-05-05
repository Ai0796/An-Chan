import discord


class FillersEmbed(discord.ui.View):

    def __init__(self, users, role):
        super().__init__(timeout=None)
        self.users = list(users)
        self.message = None
        self.role = role
        self.slice = 0

    def set_message(self, message):
        self.message = message

    def generateEmbed(self):

        HOUR = 3600

        users = self.users[self.slice * 25:self.slice* 25 + 25]
        returnStr = ''
        returnStr += 'Total Fillers: ' + str(len(self.users)) + '\n'
            
        for user in users:
            returnStr += f'<@{user}>\n'

        embed = discord.Embed(
            title=f'Fillers {self.slice * 25 + 1}-{self.slice * 25 + len(users)} (Page {self.slice + 1})', 
            description=returnStr, 
            color = 0x00BBDC)

        return embed 

    @discord.ui.button(label='Prev', style=discord.ButtonStyle.primary, emoji='⬅️')
    async def previousDay(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.slice -= 1
        if self.slice < 0:
            self.slice = len(self.users) // 25 - 1
        await interaction.response.edit_message(embed=self.generateEmbed(), view=self)

    @discord.ui.button(label='Next', style=discord.ButtonStyle.primary, emoji='➡️')
    async def nextDay(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.slice += 1
        if self.slice >= len(self.users) // 25:
            self.slice = 0
        await interaction.response.edit_message(embed=self.generateEmbed(), view=self)
        
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.success, emoji='✅')
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.edit_message(content=f'Fillers have been confirmed, giving role <@&{self.role.id}>', view=None, embed=None)
        role = interaction.guild.get_role(self.role.id)
        
        given = 0
        for user in self.users:
            user = interaction.guild.get_member(int(user))
            if user:
                print(user)
                try:
                    await user.add_roles(role)
                    given += 1
                except discord.Forbidden:
                    await interaction.followup.send(f'Could not give role to <@{user}>',allowed_mentions=discord.AllowedMentions.none())
                    
        await interaction.followup.send(f'Gave role to {given} users')
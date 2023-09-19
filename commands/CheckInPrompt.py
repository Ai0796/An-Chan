from embeds.OpenSlotsEmbed import OpenSlotsEmbed
from scripts.getCurrentEvent import getCurrentEvent
from discord.ext import commands
import discord


class CheckInPrompt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    checkInPrompt = discord.SlashCommandGroup('checkinprompt',
                                            'Commands related to the check in prompts')

    @checkInPrompt.command(name="add", description="Adds a check in prompt to the queue")
    async def add(self, ctx, prompt: discord.Option(
        discord.SlashCommandOptionType.string,
        required=True,
        description="The prompt (max 1000 characters)"
    )):
        """Adds a check in prompt to the queue"""
        prompt = prompt[:1000]
        prompt += f'\r\r- {ctx.author.display_name}\r\r'
        self.bot.checkInPrompts[ctx.guild.id].append(prompt)
        await ctx.respond(f"Check In Prompt added to queue, current position: {len(self.bot.checkInPrompts[ctx.guild.id])}", ephemeral=True)

    @checkInPrompt.command(name="view", description="Shows all prompts in the queue")
    async def view(self, ctx):
        """Shows all prompts in the queue"""
        prompts = self.bot.checkInPrompts[ctx.guild.id]
        if len(prompts) == 0:
            await ctx.respond("There are no prompts in the queue", ephemeral=True)
            return
        embed = discord.Embed(title="Check In Prompts", description="All prompts in the queue (up to 10)")
        for i, prompt in enumerate(prompts):
            embed.add_field(name=f"Prompt {i + 1}", value=prompt[:99], inline=False)
        await ctx.respond(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(CheckInPrompt(bot))

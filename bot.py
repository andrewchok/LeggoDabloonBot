# bot.py

# imports
import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

# declaring intents
intents = discord.Intents(
    messages=True, 
    message_content=True, 
    guilds=True
    )

# loading environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DEVELOPER = os.getenv('DEV_ID')

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f'{bot.user.name} is connected to the following guild:\n'
        f'[{guild.name}(id: {guild.id})]'
    )

@bot.command(name='99', help='Responds with a random quote from Brooklyn 99')
@commands.has_role('botadmin')
async def nine_nine(ctx):
    brooklyn_99_quotes = [
        'I\'m the human form of the 💯 emoji.',
        'Bingpot!',
        (
            'Cool. Cool cool cool cool cool cool cool, '
            'no doubt no doubt no doubt no doubt.'
        ),
    ]

    response = random.choice(brooklyn_99_quotes)
    await ctx.send(response)

@bot.command(name='roll', help='Simulates rolling dice: <number_of_dice> <number_of_sides>')
@commands.has_role('admin')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    await ctx.send(', '.join(dice))

# handle error for events
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')


# connect client to discord
bot.run(TOKEN)


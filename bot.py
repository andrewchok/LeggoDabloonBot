# bot.py
import os

import discord
from dotenv import load_dotenv

# declaring intents
intents = discord.Intents(messages=True, guilds=True)

# loading environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    print(
        f'message from {message.guild.id}:{message.guild.name}'
    )
    
# connect client to discord
client.run(TOKEN)


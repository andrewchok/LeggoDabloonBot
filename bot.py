# bot.py

#%% imports
import os
import random
import datetime
import discord
from discord.ext import commands
from discord.ext.commands import Context
from dotenv import load_dotenv

#%% declaring intents
intents = discord.Intents(
    messages=True, 
    message_content=True, 
    guilds=True
    )

#%% loading environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DEVELOPER = os.getenv('DEV_ID')

#%% Class Logic
class Item:
    # Constructor
    def __init__(self, id, price):
        self.id = id                                # unique Id of item
        self.owner = "None"                         # owner of the item (discord id)
        self.cooldown = datetime.datetime.now()     # cooldown after being retrieved before can be sold
        self.stock_timer = datetime.datetime.now()  # time until the price for this increases/decreases
        self.price = price                          # price of item
        print(
            f'{datetime.datetime.now()}:: Item constructed = id - {self.id}, price - {self.price}'
        )

    # Methods
    def ItemReceivedBy(self, owner, cooldown, stock_timer):
        self.owner = owner
        self.cooldown = datetime.datetime.now() + cooldown
        self.stock_timer = datetime.datetime.now() + stock_timer
        print(
            f'{datetime.datetime.now()}:: ItemReceivedBy {self.owner}, cooldown - {self.cooldown}, stock timer - {self.stock_timer}'
        )

    def DisplayInfo(self):
        return 'id - ' + str(self.id) + ' price - ' + str(self.price)

class Store:
    # Variables
    closing_time = datetime.datetime.now() + datetime.timedelta(hours=2)

    # Constructor
    def __init__(self):
        # create 6 items and store them in SQL
        self.item1 = Item(1, 10)
        print(
            f'{datetime.datetime.now()}:: Store constructed Items - {self.item1.DisplayInfo()}'
        )

    # Methods
    def Buy(self, id, owner):
        # search for item by id among items avaiable then set owner
        Item.ItemReceivedBy(self, owner, datetime.timedelta(minutes=10), datetime.timedelta(minutes=30))
        print(
            f'{datetime.datetime.now()}:: Item {id} was bought.'
        )

    def TimeUntilClosing(self):
        print(
            f'{datetime.datetime.now()}:: TimeUntilClosing - {self.closing_time - datetime.datetime.now()}'
        )
        return self.closing_time - datetime.datetime.now()

#%% Bot Logic
temp_store = Store()

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f'{bot.user.name} is connected to the following guild:\n'
        f'[{guild.name}(id: {guild.id})]'
    )

@bot.command(name='buy', help='')
@commands.has_role('botadmin')
async def buy_item(ctx: Context, item_id: int):
    global temp_store
    temp_store.Buy(item_id, ctx.author.id)

    await ctx.send("buying item " + str(item_id))
    print(
        f'{datetime.datetime.now()}:: buy_item command triggered {ctx.author}'
    )

@bot.command(name='store', help='')
@commands.has_role('botadmin')
async def show_store(ctx: Context):
    global temp_store
    await ctx.send('Store closes in ' + str(temp_store.TimeUntilClosing()))
    print(
        f'{datetime.datetime.now()}:: show_store command triggerd {ctx.author}'
    )

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    encounter_chance = random.randint(0,1)

    if(encounter_chance):
        await message.channel.send('<:smilingcat:941188757376340029>: Hello Traveler! This is Dabloon Cat please take these `4` dabloons.')
        
        print(
            f'{datetime.datetime.now()}:: {message.author} tiggered a dabloon gift event'
        )
# handle error for events
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')


# connect client to discord
bot.run(TOKEN)


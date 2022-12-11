# bot.py

#%% imports
import os
import random
import datetime
import discord
from discord import Message
from discord.ext import commands
from discord.ext.commands import Context, Bot
from dotenv import load_dotenv
from getpass import getpass
from mysql.connector import connect, Error
import aiomysql
import requests
import json

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
CMD_PREFIX = os.getenv('CMD_PREFIX')
MYSQL_USERNAME = os.getenv('MYSQL_USERNAME')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
SHOP_ID = os.getenv('SHOP_ID')
UNOWNED_ID = os.getenv('UNOWNED_ID')
TO_DELETE_ID = os.getenv('TO_DELETE_ID')
RANDOM_WORD_URL = os.getenv('RANDOM_WORD_URL')

#%% Utility Logic
def FormatTimeToString(delta_time : datetime.timedelta):
    time_message = ""
    if int(delta_time.seconds / 3600):
        time_message += str(int(delta_time.seconds / 3600)) + ' hrs '
    if int((delta_time.seconds % 3600) / 60):
        time_message += str(int((delta_time.seconds % 3600) / 60)) + ' mins '
    if delta_time.seconds % 60:
        time_message += str(delta_time.seconds % 60) + ' secs'
    return time_message

def MentionAuthor(author):
    authorId = str(author.id)
    return '<@' + authorId + '>'

def IsShopOpen():
    global shop_time
    return shop_time > datetime.datetime.now()

def get_words(num):
    response=requests.get(RANDOM_WORD_URL+str(num)).text
    return json.loads(response)

#%% MySQL Logic
class Database:
    def field(command, *values):
        try:
            with connect(
                host="localhost",
                user=MYSQL_USERNAME,
                password=MYSQL_PASSWORD,
                database="leggo_dabloons_db"
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(command, tuple(values))
                    fetch = cursor.fetchone()
                    if fetch is not None:
                        return fetch[0]
                    return                    
        except Error as e:
            print("Error:")
            print(e)

    def record(command, *values):
        try:
            with connect(
                host="localhost",
                user=MYSQL_USERNAME,
                password=MYSQL_PASSWORD,
                database="leggo_dabloons_db"
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(command, tuple(values))
                    return cursor.fetchone()                                    
        except Error as e:
            print("Error:")
            print(e)
    
    def records(command, *values):
        try:
            with connect(
                host="localhost",
                user=MYSQL_USERNAME,
                password=MYSQL_PASSWORD,
                database="leggo_dabloons_db"
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(command, tuple(values))
                    return cursor.fetchall()                                    
        except Error as e:
            print("Error:")
            print(e)

    def column(command, *values):
        try:
            with connect(
                host="localhost",
                user=MYSQL_USERNAME,
                password=MYSQL_PASSWORD,
                database="leggo_dabloons_db"
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(command, tuple(values))
                    return [item[0] for item in cursor.fetchall()]                                   
        except Error as e:
            print("Error:")
            print(e)

    def execute(command, *values):
        try:
            with connect(
                host="localhost",
                user=MYSQL_USERNAME,
                password=MYSQL_PASSWORD,
                database="leggo_dabloons_db"
            ) as connection:
                with connection.cursor() as cursor:
                    cursor.execute(command, tuple(values))
                    connection.commit()                                  
        except Error as e:
            print("Error:")
            print(e)

try:
    with connect(
        host="localhost",
        user=MYSQL_USERNAME,
        password=MYSQL_PASSWORD,
        database="leggo_dabloons_db"
    ) as connection:
        print("Successful MySQL Connection Established!")
        print(connection)

        # insert_item_query = """
        # INSERT INTO item (name, price, cooldown, stock_timer)
        # VALUES ( %s, %s, %s, %s )
        # """
        # item_records= [
        #     ("test1", 10, str(datetime.timedelta(minutes=5)), str(datetime.timedelta(minutes=8))),
        #     ("test2", 10, str(datetime.timedelta(minutes=2)), str(datetime.timedelta(minutes=4))),
        #     ("test3", 10, str(datetime.timedelta(minutes=3)), str(datetime.timedelta(minutes=2))),
        #     ("test4", 10, str(datetime.timedelta(minutes=1)), str(datetime.timedelta(minutes=1)))
        # ]
        with connection.cursor() as cursor:
            # cursor.executemany(insert_item_query, item_records)
            cursor.execute("SELECT * FROM user")
            for item in cursor.fetchall():
                print(item)
            connection.commit()
            
except Error as e:
    print("Error:")
    print(e)
    
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
    closing_time = datetime.datetime.now() + datetime.timedelta(minutes=2)

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
encounter_reset_time = datetime.timedelta(minutes=40)
shop_open_duration = datetime.timedelta(hours=6)
shop_time = datetime.datetime.strptime(Database.field("SELECT encounter_cooldown FROM user WHERE id = {}".format(SHOP_ID)), "%Y-%m-%d %H:%M:%S.%f")
doon_cat_emoji = '<:dablooncatboon:1050790287699611768>'
shop_cat_emoji = '<:storecat:1050792540158312489>'

bot = Bot(command_prefix=CMD_PREFIX, intents=intents)

@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f'{bot.user.name} is connected to the following guild:\n'
        f'[{guild.name}(id: {guild.id})]'
    )

@bot.command(name='test', help='')
@commands.has_role('botadmin')
async def test_stuff(ctx: Context):
    words = get_words(6)
    for word in words:
        print(word)
    print(
            f'{datetime.datetime.now()}:: test_stuff command triggered {ctx.author}'
        )

@bot.command(name='buy', help='')
@commands.has_role('botadmin')
async def buy_item(ctx: Context, item_id: int):
    global shop_cat_emoji

    if not IsShopOpen():
        print(
            f'{datetime.datetime.now()}:: buy_item command triggered {ctx.author} :: Store not open'
        )

    user_recently_bought = Database.record("SELECT 1 FROM recent_shoppers WHERE user_id = {}".format(ctx.author.id))
    if(user_recently_bought):        
        await ctx.send('''
                    {}: Hey! You have already bought an item {}!\n{}: One per customer!
                    '''.format(shop_cat_emoji, MentionAuthor(ctx.author), shop_cat_emoji)
                    )
    else:
        await ctx.send("bought item " + str(item_id))
    print(
        f'{datetime.datetime.now()}:: buy_item command triggered {ctx.author}'
    )

@bot.command(name='sell', help='')
@commands.has_role('botadmin')
async def sell_item(ctx: Context, item_id: int):

    await ctx.send("sold item " + str(item_id))
    print(
        f'{datetime.datetime.now()}:: buy_item command triggered {ctx.author}'
    )

@bot.command(name='shop', help='')
@commands.has_role('botadmin')
async def show_store(ctx: Context):  
    global shop_time
    global shop_cat_emoji
    current_time = datetime.datetime.now()

    if IsShopOpen():
        shop_items = Database.records("SELECT name, price, id FROM item WHERE id IN (SELECT item_id FROM ownership WHERE user_id = {})".format(SHOP_ID))
        shop_cat_message = "{}: Welcome! I have wares if you have dabloons:\n".format(shop_cat_emoji)
        for item in shop_items:
            print(f'{item}')
            shop_cat_message += "    **{}** dabloons : **{}**  `id[{}]`\n".format(item[1], item[0], item[2])
        print(f'first item name {shop_items[0][0]} : {shop_items[0][1]}')
    else:
        await ctx.send('{}: Store not open!'.format(shop_cat_emoji))
        return

    # if shop is closed, then reopen it
    if shop_time < current_time and False:
        shop_time = datetime.datetime.now() + shop_open_duration
        Database.execute("UPDATE user SET encounter_cooldown = \"{}\" WHERE id = 1".format(str(shop_time)))

    shop_cat_message += '\nShop closes in `{}`'.format(FormatTimeToString(shop_time - datetime.datetime.now()))
    await ctx.send(shop_cat_message)

    print(
        f'{datetime.datetime.now()}:: show_store command triggerd {ctx.author}'
    )

@bot.command(name='bag', help='')
async def show_inventory(ctx: Context):
    dabloons = Database.field("SELECT dabloons FROM user WHERE id = {}".format(ctx.author.id))
    if not dabloons:
        dabloons = 0
    await ctx.send(MentionAuthor(ctx.author) + ' you have `{}` dabloons'.format(dabloons))
    print(
        f'{datetime.datetime.now()}:: show_inventory command triggerd {ctx.author}'
    )

@bot.event
async def on_message(message):
    # Enable when Debugging
    # if discord.utils.get(message.author.roles, name="botadmin") is None:
    #     return

    if message.author == bot.user:
        return

    # if message was a command then do not trigger a chance for event
    if message.content.startswith(CMD_PREFIX):
        await bot.process_commands(message)
        return

    currentTime = datetime.datetime.now()
    encounter_chance = random.randint(1,15)

    if(encounter_chance == 1):        
        user_exist = Database.record("SELECT 1 FROM user WHERE id = {}".format(message.author.id))
        global doon_cat_emoji
        if(user_exist):
            user_encounter_cooldown = datetime.datetime.strptime(
                Database.field("SELECT encounter_cooldown FROM user WHERE id = {}".format(message.author.id)),
                "%Y-%m-%d %H:%M:%S.%f"
            )
            if user_encounter_cooldown < currentTime:
                dabloon_amount = random.randint(1,10)
                await message.channel.send('''
                    {}: Hello again Traveler {}!\n{}: Safe travels please take these `{}` dabloons.
                    '''.format(doon_cat_emoji, MentionAuthor(message.author), doon_cat_emoji, dabloon_amount)
                    )
                Database.execute("UPDATE user SET dabloons = dabloons + {}, encounter_cooldown = \"{}\" WHERE id = {}".format(dabloon_amount, str(datetime.datetime.now() + encounter_reset_time), message.author.id))
                print(
                    f'{datetime.datetime.now()}:: {message.author} tiggered a dabloon gift event'
                )
            else:
                print(
                        f'{datetime.datetime.now()}:: {message.author} encounter on cooldown - {FormatTimeToString(user_encounter_cooldown-currentTime)}'
                )
        else:
            dabloon_amount = 4
            await message.channel.send('''
                {}: Hello Traveler{}!\n{}: You have met Dabloon Cat please take these `{}` dabloons.
                '''.format(doon_cat_emoji, MentionAuthor(message.author), doon_cat_emoji, dabloon_amount)
                )
            Database.execute("INSERT INTO user (id, name, dabloons, encounter_cooldown) VALUES ({}, \"{}\", {}, \"{}\")".format(message.author.id, message.author, dabloon_amount, str(datetime.datetime.now() + encounter_reset_time)))
            print(
                f'{datetime.datetime.now()}:: {message.author} tiggered a dabloon gift event'
            )
    else:
        print(
            f'{datetime.datetime.now()}:: {message.author}  encounter failed the roll with {encounter_chance}'
        )
    

# handle error for events
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')


# connect client to discord
bot.run(TOKEN)


# %%

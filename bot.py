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
from enum import Enum

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

def CloseShop():
    current_time = datetime.datetime.now()
    Database.execute("UPDATE user SET encounter_cooldown = \"{}\" WHERE id = {}".format(str(current_time), SHOP_ID))
    global shop_time
    shop_time = datetime.datetime.strptime(Database.field("SELECT encounter_cooldown FROM user WHERE id = {}".format(SHOP_ID)), "%Y-%m-%d %H:%M:%S.%f")
    Database.execute("DELETE FROM recent_shoppers")
    Database.execute("UPDATE ownership SET user_id = {} WHERE user_id = {}".format(TO_DELETE_ID, SHOP_ID)) 

def GetRandomWords(num):
    response=requests.get(RANDOM_WORD_URL+str(num)).text
    return json.loads(response)

#%% MySQL Logic
class Database:
    tax = 5

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

    def create_store():
        if IsShopOpen():
            print(
                f'{datetime.datetime.now()}:: create_store triggered - shop already open'
            )
            return
        
        try:
            with connect(
                host="localhost",
                user=MYSQL_USERNAME,
                password=MYSQL_PASSWORD,
                database="leggo_dabloons_db"
            ) as connection:
                print("Populating Shop...")
                item_names = GetRandomWords(6)
                general_price = 15

                insert_item_query = """
                INSERT INTO item (name, price, cooldown, stock_timer, max_price)
                VALUES ( %s, %s, %s, %s, %s )
                """
                item_records = []
                for name in item_names:
                    item_records.append((
                        name, 
                        general_price, 
                        str(datetime.timedelta(minutes=(random.randint(30,90)))),
                        StockType.AGGRO.value,
                        random.randint(general_price - Database.tax, general_price * 2)
                        ))

                with connection.cursor() as cursor:
                    cursor.executemany(insert_item_query, item_records)
                    connection.commit()
                    
                    for name in item_names:                
                        cursor.execute("INSERT INTO ownership (item_id, user_id) VALUES ((SELECT id FROM item WHERE name = \"{}\"), {})".format(name, SHOP_ID))
                        print("Attaching ownership of item - {}".format(name))

                    global shop_time
                    shop_time = datetime.datetime.now() + shop_open_duration
                    cursor.execute("UPDATE user SET encounter_cooldown = \"{}\" WHERE id = {}".format(str(shop_time), SHOP_ID))
                    connection.commit()
                    print("Done Populating Shop!")
                    
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
        with connection.cursor() as cursor:
            # cursor.executemany(insert_item_query, item_records)
            cursor.execute("SELECT * FROM user")
            for item in cursor.fetchall():
                print(item)
            connection.commit()
            
except Error as e:
    print("Error:")
    print(e)
    
#%% Enum Logic
class StockType(Enum):
    INVALID = 0
    AGGRO = 1
    BALANCED = 2
    SLOW = 3


#%% Bot Logic
encounter_reset_time = datetime.timedelta(minutes=30)
shop_open_duration = datetime.timedelta(hours=6)
shop_time = datetime.datetime.strptime(Database.field("SELECT encounter_cooldown FROM user WHERE id = {}".format(SHOP_ID)), "%Y-%m-%d %H:%M:%S.%f")
doon_cat_emoji = '<:dablooncatboon:1050790287699611768>'
shop_cat_emoji = '<:storecat:1050792540158312489>'

bot = Bot(command_prefix=CMD_PREFIX, intents=intents, case_insensitive=True)

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
    global shop_cat_emoji

    if not IsShopOpen():
        await ctx.send("No shop open.")
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
        user_dabloons = Database.field("SELECT dabloons FROM user WHERE id = {}".format(ctx.author.id))
        item_price = Database.field("SELECT price FROM item WHERE id = {}".format(item_id))
        if user_dabloons >= item_price:
            user_dabloons -= item_price
            # update dabloons after purchase
            Database.execute("UPDATE user SET dabloons = {} WHERE id = {}".format(user_dabloons, ctx.author.id))                
            # update the ownership of the item
            Database.execute("UPDATE ownership SET user_id = {} WHERE item_id = (SELECT id FROM item WHERE id = {})".format(ctx.author.id, item_id)) 
            # update recent shoppers
            Database.execute("INSERT INTO recent_shoppers (user_id) VALUES ({})".format(ctx.author.id))
            # update cooldown time from its delta time, and take tax cut
            item_cooldown = datetime.datetime.strptime(Database.field("SELECT cooldown FROM item WHERE id = {}".format(item_id)), '%H:%M:%S')
            current_time = datetime.datetime.now()
            item_cooldown = current_time + datetime.timedelta(hours=item_cooldown.hour, minutes=item_cooldown.minute, seconds=item_cooldown.second)
            Database.execute("UPDATE item SET cooldown = \"{}\", price = price - {} WHERE id = {}".format(str(item_cooldown), Database.tax, item_id))
            # check if sold out then close shop            
            shop_items = Database.records("SELECT name, price, id FROM item WHERE id IN (SELECT item_id FROM ownership WHERE user_id = {})".format(SHOP_ID))
            if not shop_items:
                CloseShop()

        await ctx.send("{}: Thank you for your dabloons {}!\n`bought item {}`".format(MentionAuthor(ctx.author), shop_cat_emoji, item_id))
    print(
        f'{datetime.datetime.now()}:: buy_item command triggered {ctx.author}'
    )

@bot.command(name='sell', help='')
@commands.has_role('botadmin')
async def sell_item(ctx: Context, item_id: int):
    is_owner = Database.record("SELECT * FROM ownership WHERE user_id  = {} AND item_id = {}".format(ctx.author.id, item_id))
    if is_owner:
        selling_item = Database.record("SELECT name, price, cooldown FROM item WHERE id  = {}".format(item_id))
        current_time = datetime.datetime.now()
        item_cooldown = datetime.datetime.strptime(selling_item[2], "%Y-%m-%d %H:%M:%S.%f")
        if item_cooldown < current_time:
            # update the dabloons from selling
            Database.execute("UPDATE user SET dabloons = dabloons + {} WHERE id = {}".format(selling_item[1], ctx.author.id))                
            # update item ownership to unowned
            Database.execute("UPDATE ownership SET user_id = {} WHERE item_id = {}".format(UNOWNED_ID, item_id))                
            
            await ctx.send("{} sold item **{}** `id[{}]` for **{}** dabloons".format(MentionAuthor(ctx.author), selling_item[0], item_id, selling_item[1]))
        else:
            await ctx.send("{} item is on `{}` cooldown cannot be sold!".format(MentionAuthor(ctx.author), FormatTimeToString(item_cooldown-current_time)))
    else:
        await ctx.send("{} You do not own that item!".format(MentionAuthor(ctx.author)))
    print(
        f'{datetime.datetime.now()}:: sell_item command triggered {ctx.author}'
    )

@bot.command(name='shop', help='')
@commands.has_role('botadmin')
async def show_store(ctx: Context):  
    global shop_time
    global shop_cat_emoji
    current_time = datetime.datetime.now()

    if IsShopOpen():
        shop_items = Database.records("SELECT name, price, id FROM item WHERE id IN (SELECT item_id FROM ownership WHERE user_id = {})".format(SHOP_ID))
        if not shop_items:
            CloseShop()
            await ctx.send('{}: {} Store not open! Come back later..'.format(shop_cat_emoji, MentionAuthor(ctx.author)))
            return

        shop_cat_message = "{}: Welcome! I have wares if you have dabloons:\n".format(shop_cat_emoji)
        for item in shop_items:
            print(f'{item}')
            shop_cat_message += "    **{}** dabloons : **{}**  `id[{}]`\n".format(item[1], item[0], item[2])
    else:
        await ctx.send('{}: {} Store not open! Come back later..'.format(shop_cat_emoji, MentionAuthor(ctx.author)))
        return

    shop_cat_message += '\nShop closes in `{}`'.format(FormatTimeToString(shop_time - datetime.datetime.now()))
    await ctx.send(shop_cat_message)

    print(
        f'{datetime.datetime.now()}:: show_store command triggerd {ctx.author}'
    )

@bot.command(name='bag', help='')
async def show_inventory(ctx: Context):
    current_time = datetime.datetime.now()
    dabloons = Database.field("SELECT dabloons FROM user WHERE id = {}".format(ctx.author.id))
    if not dabloons:
        dabloons = 0
    user_items = Database.records("SELECT name, price, id, cooldown FROM item WHERE id IN (SELECT item_id FROM ownership WHERE user_id = {})".format(ctx.author.id))
    bag_message = MentionAuthor(ctx.author) + ' you have `{}` dabloons\n'.format(dabloons)
    for item in user_items:
        item_cooldown = datetime.datetime.strptime(item[3], "%Y-%m-%d %H:%M:%S.%f")
        bag_message += "    **{}** dabloons : **{}**  `id[{}]`    *{}*\n".format(item[1], item[0], item[2], ("READY" if item_cooldown < current_time else "..."))
    await ctx.send(bag_message)
    print(
        f'{datetime.datetime.now()}:: show_inventory command triggerd {ctx.author}'
    )

@bot.command('cd', help='check your encounter cooldown')
async def show_encounter_cooldown(ctx: Context):    
    currentTime = datetime.datetime.now()
    user_encounter_cooldown = datetime.datetime.strptime(
        Database.field("SELECT encounter_cooldown FROM user WHERE id = {}".format(ctx.author.id)),
        "%Y-%m-%d %H:%M:%S.%f"
    )
    if user_encounter_cooldown < currentTime:  
        await ctx.send(MentionAuthor(ctx.author) + ' you are ready for an encounter!')
    else:
        await ctx.send(MentionAuthor(ctx.author) + ' you have `{}` cooldown on your encounter.'.format(FormatTimeToString(user_encounter_cooldown-currentTime)))
    print(
        f'{datetime.datetime.now()}:: show_encounter_cooldown command triggerd {ctx.author}'
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
           
    user_exist = Database.record("SELECT 1 FROM user WHERE id = {}".format(message.author.id))
    global doon_cat_emoji
    if(user_exist):
        user_encounter_cooldown = datetime.datetime.strptime(
            Database.field("SELECT encounter_cooldown FROM user WHERE id = {}".format(message.author.id)),
            "%Y-%m-%d %H:%M:%S.%f"
        )
        if user_encounter_cooldown < currentTime:            
            encounter_chance = random.randint(1,4)
            if(encounter_chance == 1): 
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
                Database.execute("UPDATE user SET encounter_cooldown = \"{}\" WHERE id = {}".format(str(datetime.datetime.now() + encounter_reset_time), message.author.id))
                print(
                    f'{datetime.datetime.now()}:: {message.author}  encounter failed the roll with {encounter_chance} - put on cooldown'
                )
        else:
            print(
                    f'{datetime.datetime.now()}:: {message.author} encounter on cooldown - {FormatTimeToString(user_encounter_cooldown-currentTime)}'
            )
    # first time gift
    else:
        encounter_chance = random.randint(1,5)
        if(encounter_chance == 1): 
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
    
#%% Test Area
@bot.command(name='test', help='')
@commands.has_role('botadmin')
async def test_stuff(ctx: Context):
    Database.create_store()
    print(
            f'{datetime.datetime.now()}:: test_stuff command triggered {ctx.author}'
        )

@bot.command(name='t_close', help='')
@commands.has_role('botadmin')
async def test_close_store(ctx: Context):
    CloseShop()
    print(
            f'{datetime.datetime.now()}:: test_close_store command triggered {ctx.author}'
        )

@bot.command(name='t_delete_pending', help='')
@commands.has_role('botadmin')
async def test_delete_pending_items(ctx: Context):
    Database.execute("DELETE FROM item WHERE id IN (SELECT item_id FROM ownership WHERE user_id = {})".format(TO_DELETE_ID)) 
    print(
            f'{datetime.datetime.now()}:: test_delete_pending_items command triggered {ctx.author}'
        )    

# handle error for events
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('You do not have the correct role for this command.')


# connect client to discord
bot.run(TOKEN)


# %%

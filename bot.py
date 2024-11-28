import discord
from discord.ext import commands
import logging
import os
import mysql.connector
import time
import asyncio

def db_connect():
    conn = None
    while conn is None:
        try:
            conn = mysql.connector.connect(
                host="db",
                user=mysql_user,
                password=mysql_password,
                database="nickeljar",
                autocommit=True,
                connect_timeout=10
            )
            break
        except mysql.connector.Error as err:
            print(f"Failed to connect to MySQL server: {err}")
            time.sleep(1)
        except Exception as e:
            print(f"MySQL error occured: {e}")
            exit(1)

    logger.info("Connected to MySQL")
    print("Connected to MySQL")
    return conn

data_path = 'data'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.getLogger('discord.http').setLevel(logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)
handler = logging.FileHandler(filename=f'{data_path}/discord.log', encoding='utf-8', mode='a')

dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

# load token from env
discord_token = os.getenv('DISCORD_TOKEN')
if discord_token is None:
    print("DISCORD_TOKEN not found")
    logger.error("DISCORD_TOKEN not found")
    exit(1)

# load mysql creds from env
mysql_user = os.getenv('MYSQL_USER')
if mysql_user is None:
    print("MYSQL_USER not found")
    logger.error("MYSQL_USER not found")
    exit(1)
mysql_password = os.getenv('MYSQL_PASSWORD')
if mysql_password is None:
    print("MYSQL_PASSWORD not found")
    logger.error("MYSQL_PASSWORD not found")
    exit(1)

# load all word lists in memory (ext is txt)
words = []
for file in os.listdir(f'{data_path}/'):
    if file.endswith('.txt'):
        with open(f'{data_path}/{file}', 'r') as f:
            for line in f:
                words.append(line.strip())
print(f"Loaded {len(words)} word(s)")
logger.info(f"Loaded {len(words)} word(s)")

conn = db_connect()

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'We have logged in as {bot.user}')
    logger.info(f'We have logged in as {bot.user}')

    # run the birthday thread
    asyncio.create_task(wait_for_bdays())

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    
    if message.author == bot.user:
        return

    content = message.content.lower()
    # remove punctuation
    content = ''.join(e for e in content if e.isalnum() or e.isspace())

    # TODO convert all numbers to words
    # content = content.replace('0', 'o').replace('1', 'i')

    conn = globals().get('conn')

    vulgarity = {}
    for word in content.split():
        if word in words:
            # add_nickel(message)
            vulgarity[word] = vulgarity.get(word, 0) + 1
    
    if not conn.is_connected():
        conn = db_connect()

    # round about way, but it works out
    cursor = conn.cursor()
    for word, count in vulgarity.items():
        # oh lol. would only add once for each word
        for _ in range(count):
            cursor.execute("insert into nickels (guild, username, word) VALUES (%s, %s, %s)",
                           (message.guild.name, message.author.name, word)
                          )
    cursor.close()

    nickels = sum(vulgarity.values())
    if nickels > 1:
        await message.channel.send(f"{message.author} added {nickels} nickels to the jar")
    elif nickels == 1:
        await message.channel.send(f"{message.author} added a nickel to the jar")

bot.run(discord_token, log_handler=None)
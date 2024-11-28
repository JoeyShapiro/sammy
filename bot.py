import discord
from discord.ext import commands
import logging
import os
from transformers import AutoTokenizer

data_path = '.'
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

messages = []

# load token from env
discord_token = os.getenv('DISCORD_TOKEN')
if discord_token is None:
    # try to load .env
    with open('.env', 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            if key == 'DISCORD_TOKEN':
                discord_token = value
                break
    
if discord_token is None:
    print("DISCORD_TOKEN not found")
    logger.error("DISCORD_TOKEN not found")
    exit(1)

tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
eos = tokenizer.sep_token
max_tokens = 128
print(f"Tokenizer: {tokenizer}; EOS: {eos}; Max tokens: {max_tokens}")
logger.info(f"Tokenizer: {tokenizer}; EOS: {eos}; Max tokens: {max_tokens}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'We have logged in as {bot.user}')
    logger.info(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    messages = globals()['messages']

    try:
        messages.append(message)
        tokens = []
        i = 0
        for msg_iter in messages[::-1]:
            tokens += tokenizer.tokenize(msg_iter.content+eos)
            if len(tokens) > max_tokens:
                break
            i += 1
        messages = messages[len(messages)-i-1:]
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Error: {e}")

    if message.author == bot.user:
        return
    
    if should_talk(tokens):
        await message.channel.send(f"The total tokens are {len(tokens)}.")

def should_talk(tokens) -> bool:
    return len(tokens) > max_tokens

bot.run(discord_token, log_handler=None)
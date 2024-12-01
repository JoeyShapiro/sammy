import discord
from discord.ext import commands
import logging
import os
from transformers import AutoTokenizer, pipeline, set_seed
import torch
import time
import ollama

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

def get_env(env_key):
    env_val = os.getenv(env_key)
    if env_val is None:
        # try to load .env
        with open('.env', 'r') as f:
            for line in f:
                key, value = line.strip().split('=')
                if key == env_key:
                    env_val = value
                    break
        
    if env_val is None:
        print(f"{env_key} not found")
        logger.error(f"{env_key} not found")
        exit(1)

# load token from env
discord_token = get_env('DISCORD_TOKEN')
ollama_url = get_env('OLLAMA_URL')

tokenizer = AutoTokenizer.from_pretrained('gpt2')
eos = tokenizer.eos_token
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
    
    if '<@1311363791157465179>' in message.content:
        message.content = message.content.replace('<@1311363791157465179>', 'Sammy')

        async with message.channel.typing():
            print("Generating response...")
            start = time.time()
            model = ollama.OllamaAPI(base_url=ollama_url)
            
            # Generate text
            response = model.generate(
                model="llama3.2:latest",
                prompt=message.content,
                system="You are a female chatter named Sammy. you are an egirl who occastionally adds japenese into your messages.",
                options={
                    "temperature": 0.7,
                    "max_tokens": 100
                }
            )
            print(f"Response took {time.time()-start:.2f}s.")
        await message.channel.send(response)
    
    if should_talk(tokens):
        await message.channel.send(f"The total tokens are {len(tokens)}.")

def should_talk(tokens) -> bool:
    return len(tokens) > max_tokens

bot.run(discord_token, log_handler=None)
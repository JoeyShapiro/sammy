import discord
from discord.ext import commands
import logging
import os
from transformers import AutoTokenizer, pipeline, set_seed
import torch
import requests
import json

class OllamaAPI:
    def __init__(self, base_url="http://localhost:11434"):
        """Initialize Ollama API client.
        
        Args:
            base_url (str): Base URL for Ollama API (default: http://localhost:11434)
        """
        self.base_url = base_url.rstrip('/')
        
    def generate(self, model, prompt="", system="", options=None):
        """Generate a response using the specified model.
        
        Args:
            model (str): Name of the model to use
            prompt (str): The prompt to send to the model
            system (str): System prompt to prepend
            options (dict): Additional model parameters like temperature
            
        Returns:
            dict: JSON response from the API
        """
        endpoint = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
        }
        
        if options:
            payload.update(options)
        
        response = requests.post(endpoint, json=payload)

        reply = ''
        for data in response.content.split(b'\n'):
            message = json.loads(data)
            reply += message['response']

            if message['done']:
                break
            
        return reply
    
    def list_models(self):
        """List all available models.
        
        Returns:
            dict: JSON response containing available models
        """
        endpoint = f"{self.base_url}/api/tags"
        response = requests.get(endpoint)
        return response.json()
    
    def pull_model(self, model="llama2"):
        """Pull a model from Ollama's registry.
        
        Args:
            model (str): Name of the model to pull
            
        Returns:
            dict: JSON response indicating pull status
        """
        endpoint = f"{self.base_url}/api/pull"
        payload = {"name": model}
        response = requests.post(endpoint, json=payload)
        return response.json()


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

tokenizer = AutoTokenizer.from_pretrained('gpt2')
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
    
    if '<@1311363791157465179>' in message.content:
        message.content = message.content.replace('<@1311363791157465179>', 'Sammy')

        try:
            print("Generating response...")
            ollama = OllamaAPI()
            
            # Generate text
            response = ollama.generate(
                model="llama3.2:latest",
                prompt=message.content,
                system="You are a chatter named Sammy",
                options={
                    "temperature": 0.7,
                    "max_tokens": 100
                }
            )
            await message.channel.send(response)
        except Exception as e:
            print(f"Error: {e}")
            logger.error(f"Error: {e}")
    
    if should_talk(tokens):
        await message.channel.send(f"The total tokens are {len(tokens)}.")

def should_talk(tokens) -> bool:
    return len(tokens) > max_tokens

bot.run(discord_token, log_handler=None)
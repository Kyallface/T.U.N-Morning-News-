import discord
import openai
import asyncio
import os
from discord.ext import tasks

openai.api_key = os.getenv("OPENAI_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def get_message_from_gpt():
    response = openai.ChatCompletion.create(
        model="gpt-5",  # or gpt-4o-mini if you like cheap
        messages=[{"role": "system", "content": "Give me today's daily wisdom"}]
    )
    return response.choices[0].message["content"]

@tasks.loop(hours=24)
async def daily_post():
    channel = client.get_channel(CHANNEL_ID)
    msg = await get_message_from_gpt()
    await channel.send(msg)

@client.event
async def on_ready():
    daily_post.start()

client.run(DISCORD_TOKEN)

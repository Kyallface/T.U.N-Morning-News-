import discord
from openai import OpenAI
import asyncio
import os
from discord.ext import tasks
from dotenv import load_dotenv

# Load .env values
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Set up clients
discord_intents = discord.Intents.default()
discord_client = discord.Client(intents=discord_intents)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Load persona from file
with open("persona.txt", "r", encoding="utf-8") as f:
    persona_instructions = f.read().strip()

# Get message from OpenAI
async def get_message_from_gpt():
    response = openai_client.chat.completions.create(
        model="gpt-5",  # or gpt-4.1
        messages=[
            {"role": "system", "content": persona_instructions},
            {"role": "user", "content": "Give me today's daily message."}
        ]
    )
    return response.choices[0].message.content

# Task loop
@tasks.loop(hours=24)
async def daily_post():
    channel = discord_client.get_channel(CHANNEL_ID)
    try:
        msg = await get_message_from_gpt()
    except Exception as e:
        msg = f"⚠️ Error fetching message: {e}"

    # Split message on speaker names
    parts = []
    current = []
    for line in msg.splitlines():
        if line.strip().startswith(("***Jessica Hale*** :", "***Steve Bakersfield*** :")):
            if current:
                parts.append("\n".join(current))
                current = []
        current.append(line)
    if current:
        parts.append("\n".join(current))

    # Send each part with a leading linebreak, truncated if needed
    for part in parts:
        if len(part) > 2000:
            part = part[:1997] + "..."
        await channel.send("\n" + part)


# On ready
@discord_client.event
async def on_ready():
    print(f"Logged in as {discord_client.user}")
    daily_post.start()

# Run bot
discord_client.run(DISCORD_TOKEN)

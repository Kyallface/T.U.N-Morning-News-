import discord
from openai import OpenAI
import os
from dotenv import load_dotenv
import asyncio
from audio_utils import generate_audio
from datetime import datetime


# Load .env values
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Flags
LIVE_FLAG = False   # set True for production
AUDIO_FLAG = True   # generate audio
TEXT_FLAG = False   # future option

if LIVE_FLAG:
    CHANNEL_ID = int(os.getenv("CHANNEL_ID_LIVE"))
else:
    CHANNEL_ID = int(os.getenv("CHANNEL_ID_TEST"))

# Discord + OpenAI setup
discord_intents = discord.Intents.default()
discord_client = discord.Client(intents=discord_intents)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Load persona
with open("persona.txt", "r", encoding="utf-8") as f:
    persona_instructions = f.read().strip()

async def get_message_from_gpt():
    # Get today’s date but swap year to 2050
    today = datetime.now()
    future_date = today.replace(year=2050).strftime("%Y-%m-%d")  # e.g. 2050-09-23

    response = openai_client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": persona_instructions},
            {"role": "user", "content": f"Give me the dailt news for {future_date}."}
        ]
    )
    return response.choices[0].message.content

async def send_message_once():
    channel = discord_client.get_channel(CHANNEL_ID)
    try:
        msg = await get_message_from_gpt()
    except Exception as e:
        msg = f"⚠️ Error fetching message: {e}"

    # Split message into dialogue parts
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

    # Audio output (stitch all parts) → send this first
    if AUDIO_FLAG:
        try:
            audio_file = generate_audio(parts)
            await channel.send(file=discord.File(audio_file))
        except Exception as e:
            await channel.send(f"⚠️ Error generating TTS: {e}")

    # Then send each part as text
    for part in parts:
        if len(part) > 2000:
            part = part[:1997] + "..."
        await channel.send("\n" + part)

    await discord_client.close()

@discord_client.event
async def on_ready():
    print(f"Logged in as {discord_client.user}")
    await send_message_once()

discord_client.run(DISCORD_TOKEN)

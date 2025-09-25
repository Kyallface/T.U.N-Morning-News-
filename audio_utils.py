from openai import OpenAI
from pydub import AudioSegment
import os
import re
from datetime import datetime

VOICE_MAP = {
    "Jessica": "alloy",
    "Steve": "verse"
}

def clean_line(text):
    match = re.match(r"\*{3}(\w+)\s+\w+\*{3}\s*:", text.strip())
    if match:
        speaker = match.group(1)
        dialogue = text.split(":", 1)[1].strip()
        return speaker, dialogue
    return None, text.strip()

def generate_audio(
    dialogue_parts,
    background_path="res/TUN Morning News Background.mp3",
    bg_offset_ms=13000,
    fade_out_ms=4000
):
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    os.makedirs("res", exist_ok=True)

    dialogue = AudioSegment.silent(duration=500)
    temp_files = []

    for idx, part in enumerate(dialogue_parts, 1):
        lines = part.splitlines()
        for line in lines:
            speaker, content = clean_line(line)
            if not content:
                continue

            voice = VOICE_MAP.get(speaker, "alloy")
            temp_file = os.path.join("res", f"chunk_{idx}_{speaker}.mp3")
            temp_files.append(temp_file)

            with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice=voice,
                input=content
            ) as response:
                response.stream_to_file(temp_file)

            seg = AudioSegment.from_file(temp_file, format="mp3")
            dialogue += seg + AudioSegment.silent(duration=250)

    if os.path.exists(background_path):
        bg = AudioSegment.from_file(background_path, format="mp3")
        total_length = bg_offset_ms + len(dialogue) + fade_out_ms
        if len(bg) < total_length:
            bg = bg + AudioSegment.silent(duration=(total_length - len(bg)))
        combined = bg.overlay(dialogue, position=bg_offset_ms)
        combined = combined[:total_length].fade_out(fade_out_ms)
    else:
        combined = dialogue

    # Build safe filename with underscores
    today = datetime.now().strftime("%Y-%m-%d")
    future_date = today.replace(today[:4], "2050")
    safe_name = f"T.U.N_News_Broadcast_{future_date}.mp3"
    filename = os.path.join("res", safe_name)

    combined.export(filename, format="mp3")

    for f in temp_files:
        try:
            os.remove(f)
        except OSError:
            pass

    return filename

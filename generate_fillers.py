import os
import requests
import hashlib
from dotenv import load_dotenv
from app import _ensure_cache_dir  # reuse your cache folder helper

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

FILLER_LINES = [
    "Okay, one moment.",
    "Sure, just a second.",
    "Let me get that for you.",
    "One sec, please.",
    "Alright, just a moment.",
    "Sure thing, hang on.",
    "Got it, give me a sec.",
    "Let me connect you.",
    "Hold on just a bit.",
    "Sure, let me check.",
    "Alright, stand by.",
    "Please hold on.",
    "Okay, connecting you now.",
    "Just a quick moment.",
    "I’ll get that right now.",
    "Hang tight.",
    "Sure, right away.",
    "One moment, please.",
    "Let me pull that up.",
    "Alright, here we go."
]

def elevenlabs_tts_to_file(text, filename):
    cache_dir = _ensure_cache_dir()
    out_path = os.path.join(cache_dir, filename)
    if os.path.exists(out_path):
        print(f"Skipping (exists): {filename}")
        return out_path

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    data = {"text": text, "voice_settings": {"stability": 0.4, "similarity_boost": 0.5}}

    print(f"Generating: {filename}")
    r = requests.post(url, headers=headers, json=data, timeout=60)
    r.raise_for_status()

    with open(out_path, "wb") as f:
        f.write(r.content)

    return out_path

if __name__ == "__main__":
    for i, line in enumerate(FILLER_LINES, start=1):
        elevenlabs_tts_to_file(line, f"filler{i}.mp3")

    print("✅ All filler lines generated.")

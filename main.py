from flask import Flask, request, Response
import os
import json
import time
import random
import collections
import requests
import io

import numpy as np

import os

USE_SOUNDDEVICE = os.getenv("USE_SOUNDDEVICE", "0") == "1"
USE_VAD = os.getenv("USE_VAD", "0") == "1"
USE_AUDIO = os.getenv("USE_AUDIO", "0") == "1"

# Guard soundfile import
if USE_AUDIO:
    try:
        import soundfile as sf
    except Exception as e:
        raise RuntimeError(
            "soundfile not available. Disable by unsetting USE_AUDIO."
        ) from e
else:
    class _SoundFileStub:
        def __getattr__(self, name):
            raise RuntimeError(
                "soundfile is disabled on this server. Set USE_AUDIO=1 only for local runs."
            )
    sf = _SoundFileStub()

if USE_VAD:
    try:
        import webrtcvad  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "webrtcvad not available. Disable by unsetting USE_VAD."
        ) from e
else:
    class _VADStub:
        def __init__(self, *args, **kwargs): pass
        def is_speech(self, *args, **kwargs):
            # fallback: treat all audio as not speech
            return False
    webrtcvad = _VADStub  # type: ignore
sd = None
if USE_SOUNDDEVICE:
    try:
        import sounddevice as sd  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "sounddevice/PortAudio not available. Disable by unsetting USE_SOUNDDEVICE."
        ) from e
else:
    class _SoundDeviceStub:
        def __getattr__(self, name):
            raise RuntimeError(
                "sounddevice is disabled on this server. Set USE_SOUNDDEVICE=1 only for local runs."
            )
    sd = _SoundDeviceStub()

from faster_whisper import WhisperModel
from openai import OpenAI
from twilio.twiml.voice_response import VoiceResponse

# Guard dotenv import
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available, skipping .env file loading")

# Guard pyaudio import
if USE_AUDIO:
    try:
        import pyaudio
        from pydub import AudioSegment
    except Exception as e:
        raise RuntimeError(
            "pyaudio/pydub not available. Disable by unsetting USE_AUDIO."
        ) from e
else:
    class _PyAudioStub:
        def __getattr__(self, name):
            raise RuntimeError(
                "pyaudio is disabled on this server. Set USE_AUDIO=1 only for local runs."
            )
    pyaudio = _PyAudioStub()
    
    class _AudioSegmentStub:
        def __getattr__(self, name):
            raise RuntimeError(
                "pydub is disabled on this server. Set USE_AUDIO=1 only for local runs."
            )
    AudioSegment = _AudioSegmentStub()

# API Keys
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

# Load store configuration
with open("store_config.json") as f:
    store_config = json.load(f)

# Whisper model setup
model = WhisperModel("tiny", device="cpu", compute_type="int8")

# Flask app setup
app = Flask(__name__)

# Record user's voice with early cutoff if silence detected
def record_audio(filename, sample_rate=16000, max_duration=6):
    print("Listening...")

    vad = webrtcvad.Vad()
    vad.set_mode(3)  # 0–3: higher = more aggressive about filtering out silence

    frame_duration_ms = 30  # 10, 20, or 30 ms
    frame_size = int(sample_rate * frame_duration_ms / 1000)  # samples per frame
    frame_bytes = frame_size * 2  # 16-bit audio = 2 bytes/sample

    silence_threshold = 15  # number of consecutive silent frames before stopping
    max_frames = int((sample_rate * max_duration) / frame_size)

    recorded_frames = []
    silent_frames = 0

    stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16')
    with stream:
        for _ in range(max_frames):
            audio, _ = stream.read(frame_size)
            frame = audio[:, 0].tobytes()
            is_speech = vad.is_speech(frame, sample_rate)

            recorded_frames.append(frame)

            if not is_speech:
                silent_frames += 1
                if silent_frames > silence_threshold:
                    break
            else:
                silent_frames = 0

    print("Stopped listening.")

    # Save the audio to file
    audio_data = b''.join(recorded_frames)
    with sf.SoundFile(filename, mode='w', samplerate=sample_rate, channels=1, subtype='PCM_16') as f:
        f.write(np.frombuffer(audio_data, dtype='int16'))

    print("Saved voice to", filename)

time.sleep(0.2)

# Transcribe audio
def transcribe(filename):
    segments, _ = model.transcribe(filename, beam_size=1)
    transcript = " ".join([segment.text for segment in segments])
    return transcript.strip()

# Generate response from GPT
def generate_response(transcript):
    departments = ', '.join(store_config['departments'].keys())

    prompt = f"""
You are an AI phone assistant working for a large superstore like Walmart or Fred Meyer. Your job is to connect customers to the correct department based on what they ask. This store carries groceries, household goods, electronics, health and beauty items, hardware, tools, and more.

You must respond in a **valid JSON object only**, with no extra dialogue or explanation.

When a customer says something like: "{transcript}", respond ONLY in this JSON format:

{{
  "response": "Your spoken response to the customer, e.g. 'Let me connect you to Grocery.'",
  "department": "Exact department name from the list below, or null if clarification is needed"
}}

Departments: {departments}

Instructions:
- You must **always** assign a department (never "None" unless it's clearly small talk or an incomplete request).
- Make a **best guess** even if it's not 100% clear.
- If the customer makes small talk (e.g., "how are you?", "what's up?"), respond politely but do **not** assign a department yet. Wait for them to explain what they need.
- If the customer is cut off or doesn't finish their sentence, respond with a short prompt asking them to clarify.
- Use common sense and real-world retail logic to assign departments confidently, even if the item isn't explicitly listed.
- Never say that you are an AI or mention artificial intelligence. Always respond as if you're a normal human employee working at the store, using casual, friendly language.
- Only assign a department if the request clearly relates to a product or store service.
- In cases where clarification is needed, respond with a brief, friendly question and set `"department": null`.

DEPARTMENT LOGIC:

- Grocery = packaged foods, drinks, snacks, dairy, produce, frozen items, canned goods, condiments, and household consumables like toilet paper, paper towels, and dish soap. Use Grocery for food unless it clearly fits into Deli, Bakery, or Meat & Seafood.

- Meat & Seafood = fresh or raw meat, poultry, and seafood. Includes fish, shrimp, crab legs, salmon, steak, ribs, ground beef, chicken thighs, etc. Use this if it sounds like something you'd get from a butcher or seafood counter.

- Deli = fresh prepared foods, sliced meats and cheeses, rotisserie chickens, hot meals, lunch trays — anything ready to eat that is not baked goods.

- Bakery = fresh baked goods like bread, cakes, cookies, donuts, muffins, croissants — NOT packaged or frozen dessert items.

- Electronics = phones, chargers, headphones, batteries, computers, printers, printer paper, ink, USB sticks, keyboards, TVs, game consoles.

- Home and Garden = tools, plants, furniture, seasonal/outdoor items, cleaning supplies, extension cords, grills, and grilling accessories.

- Health and Beauty = shampoo, conditioner, deodorant, lotion, toothpaste, makeup, vitamins, supplements, over-the-counter medications.

- Customer Service = gift cards, returns, lost & found, store hours, complaints, general inquiries.

Instructions:
- If a product fits multiple areas, pick the department most likely to handle **customer questions** about it.
- Use common sense: "fish" usually means fresh fish unless the customer clearly says frozen or canned.
- Do NOT respond with "None" — if unsure, make your best guess using real-world logic.
- If the customer's request is vague or unrelated to a product, politely ask them to clarify.



Example mappings:
- Whipped cream → Grocery
- Cake → Bakery
- Shampoo → Health and Beauty
- Rotisserie chicken → Deli
- Hammer → Home and Garden
- Phone charger → Electronics
- Dog food → Grocery
- Toothpaste → Health and Beauty
- Valentine's card → Customer Service
- Printer → Electronics
- Printer paper → Electronics
- USB cable → Electronics
- Toilet paper → Grocery
- Vitamins → Health and Beauty
- Fish → Meat & Seafood
- Salmon → Meat & Seafood
- Chicken thighs → Meat & Seafood
- Ground beef → Meat & Seafood
- Muffins → Bakery
- Cake → Bakery
- Rotisserie chicken → Deli
- Hot lunch → Deli
- Eggs → Grocery
- Canned tuna → Grocery
- Rice → Grocery
- Pasta → Grocery
- Bread → Bakery
- Milk → Grocery
- Cheese → Grocery
- Bananas → Grocery
- Apples → Grocery
- Shampoo → Health and Beauty




NEVER say anything outside the JSON block.
"""

    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}]
    )

    try:
        content = completion.choices[0].message.content.strip()
        parsed = json.loads(content)
        return parsed["response"], parsed["department"]
    except Exception as e:
        print("Error parsing GPT response:", e)
        print("Raw response was:", content)
        return "Sorry, I'm having trouble understanding.", "None"

# Speak response using ElevenLabs
def speak_response(text):
    headers = {
        "xi-api-key": ELEVENLABS_KEY,
        "Content-Type": "application/json"
    }
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

    data = {
        "text": text,
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.5
        }
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        # Decode MP3 using pydub
        audio = AudioSegment.from_file(io.BytesIO(response.content), format="mp3")
        pcm_data = audio.raw_data

        # Play using PyAudio
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(audio.sample_width),
                    channels=audio.channels,
                    rate=audio.frame_rate,
                    output=True)
        stream.write(pcm_data)
        stream.stop_stream()
        stream.close()
        p.terminate()

    else:
        print("TTS failed", response.text)
        
def get_random_employee_name():
    names = ["Lisa", "Mark", "Tina", "Derek", "Amy", "Kevin", "Janet", "Steve"]
    return random.choice(names)

# Main loop
MAX_EXCHANGES = 4

def main():
    exchanges = 0

    # Operator-style greeting
    employee_name = get_random_employee_name()
    greeting = f"Awesome Grocery, this is {employee_name}. How can I help you today?"
    speak_response(greeting)

    while exchanges < MAX_EXCHANGES:
        record_audio("input.wav", sample_rate=16000)
        user_text = transcribe("input.wav")
        print("You said:", user_text)

        if not user_text:
            speak_response("Sorry, I didn't catch that. Could you please repeat?")
            exchanges += 1
            continue

        if "operator" in user_text.lower() or "human" in user_text.lower():
            speak_response("Connecting you to a human now.")
            break

        response_text, department = generate_response(user_text)
        print("GPT says:", response_text)
        print("Detected department:", department)

        speak_response(response_text)

        if department and department != "None":
            print("Call ended.")
            break
        else:
            exchanges += 1

    if exchanges >= MAX_EXCHANGES:
        speak_response("Sorry, we're having trouble understanding. Redirecting to a human.")

# Flask routes
@app.get("/")
def health():
    return "OK", 200

@app.post("/voice")
def voice():
    vr = VoiceResponse()
    vr.say("Thanks for calling Awesome Grocery. This is our test webhook. Goodbye.", voice="alice")
    vr.hangup()
    return Response(str(vr), mimetype="text/xml")

@app.route("/voice_advanced", methods=["POST"])
def voice_advanced():
    print("Incoming call...")
    speak_response("Welcome to Awesome Grocery. Please tell me what you're looking for.")

    record_audio("input.wav", sample_rate=16000)
    user_text = transcribe("input.wav")
    print("You said:", user_text)

    response_text, department = generate_response(user_text)
    print("GPT says:", response_text)
    print("Detected department:", department)

    speak_response(response_text)

    # Return TwiML to Twilio — we can hang up here or keep the call alive
    resp = VoiceResponse()
    resp.say(response_text, voice="alice")
    resp.hangup()
    return Response(str(resp), mimetype='text/xml')

if __name__ == "__main__":
    app.run(debug=True, port=5000)
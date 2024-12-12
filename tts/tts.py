import time
from fastapi import FastAPI, HTTPException
from pythainlp.tokenize import sent_tokenize
from pydantic import BaseModel , Field
import requests
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for input validation
class VoiceRequest(BaseModel):
    text: str
    audio_id: str = "EUOJF"
    speaker: str = "52"
    volume: int = 100
    speed: float = 1
    type_media: str = "mp3"
    language: str = "th"
    token: str = os.getenv("BOTNOI_API_TOKEN")

# Function to split text for text delay
def auto_generate_text_delay_with_pythainlp(text):
    text_delay = sent_tokenize(text, engine="thaisum")
    text_delay = " ".join(text_delay).strip()
    return text_delay

# Function to call Botnoi's API to generate voice
def generate_voice(audio_id, text, text_delay, speaker, volume, speed, type_media, language, token):
    url = "https://api-genvoice.botnoi.ai/voice/v1/generate_voice?provider=botnoivoice"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "audio_id": audio_id,
        "text": text,
        "text_delay": text_delay,
        "speaker": speaker,
        "volume": str(volume),
        "speed": str(speed),
        "type_media": type_media,
        "language": language,
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        data = response.json()
        if "data" in data:
            return data["data"]  # URL of the generated audio
        else:
            raise HTTPException(status_code=500, detail=data.get("message", "Unknown error"))
    else:
        raise HTTPException(status_code=response.status_code, detail="Voice generation failed")

# Function to download MP3 from a URL
def download_mp3(url, output_path):
    headers = {
        "Accept-Encoding": "identity;q=1, *;q=0",
        "Referer": "https://voice.botnoi.ai/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    }

    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 200:
        with open(output_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:  # Filter out keep-alive chunks
                    file.write(chunk)
    else:
        raise HTTPException(status_code=response.status_code, detail=f"{response.status_code} Failed to download MP3")

# FastAPI endpoint to generate and download voice
@app.post("/generate_voice_botnoi/")
def generate_voice_endpoint(request: VoiceRequest):
    
    text_delay = request.text
    # text_delay = auto_generate_text_delay_with_pythainlp(request.text)
    print("Text delay:", text_delay)
    audio_url = generate_voice(
        audio_id=request.audio_id,
        text=request.text,
        text_delay=text_delay,
        speaker=request.speaker,
        volume=request.volume,
        speed=request.speed,
        type_media=request.type_media,
        language=request.language,
        token=request.token,
    )
    
    # Generate unique filename for the MP3
    print("botnoi url: ", audio_url)
    output_dir = "generated_voice/botnoi"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{int(time.time())}.mp3")
    download_mp3(audio_url, output_file)
    
    return FileResponse(output_file, media_type="audio/mpeg", filename="output.mp3")

# -----------------------------------------------------------VAJA9-----------------------------------------------------------
# VAJA9 Voice Generation
class Vaja9Request(BaseModel):
    text: str
    speaker: int = 1
    phrase_break: int = 0
    audiovisual: int = 0

def generate_vaja9_voice(text: str, speaker: int, phrase_break: int, audiovisual: int):
    url = 'https://api.aiforthai.in.th/vaja9/synth_audiovisual'
    headers = {
        'Apikey': os.getenv("VAJA9_API_KEY"),
        'Content-Type': 'application/json'
    }
    data = {
        'input_text': text,
        'speaker': speaker, 
        'phrase_break': phrase_break,
        'audiovisual': audiovisual
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)  # Increased timeout to 60 seconds
        if response.status_code == 200:
            return response.json()['wav_url']
        elif response.status_code == 502:
            raise HTTPException(status_code=502, detail="Bad Gateway - The server received an invalid response from the upstream server")
        else:
            raise HTTPException(status_code=response.status_code, detail="Voice generation failed")
    except requests.exceptions.ReadTimeout:
        raise HTTPException(status_code=504, detail="Gateway Timeout - The server took too long to respond")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Bad Gateway - Connection error: {str(e)}")

def download_vaja9_wav(url: str, output_path: str):
    api_key = os.getenv("VAJA9_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="VAJA9_API_KEY environment variable not set")
    headers = {'Apikey': api_key}
    try:
        response = requests.get(url, headers=headers, timeout=60)  # Increased timeout to 60 seconds
        if response.status_code == 200:
            with open(output_path, 'wb') as file:
                file.write(response.content)
        elif response.status_code == 502:
            raise HTTPException(status_code=502, detail="Bad Gateway - The server received an invalid response from the upstream server")
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to download WAV")
    except requests.exceptions.ReadTimeout:
        raise HTTPException(status_code=504, detail="Gateway Timeout - The server took too long to respond")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Bad Gateway - Connection error: {str(e)}")

@app.post("/generate_voice_vaja9/")
def generate_voice_vaja9_endpoint(request: Vaja9Request):
    """
    Generate a voice file using the Vaja9 endpoint.
    - text (str): ข้อความที่ต้องการสังเคราะห์เสียง (สูงสุดไม่เกิน 300 ตัวอักษร)
    - speaker (int): ประเภทของเสียงที่ต้องการ
        0 : เสียงผู้ชาย
        1 : เสียงผู้หญิง
        2 : เสียงเด็กผู้ชาย
        3 : เสียงเด็กผู้หญิง
    - phrase_break (int): ประเภทของการหยุดเว้นวรรค
        0 : หยุดเว้นวรรคแบบอัตโนมัติ
        1 : ไม่หยุดเว้นวรรค
    - audiovisual (int): ประเภทของโมเดล
        0 : โมเดลสังเคราะห์เสียง
        1 : โมเดลสังเคราะห์เสียง และภาพ
    """

    try:
        audio_url = generate_vaja9_voice(
            text=request.text,
            speaker=request.speaker,
            phrase_break=request.phrase_break,
            audiovisual=request.audiovisual
        )
        
        # Generate unique filename for the WAV file
        output_dir = "generated_voice/vaja9"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{int(time.time())}.wav")
        download_vaja9_wav(audio_url, output_file)
        
        return FileResponse(output_file, media_type="audio/wav", filename="output.wav")
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Bad Gateway - Unexpected error: {str(e)}")
    

if __name__ == "__main__":
    uvicorn.run("tts:app", host="0.0.0.0", port=8001, reload=True)
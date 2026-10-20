from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
import re

app = FastAPI()

# السماح لتطبيق الموبايل بالاتصال بالسيرفر
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_text_for_tts(text: str) -> str:
    text = re.sub(r'(\d+)\s*[-–—.]\s*', r'\1: ', text)
    text = re.sub(r'[-–—_]+', '، ', text)
    text = re.sub(r'[*#~`\\/|<>{}\[\]()]+', ' ', text)
    text = re.sub(r'[،,]{2,}', '،', text)
    return re.sub(r'\s+', ' ', text).strip()

# 1. مسار الإنعاش: هذا ما سيطلبه Cron-job كل 10 دقائق
@app.get("/ping")
async def keep_alive():
    return {"status": "السيرفر مستيقظ ويعمل بكفاءة"}

# 2. مسار الصوت: هذا ما سيطلبه تطبيقك لتشغيل صوت حامد
@app.post("/api/tts")
async def generate_tts(data: dict):
    text = data.get("text", "")
    voice = data.get("voice", "ar-SA-HamedNeural")
    
    if not text:
        raise HTTPException(status_code=400, detail="النص مطلوب")
        
    cleaned_text = clean_text_for_tts(text)
    communicate = edge_tts.Communicate(cleaned_text, voice)
    
    audio_data = bytearray()
    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.extend(chunk["data"])
        return Response(content=bytes(audio_data), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

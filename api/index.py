"""
FastAPI backend for Multilingual Voice Transcriber and Translator
Deployed on Vercel as serverless functions
"""
import sys
import json
import sqlite3
import os
from datetime import datetime
from typing import Optional
import base64
import tempfile

# Compatibility shims for modules removed in Python 3.13
import types

# aifc compatibility shim
try:
    import aifc
except ModuleNotFoundError:
    aifc_module = types.ModuleType('aifc')
    aifc_module.Error = Exception
    aifc_module.open = lambda *args, **kwargs: None
    sys.modules['aifc'] = aifc_module

# audioop compatibility
try:
    import audioop
except ModuleNotFoundError:
    try:
        import audioop_lts as audioop
        sys.modules['audioop'] = audioop
    except ImportError:
        def _audioop_stub(*args, **kwargs):
            if args:
                return args[0] if isinstance(args[0], bytes) else b''
            return b''
        audioop_module = types.ModuleType('audioop')
        audioop_module.add = _audioop_stub
        audioop_module.mul = _audioop_stub
        audioop_module.tomono = _audioop_stub
        audioop_module.tostereo = _audioop_stub
        audioop_module.ratecv = _audioop_stub
        audioop_module.lin2lin = _audioop_stub
        audioop_module.bias = _audioop_stub
        audioop_module.reverse = _audioop_stub
        audioop_module.byteswap = _audioop_stub
        audioop_module.avg = lambda *args: 0
        audioop_module.max = lambda *args: 0
        audioop_module.minmax = lambda *args: (0, 0)
        audioop_module.rms = lambda *args: 0
        audioop_module.cross = lambda *args: 0
        audioop_module.findfactor = lambda *args: 0.0
        audioop_module.findfit = lambda *args: 0.0
        audioop_module.findmax = lambda *args: 0
        audioop_module.avgpp = lambda *args: 0
        audioop_module.maxpp = lambda *args: 0
        sys.modules['audioop'] = audioop_module

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import speech_recognition as sr
from translate import Translator
from gtts import gTTS
import requests
import urllib.parse
import re
import difflib

app = FastAPI(title="Voice Transcriber API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path (using /tmp for Vercel's read-only filesystem)
DB_PATH = os.environ.get('DB_PATH', '/tmp/transcripts.db')

# Initialize database
def init_db():
    """Initialize SQLite DB and create tables if missing."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                src_lang TEXT,
                tgt_lang TEXT,
                original_text TEXT,
                translated_text TEXT,
                audio_path TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS workers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                phone_number TEXT,
                name TEXT,
                skill TEXT,
                education TEXT,
                age TEXT,
                sex TEXT,
                experience TEXT,
                location TEXT,
                aadhaar TEXT,
                wage_expected TEXT,
                languages_known TEXT,
                raw_answers TEXT,
                audio_path TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database init error: {e}")

# Initialize on startup
init_db()

# Request/Response models
class TranslateRequest(BaseModel):
    text: str
    src_lang: str = "en"
    tgt_lang: str = "hi"

class OTPRequest(BaseModel):
    phone_number: str

class OTPVerifyRequest(BaseModel):
    phone_number: str
    otp: str

class WorkerOnboardingRequest(BaseModel):
    phone_number: str
    answers: dict

# Helper functions (extracted from main.py)
def _fallback_google_translate(text, src, tgt):
    """Use the unofficial Google Translate web API as a fallback."""
    try:
        base = 'https://translate.googleapis.com/translate_a/single'
        params = {
            'client': 'gtx',
            'sl': src,
            'tl': tgt,
            'dt': 't',
            'q': text,
        }
        url = base + '?' + urllib.parse.urlencode(params)
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        parts = [seg[0] for seg in data[0] if seg and seg[0]]
        return ''.join(parts)
    except Exception as e:
        raise

def _is_suspicious_translation(src_text, translated_text):
    """Detect obviously-broken translations."""
    if not translated_text:
        return True
    if translated_text.strip() == src_text.strip():
        return True
    if len(translated_text.strip()) < max(3, len(src_text.strip()) // 3):
        return True
    lines = translated_text.splitlines()
    short_lines = sum(1 for L in lines if len(L.strip()) <= 2)
    if len(lines) >= 2 and short_lines >= len(lines) // 2:
        return True
    tokens = re.findall(r"\b\w\b", translated_text)
    if len(tokens) >= 2:
        return True
    return False

def _contains_hindi(text):
    try:
        return bool(re.search(r'[\u0900-\u097F]', str(text or '')))
    except Exception:
        return False

def _normalize_digits(text):
    """Convert Devanagari digits to ASCII."""
    if text is None:
        return ''
    s = str(text)
    trans = str.maketrans('०१२३४५६७८९', '0123456789')
    s = s.translate(trans)
    s = re.sub(r'(?<=\d)\s+(?=\d)', '', s)
    return s

def _translate_to_english(text, assumed_src=None):
    """Translate arbitrary text to English with fallback."""
    try:
        src = assumed_src
        if src is None:
            src = 'hi' if _contains_hindi(text) else 'en'
        if src == 'en':
            return text
        try:
            t = Translator(from_lang=src, to_lang='en').translate(text)
        except Exception:
            t = ''
        if not t or _is_suspicious_translation(str(text or ''), t):
            try:
                t_fb = _fallback_google_translate(str(text or ''), src, 'en')
                return t_fb or t or str(text or '')
            except Exception:
                return t or str(text or '')
        return t
    except Exception:
        return str(text or '')

# API Endpoints

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Voice Transcriber API is running", "status": "ok"}

@app.post("/api/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...), language: str = Form("en-US")):
    """
    Transcribe audio file to text.
    language: Recognition language code (e.g., 'en-US', 'hi-IN')
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            content = await audio_file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Recognize speech
        recognizer = sr.Recognizer()
        with sr.AudioFile(tmp_path) as source:
            audio = recognizer.record(source)
        
        try:
            text = recognizer.recognize_google(audio, language=language)
        except sr.UnknownValueError:
            text = ""
        except sr.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Recognition service error: {e}")
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return {"text": text, "language": language}
    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/translate")
async def translate_text(request: TranslateRequest):
    """Translate text from source language to target language."""
    try:
        translator = Translator(from_lang=request.src_lang, to_lang=request.tgt_lang)
        translated_text = translator.translate(request.text)
        
        # Fallback if translation looks suspicious
        if _is_suspicious_translation(request.text, translated_text):
            try:
                translated_text = _fallback_google_translate(request.text, request.src_lang, request.tgt_lang)
            except Exception:
                pass
        
        return {
            "original_text": request.text,
            "translated_text": translated_text,
            "src_lang": request.src_lang,
            "tgt_lang": request.tgt_lang
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/text-to-speech")
async def text_to_speech(text: str = Form(...), language: str = Form("hi")):
    """Convert text to speech and return audio file."""
    try:
        tts = gTTS(text=text, lang=language)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tts.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        return FileResponse(
            tmp_path,
            media_type="audio/mpeg",
            filename="translated_audio.mp3",
            background=lambda: os.unlink(tmp_path)  # Clean up after response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transcribe-and-translate")
async def transcribe_and_translate(
    audio_file: UploadFile = File(...),
    src_lang: str = Form("en"),
    tgt_lang: str = Form("hi"),
    recognition_lang: str = Form("en-US")
):
    """Complete pipeline: transcribe audio, translate text, and generate TTS."""
    try:
        # Step 1: Transcribe
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_audio:
            content = await audio_file.read()
            tmp_audio.write(content)
            audio_path = tmp_audio.name
        
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        
        try:
            original_text = recognizer.recognize_google(audio, language=recognition_lang)
        except sr.UnknownValueError:
            original_text = ""
        except sr.RequestError as e:
            os.unlink(audio_path)
            raise HTTPException(status_code=500, detail=f"Recognition error: {e}")
        
        os.unlink(audio_path)
        
        if not original_text:
            raise HTTPException(status_code=400, detail="No speech detected in audio")
        
        # Step 2: Translate
        translator = Translator(from_lang=src_lang, to_lang=tgt_lang)
        try:
            translated_text = translator.translate(original_text)
        except Exception:
            translated_text = ""
        
        if _is_suspicious_translation(original_text, translated_text):
            try:
                translated_text = _fallback_google_translate(original_text, src_lang, tgt_lang)
            except Exception:
                pass
        
        # Step 3: Generate TTS
        tts = gTTS(text=translated_text, lang=tgt_lang)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_tts:
            tts.save(tmp_tts.name)
            tts_path = tmp_tts.name
        
        # Step 4: Save to database
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            ts = datetime.utcnow().isoformat()
            # Save English version for storage
            save_text_en = translated_text if tgt_lang.startswith('en') else _translate_to_english(original_text, src_lang)
            c.execute(
                'INSERT INTO transcripts (timestamp, src_lang, tgt_lang, original_text, translated_text, audio_path) VALUES (?,?,?,?,?,?)',
                (ts, src_lang, tgt_lang, original_text, save_text_en, tts_path)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database save error: {e}")
        
        # Return audio file
        return FileResponse(
            tts_path,
            media_type="audio/mpeg",
            filename="translated_audio.mp3",
            background=lambda: os.unlink(tts_path)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/send-otp")
async def send_otp(request: OTPRequest):
    """Send OTP to phone number (demo - in production use SMS service)."""
    import random
    otp = str(random.randint(100000, 999999))
    # In production, send via SMS service (Twilio, etc.)
    # For demo, return OTP (in production, store in Redis/cache with expiry)
    return {"otp": otp, "message": "OTP sent (demo mode)"}

@app.post("/api/verify-otp")
async def verify_otp(request: OTPVerifyRequest):
    """Verify OTP and check if user exists."""
    # In production, verify OTP from cache
    # For demo, accept any 6-digit OTP
    if len(request.otp) != 6 or not request.otp.isdigit():
        raise HTTPException(status_code=400, detail="Invalid OTP format")
    
    # Check if user exists
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id FROM workers WHERE phone_number = ?', (request.phone_number,))
        result = c.fetchone()
        conn.close()
        
        user_exists = result is not None
        return {
            "verified": True,
            "user_exists": user_exists,
            "phone_number": request.phone_number
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/onboard-worker")
async def onboard_worker(request: WorkerOnboardingRequest):
    """Save worker onboarding data."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if phone number already exists
        c.execute('SELECT id FROM workers WHERE phone_number = ?', (request.phone_number,))
        if c.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Phone number already exists")
        
        # Normalize and translate answers
        ans = dict(request.answers)
        for k in ['name', 'education', 'sex', 'location', 'languages_known']:
            ans[k] = _translate_to_english(ans.get(k, ''))
        
        # Normalize other fields
        ans['age'] = _normalize_digits(ans.get('age', ''))
        ans['experience'] = _normalize_digits(ans.get('experience', ''))
        ans['wage_expected'] = _normalize_digits(ans.get('wage_expected', ''))
        aadhaar = _normalize_digits(ans.get('aadhaar', ''))
        ans['aadhaar'] = re.sub(r'\D', '', aadhaar)
        
        ts = datetime.utcnow().isoformat()
        raw = json.dumps(request.answers, ensure_ascii=False)
        
        c.execute(
            'INSERT INTO workers (timestamp, phone_number, name, skill, education, age, sex, experience, location, aadhaar, wage_expected, languages_known, raw_answers, audio_path) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (ts, request.phone_number, ans.get('name'), ans.get('skill'), ans.get('education'),
             ans.get('age'), ans.get('sex'), ans.get('experience'), ans.get('location'),
             ans.get('aadhaar'), ans.get('wage_expected'), ans.get('languages_known'), raw, None)
        )
        conn.commit()
        conn.close()
        
        return {"message": "Worker onboarded successfully", "phone_number": request.phone_number}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workers")
async def get_workers():
    """Get all workers."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, timestamp, phone_number, name, skill, education, age, sex, experience, location, aadhaar, wage_expected, languages_known FROM workers ORDER BY id DESC')
        rows = c.fetchall()
        conn.close()
        
        workers = []
        for row in rows:
            workers.append({
                "id": row[0],
                "timestamp": row[1],
                "phone_number": row[2],
                "name": row[3],
                "skill": row[4],
                "education": row[5],
                "age": row[6],
                "sex": row[7],
                "experience": row[8],
                "location": row[9],
                "aadhaar": row[10],
                "wage_expected": row[11],
                "languages_known": row[12]
            })
        
        return {"workers": workers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transcripts")
async def get_transcripts():
    """Get all transcripts."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, timestamp, src_lang, tgt_lang, original_text, translated_text FROM transcripts ORDER BY id DESC LIMIT 100')
        rows = c.fetchall()
        conn.close()
        
        transcripts = []
        for row in rows:
            transcripts.append({
                "id": row[0],
                "timestamp": row[1],
                "src_lang": row[2],
                "tgt_lang": row[3],
                "original_text": row[4],
                "translated_text": row[5]
            })
        
        return {"transcripts": transcripts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Vercel serverless handler
# Vercel automatically detects FastAPI app, but we can also export it explicitly
# The app variable is automatically used by Vercel's Python runtime


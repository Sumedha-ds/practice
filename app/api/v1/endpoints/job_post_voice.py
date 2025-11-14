"""
Voice-based Job Posting API endpoints - Similar to onboarding flow.
Each question is asked via voice, and answers are received via voice input.
"""
# Python 3.13 compatibility shims for speech_recognition
import sys
try:
    import aifc
except ModuleNotFoundError:
    import warnings
    warnings.filterwarnings('ignore')
    sys.modules['aifc'] = type(sys)('aifc')

try:
    import audioop
except ModuleNotFoundError:
    try:
        import audioop_lts as audioop
        sys.modules['audioop'] = audioop
    except ImportError:
        sys.modules['audioop'] = type(sys)('audioop')

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import base64
import json
import io
import os
import tempfile

from app.api.deps import get_db
from app.models.job import Job
from app.models.user import User

# Speech recognition and TTS
import speech_recognition as sr
from gtts import gTTS
from translate import Translator

router = APIRouter(prefix="/job-post-voice", tags=["Job Post Voice"])

# Job posting questions
JOB_POST_QUESTIONS = {
    "job_title": {
        "text": "कृपया नौकरी का शीर्षक बताएं। जैसे कि चित्रकार, बिजली मिस्त्री, ड्राइवर, रसोइया।",
        "text_en": "Please tell the job title. Such as painter, electrician, driver, cook.",
        "order": 1
    },
    "gender": {
        "text": "क्या आप पुरुष या महिला कर्मचारी चाहते हैं? कृपया बताएं।",
        "text_en": "Do you want male or female employees? Please tell.",
        "order": 2
    },
    "wage": {
        "text": "कृपया दैनिक वेतन की राशि बताएं। रुपये में।",
        "text_en": "Please tell the daily wage amount in rupees.",
        "order": 3
    },
    "city": {
        "text": "यह नौकरी किस शहर में है? कृपया शहर का नाम बताएं।",
        "text_en": "In which city is this job? Please tell the city name.",
        "order": 4
    },
    "audio_description": {
        "text": "कृपया नौकरी का विवरण बोलें। क्या काम है, समय क्या है, और अन्य जानकारी।",
        "text_en": "Please speak the job description. What is the work, timing, and other details.",
        "order": 5
    }
}

# Temporary storage for job post answers (in production, use Redis or database)
job_post_answers_storage = {}


def generate_question_audio(question_text: str) -> bytes:
    """Generate TTS audio for a question in Hindi."""
    try:
        tts = gTTS(text=question_text, lang='hi', slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return audio_fp.read()
    except Exception as e:
        print(f"Error generating audio: {e}")
        return None


def get_user_from_token(authorization: str, db: Session) -> Optional[User]:
    """Extract user from Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    # Simple token format: token_<phone>_<random>
    if token.startswith("token_"):
        parts = token.split("_")
        if len(parts) >= 2:
            phone = parts[1]
            user = db.query(User).filter(User.phone == phone).first()
            return user
    return None


@router.get("/questions")
async def get_job_post_questions():
    """
    Get all job posting questions (text only).
    """
    questions = []
    for key, data in sorted(JOB_POST_QUESTIONS.items(), key=lambda x: x[1]['order']):
        questions.append({
            "key": key,
            "text": data["text"],
            "text_en": data["text_en"],
            "order": data["order"]
        })
    
    return {
        "success": True,
        "questions": questions
    }


@router.get("/question/{question_key}/voice")
async def get_job_post_question_voice(question_key: str):
    """
    Get a specific job posting question with TTS audio.
    
    Returns:
        - question_key: The key of the question
        - question_text: Hindi text
        - question_text_en: English text
        - audio_base64: Base64 encoded MP3 audio
    """
    if question_key not in JOB_POST_QUESTIONS:
        raise HTTPException(status_code=404, detail=f"Question '{question_key}' not found")
    
    question_data = JOB_POST_QUESTIONS[question_key]
    audio_bytes = generate_question_audio(question_data["text"])
    
    audio_base64 = None
    if audio_bytes:
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    return {
        "success": True,
        "question_key": question_key,
        "question_text": question_data["text"],
        "question_text_en": question_data["text_en"],
        "audio_base64": audio_base64,
        "order": question_data["order"]
    }


@router.post("/answer")
async def save_job_post_answer(
    question_key: str = Form(...),
    audio_file: Optional[UploadFile] = File(None),
    text_answer: Optional[str] = Form(None),
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Save an answer to a job posting question.
    
    Accepts either:
    - audio_file: Voice recording (WAV/WebM format)
    - text_answer: Direct text input
    
    The audio will be transcribed (Hindi) and translated to English.
    """
    # Authenticate user
    user = get_user_from_token(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    phone = user.phone
    
    # Validate question key
    if question_key not in JOB_POST_QUESTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid question key: {question_key}")
    
    answer_text = None
    answer_text_hindi = None
    
    # Process audio file if provided
    if audio_file:
        try:
            # Read audio file
            audio_content = await audio_file.read()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                temp_audio.write(audio_content)
                temp_audio_path = temp_audio.name
            
            try:
                # Recognize speech
                recognizer = sr.Recognizer()
                with sr.AudioFile(temp_audio_path) as source:
                    audio_data = recognizer.record(source)
                
                # Recognize in Hindi
                answer_text_hindi = recognizer.recognize_google(audio_data, language='hi-IN')
                
                # Translate Hindi to English
                try:
                    translator = Translator(from_lang="hi", to_lang="en")
                    answer_text = translator.translate(answer_text_hindi)
                except Exception as e:
                    print(f"Translation warning: {e}")
                    answer_text = answer_text_hindi
                    
            finally:
                # Clean up temp file
                if os.path.exists(temp_audio_path):
                    os.remove(temp_audio_path)
                    
        except sr.UnknownValueError:
            raise HTTPException(status_code=400, detail="Could not understand the audio")
        except sr.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Speech recognition error: {e}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing audio: {e}")
    
    # Use text answer if provided
    elif text_answer:
        answer_text = text_answer
    
    else:
        raise HTTPException(status_code=400, detail="Either audio_file or text_answer must be provided")
    
    # Special handling for audio_description - store the audio file itself
    if question_key == "audio_description" and audio_file:
        # Store the actual audio content for this question
        audio_content = await audio_file.read()
        if phone not in job_post_answers_storage:
            job_post_answers_storage[phone] = {}
        job_post_answers_storage[phone]["audio_description_file"] = audio_content
    
    # Initialize storage for this phone if not exists
    if phone not in job_post_answers_storage:
        job_post_answers_storage[phone] = {}
    
    # Save the answer
    job_post_answers_storage[phone][question_key] = answer_text
    
    return {
        "success": True,
        "question_key": question_key,
        "answer_text": answer_text,
        "original_hindi": answer_text_hindi,
        "phone_number": phone,
        "message": "Answer saved successfully"
    }


@router.post("/complete")
async def complete_job_post(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Complete the job posting by creating the job with all collected answers.
    
    Validates that all required questions have been answered.
    """
    # Authenticate user
    user = get_user_from_token(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    phone = user.phone
    
    # Check if user has answers
    if phone not in job_post_answers_storage:
        raise HTTPException(status_code=400, detail="No answers found. Please answer the questions first.")
    
    answers = job_post_answers_storage[phone]
    
    # Validate all questions are answered
    missing_questions = []
    for key in JOB_POST_QUESTIONS.keys():
        if key not in answers or not answers[key]:
            missing_questions.append(key)
    
    if missing_questions:
        raise HTTPException(
            status_code=400,
            detail=f"Missing answers for: {', '.join(missing_questions)}"
        )
    
    try:
        # Create the job post
        job = Job(
            jobTitle=answers.get("job_title"),
            gender=answers.get("gender"),
            wage=float(answers.get("wage", 0)),
            city=answers.get("city"),
            audioScript=answers.get("audio_description", ""),
            userId=user.id
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Save audio file if exists
        if "audio_description_file" in answers:
            audio_dir = "uploaded_audio"
            os.makedirs(audio_dir, exist_ok=True)
            audio_filename = f"job_{job.id}_audio.mp3"
            audio_path = os.path.join(audio_dir, audio_filename)
            
            with open(audio_path, "wb") as f:
                f.write(answers["audio_description_file"])
        
        # Clear the answers from storage
        del job_post_answers_storage[phone]
        
        return {
            "success": True,
            "message": "Job posted successfully",
            "job_id": job.id,
            "job_title": job.jobTitle,
            "gender": job.gender,
            "wage": job.wage,
            "city": job.city
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating job post: {str(e)}")


@router.get("/progress")
async def get_job_post_progress(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get the current progress of job posting.
    
    Returns which questions have been answered and which are pending.
    """
    # Authenticate user
    user = get_user_from_token(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    phone = user.phone
    
    # Get current answers
    current_answers = job_post_answers_storage.get(phone, {})
    
    progress = []
    for key, data in sorted(JOB_POST_QUESTIONS.items(), key=lambda x: x[1]['order']):
        progress.append({
            "question_key": key,
            "question_text": data["text"],
            "question_text_en": data["text_en"],
            "answered": key in current_answers and current_answers[key] is not None,
            "answer": current_answers.get(key),
            "order": data["order"]
        })
    
    total_questions = len(JOB_POST_QUESTIONS)
    answered_questions = sum(1 for p in progress if p["answered"])
    
    return {
        "success": True,
        "phone_number": phone,
        "total_questions": total_questions,
        "answered_questions": answered_questions,
        "completion_percentage": (answered_questions / total_questions) * 100,
        "progress": progress
    }


@router.delete("/clear")
async def clear_job_post_answers(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Clear all saved answers for the current job post (start over).
    """
    # Authenticate user
    user = get_user_from_token(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    phone = user.phone
    
    if phone in job_post_answers_storage:
        del job_post_answers_storage[phone]
    
    return {
        "success": True,
        "message": "Job post answers cleared successfully"
    }


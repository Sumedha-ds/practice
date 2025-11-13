"""
REST API Server for Worker Onboarding System
Run with: python api_server.py
"""
import sys
import types

# Compatibility shims for modules removed in Python 3.13
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

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sqlite3
import json
import os
import re
import difflib
from datetime import datetime
from functools import wraps
import random
import speech_recognition as sr
from gtts import gTTS
import base64
import io
import tempfile

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'transcripts.db')

# Simple token storage (use JWT in production)
tokens = {}  # {phone_number: token}

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create workers table if not exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            phone_number TEXT,
            profile_created INTEGER DEFAULT 0,
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
    
    # Add columns if they don't exist
    c.execute("PRAGMA table_info(workers)")
    columns = [row[1] for row in c.fetchall()]
    
    if 'phone_number' not in columns:
        c.execute("ALTER TABLE workers ADD COLUMN phone_number TEXT")
    if 'profile_created' not in columns:
        c.execute("ALTER TABLE workers ADD COLUMN profile_created INTEGER DEFAULT 0")
        c.execute("UPDATE workers SET profile_created = 1 WHERE profile_created IS NULL OR profile_created = 0")
    
    if 'user_choice' not in columns:
        c.execute("ALTER TABLE workers ADD COLUMN user_choice TEXT")
    
    conn.commit()
    conn.close()

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token or token not in tokens.values():
            return jsonify({'success': False, 'message': 'Unauthorized. Please login.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_phone_from_token():
    """Get phone number from auth token"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    for phone, t in tokens.items():
        if t == token:
            return phone
    return None

# ==================== AUTHENTICATION APIs ====================

@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP and check if profile exists"""
    data = request.get_json()
    phone = data.get('phone_number', '').strip()
    otp = data.get('otp', '').strip()
    
    if not phone or len(phone) != 10 or not phone.isdigit():
        return jsonify({
            'success': False,
            'message': 'Invalid phone number format'
        }), 400
    
    if not otp or len(otp) != 4 or not otp.isdigit():
        return jsonify({
            'success': False,
            'message': 'Invalid OTP format. Must be 4 digits.'
        }), 400
    
    # Accept any 4-digit OTP (no validation)
    # Check if profile exists and onboarding status
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT profile_created, user_choice FROM workers WHERE phone_number = ?', (phone,))
    result = c.fetchone()
    conn.close()
    
    # Determine onboarding status
    onboarding_completed = result is not None and result[0] == 1
    profile_exists = result is not None
    user_choice = result['user_choice'] if result and result['user_choice'] else None
    
    # Generate token (use JWT in production)
    token = f"token_{phone}_{random.randint(1000, 9999)}"
    tokens[phone] = token
    
    # Return response with user choice if exists
    response = {
        'phone_number': phone,
        'onboarding_completed': onboarding_completed,
        'token': token
    }
    
    # Include user choice if it exists
    if user_choice:
        response['user_choice'] = user_choice
    
    return jsonify(response), 200

@app.route('/api/auth/check-profile/<phone_number>', methods=['GET'])
def check_profile(phone_number):
    """Check if profile exists for phone number"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT profile_created FROM workers WHERE phone_number = ?', (phone_number,))
    result = c.fetchone()
    conn.close()
    
    profile_exists = result is not None and result[0] == 1
    
    return jsonify({
        'success': True,
        'phone_number': phone_number,
        'profile_exists': profile_exists,
        'profile_created': 1 if profile_exists else 0
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
@require_auth
def logout():
    """Logout current user"""
    phone = get_phone_from_token()
    if phone and phone in tokens:
        del tokens[phone]
    
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200

@app.route('/api/auth/user-choice/question', methods=['GET'])
@require_auth
def get_user_choice_question():
    """Get the user choice question text for TTS"""
    language = request.args.get('language', 'en')
    
    questions = {
        'en': 'What would you like to do? Say apply job, post job, or learning module.',
        'hi': 'आप क्या करना चाहेंगे? कहें apply job, post job, या learning module।'
    }
    
    question_text = questions.get(language, questions['en'])
    
    # Generate TTS audio
    try:
        tts = gTTS(text=question_text, lang='en' if language == 'en' else 'hi', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Convert to base64 for JSON response
        audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'question_text': question_text,
            'audio_base64': audio_base64,
            'language': language
        }), 200
    except Exception as e:
        return jsonify({
            'success': True,
            'question_text': question_text,
            'audio_base64': None,
            'language': language,
            'error': f'Could not generate audio: {str(e)}'
        }), 200

@app.route('/api/auth/user-choice', methods=['POST'])
@require_auth
def save_user_choice():
    """Save user's choice from voice response (Apply Job, Post Job, or Learning Module)"""
    phone = get_phone_from_token()
    if not phone:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    voice_text = data.get('voice_text', '').strip().lower()
    
    if not voice_text:
        return jsonify({
            'success': False,
            'message': 'Voice text is required'
        }), 400
    
    # Process voice text to determine choice
    # Keywords for each choice
    apply_keywords = ['apply', 'job', 'apply job', 'apply for job', 'find job', 'search job']
    post_keywords = ['post', 'post job', 'create job', 'add job', 'list job']
    learning_keywords = ['learn', 'learning', 'learning module', 'education', 'course', 'training']
    
    user_choice = None
    
    # Check for apply job
    if any(keyword in voice_text for keyword in apply_keywords):
        if 'post' not in voice_text:  # Avoid confusion with "post job"
            user_choice = 'apply_job'
    
    # Check for post job
    if not user_choice and any(keyword in voice_text for keyword in post_keywords):
        user_choice = 'post_job'
    
    # Check for learning module
    if not user_choice and any(keyword in voice_text for keyword in learning_keywords):
        user_choice = 'learning_module'
    
    if not user_choice:
        return jsonify({
            'success': False,
            'message': 'Could not understand your choice. Please say: apply job, post job, or learning module.',
            'recognized_text': voice_text
        }), 400
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Update user choice in database
        c.execute('UPDATE workers SET user_choice = ? WHERE phone_number = ?', 
                  (user_choice, phone))
        
        if c.rowcount == 0:
            # If no row updated, user might not exist - create a basic record
            ts = datetime.utcnow().isoformat()
            c.execute('''INSERT INTO workers (timestamp, phone_number, user_choice, profile_created) 
                        VALUES (?, ?, ?, 0)''', (ts, phone, user_choice))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'User choice saved successfully',
            'phone_number': phone,
            'user_choice': user_choice,
            'recognized_text': voice_text
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to save user choice: {str(e)}'
        }), 500

@app.route('/api/auth/user-choice/recognize', methods=['POST'])
@require_auth
def recognize_voice_choice():
    """Recognize voice input from audio file (multipart upload) and return the choice"""
    phone = get_phone_from_token()
    if not phone:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    # Check if audio file is provided
    if 'audio' not in request.files:
        return jsonify({
            'success': False,
            'message': 'Audio file is required. Send as multipart/form-data with field name "audio"'
        }), 400
    
    audio_file = request.files['audio']
    language = request.form.get('language', 'hi-IN')  # Default to Hindi
    
    # Validate audio file
    if audio_file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No audio file selected'
        }), 400
    
    try:
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Read audio file
        # Note: speech_recognition supports WAV, FLAC, AIFF formats
        # MP3 files need to be converted first
        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)
        except Exception as e:
            # Check if it's an unsupported format error
            error_msg = str(e).lower()
            if 'mp3' in error_msg or 'format' in error_msg or 'codec' in error_msg:
                return jsonify({
                    'success': False,
                    'message': f'Unsupported audio format. Please use WAV, FLAC, or AIFF format. Error: {str(e)}'
                }), 400
            else:
                raise
        
        # Recognize speech using Google Speech Recognition
        text = recognizer.recognize_google(audio_data, language=language)
        text_lower = text.lower()
        
        # Process to determine choice - support both English and Hindi
        # English keywords
        apply_keywords_en = ['apply', 'job', 'apply job', 'apply for job', 'find job', 'search job']
        post_keywords_en = ['post', 'post job', 'create job', 'add job', 'list job']
        learning_keywords_en = ['learn', 'learning', 'learning module', 'education', 'course', 'training', 'study']
        
        # Hindi keywords (both Devanagari and transliterated)
        apply_keywords_hi = ['अप्लाई', 'जॉब', 'नौकरी', 'काम', 'खोज', 'ढूंढ']
        post_keywords_hi = ['पोस्ट', 'नौकरी देना', 'भर्ती', 'विज्ञापन']
        learning_keywords_hi = [
            'सीखना', 'सीख', 'शिक्षा', 'पढ़ाई', 'पढ़ना', 'ट्रेनिंग', 'प्रशिक्षण',
            'कोर्स', 'मॉड्यूल', 'लर्निंग', 'एजुकेशन', 'ज्ञान', 'अध्ययन',
            'seekh', 'padhai', 'training', 'module'
        ]
        
        # Combine all keywords
        apply_keywords = apply_keywords_en + apply_keywords_hi
        post_keywords = post_keywords_en + post_keywords_hi
        learning_keywords = learning_keywords_en + learning_keywords_hi
        
        user_choice = None
        
        # Check for learning module FIRST (more specific)
        if any(keyword in text_lower for keyword in ['learning module', 'लर्निंग मॉड्यूल', 'module', 'मॉड्यूल']):
            user_choice = 'learning_module'
        elif any(keyword in text_lower for keyword in learning_keywords):
            user_choice = 'learning_module'
        
        # Check for post job
        if not user_choice and any(keyword in text_lower for keyword in post_keywords):
            user_choice = 'post_job'
        
        # Check for apply job (check last to avoid conflicts)
        if not user_choice and any(keyword in text_lower for keyword in apply_keywords):
            # Make sure it's not "post job"
            if not any(keyword in text_lower for keyword in ['post', 'पोस्ट']):
                user_choice = 'apply_job'
        
        if not user_choice:
            return jsonify({
                'success': False,
                'message': 'Could not understand your choice. Please say: apply job, post job, or learning module.',
                'recognized_text': text
            }), 400
        
        # Save choice to database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('UPDATE workers SET user_choice = ? WHERE phone_number = ?', 
                  (user_choice, phone))
        if c.rowcount == 0:
            ts = datetime.utcnow().isoformat()
            c.execute('''INSERT INTO workers (timestamp, phone_number, user_choice, profile_created) 
                        VALUES (?, ?, ?, 0)''', (ts, phone, user_choice))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'user_choice': user_choice,
            'recognized_text': text,
            'phone_number': phone
        }), 200
        
    except sr.UnknownValueError:
        return jsonify({
            'success': False,
            'message': 'Could not understand audio. Please try again.'
        }), 400
    except sr.RequestError as e:
        return jsonify({
            'success': False,
            'message': f'Speech recognition service error: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing audio: {str(e)}'
        }), 500

# ==================== ONBOARDING APIs ====================

@app.route('/api/onboarding/questions', methods=['GET'])
def get_questions():
    """Get onboarding questions (text only)"""
    language = request.args.get('language', 'en')
    
    questions = [
        {'key': 'name', 'en': 'What is your name?', 'hi': 'आपका नाम क्या है?'},
        {'key': 'skill', 'en': 'What is your skill? (eg: plumber, painter)', 'hi': 'आपका कौशल क्या है? (जैसे: पलंबर, पेंटर)'},
        {'key': 'education', 'en': 'What is your education level?', 'hi': 'आपकी शिक्षा क्या है?'},
        {'key': 'age', 'en': 'What is your age?', 'hi': 'आपकी उम्र क्या है?'},
        {'key': 'sex', 'en': 'What is your sex? (male/female)', 'hi': 'आपका लिंग क्या है? (पुरुष/महिला)'},
        {'key': 'experience', 'en': 'How many years of experience?', 'hi': 'अनुभव के वर्षों की संख्या क्या है?'},
        {'key': 'location', 'en': 'Which city or village are you from?', 'hi': 'आप किस शहर या गांव से हैं?'},
        {'key': 'wage_expected', 'en': 'What is your expected daily wage?', 'hi': 'आपकी अपेक्षित दैनिक मजदूरी क्या है?'},
        {'key': 'languages_known', 'en': 'Which languages do you know?', 'hi': 'आप किन भाषाओं को जानते हैं?'},
    ]
    
    return jsonify({
        'success': True,
        'questions': questions
    }), 200

@app.route('/api/onboarding/question/<question_key>', methods=['GET'])
def get_question_voice(question_key):
    """Get a specific onboarding question with voice audio"""
    language = request.args.get('language', 'en')
    
    questions_map = {
        'name': {'en': 'What is your name?', 'hi': 'आपका नाम क्या है?'},
        'skill': {'en': 'What is your skill? For example, plumber, painter, electrician?', 'hi': 'आपका कौशल क्या है? जैसे: पलंबर, पेंटर, इलेक्ट्रीशियन?'},
        'education': {'en': 'What is your education level?', 'hi': 'आपकी शिक्षा क्या है?'},
        'age': {'en': 'What is your age?', 'hi': 'आपकी उम्र क्या है?'},
        'sex': {'en': 'What is your sex? Male or female?', 'hi': 'आपका लिंग क्या है? पुरुष या महिला?'},
        'experience': {'en': 'How many years of experience do you have?', 'hi': 'आपको कितने वर्षों का अनुभव है?'},
        'location': {'en': 'Which city or village are you from?', 'hi': 'आप किस शहर या गांव से हैं?'},
        'wage_expected': {'en': 'What is your expected daily wage?', 'hi': 'आपकी अपेक्षित दैनिक मजदूरी क्या है?'},
        'languages_known': {'en': 'Which languages do you know?', 'hi': 'आप किन भाषाओं को जानते हैं?'},
    }
    
    if question_key not in questions_map:
        return jsonify({
            'success': False,
            'message': 'Invalid question key'
        }), 400
    
    question_text = questions_map[question_key].get(language, questions_map[question_key]['en'])
    
    try:
        # Generate TTS audio
        tts = gTTS(text=question_text, lang=language if language == 'hi' else 'en', slow=False)
        
        # Save to in-memory buffer
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        # Convert to base64 for JSON response
        audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'question_key': question_key,
            'question_text': question_text,
            'audio_base64': audio_base64,
            'language': language
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to generate audio: {str(e)}',
            'question_text': question_text,
            'audio_base64': None,
            'language': language
        }), 500

@app.route('/api/onboarding/answer', methods=['POST'])
@require_auth
def save_onboarding_answer():
    """Save a single onboarding answer (voice or text)"""
    phone = get_phone_from_token()
    if not phone:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    # Handle both multipart (voice) and JSON (text) requests
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Voice answer - process audio
        if 'audio' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Audio file is required for voice answer'
            }), 400
        
        audio_file = request.files['audio']
        question_key = request.form.get('question_key')
        language = request.form.get('language', 'hi-IN')  # Default to Hindi
        
        if not question_key:
            return jsonify({
                'success': False,
                'message': 'question_key is required'
            }), 400
        
        try:
            # Recognize speech from audio
            recognizer = sr.Recognizer()
            
            try:
                with sr.AudioFile(audio_file) as source:
                    audio_data = recognizer.record(source)
            except Exception as e:
                error_msg = str(e).lower()
                if 'mp3' in error_msg or 'format' in error_msg or 'codec' in error_msg:
                    return jsonify({
                        'success': False,
                        'message': f'Unsupported audio format. Please use WAV, FLAC, or AIFF format.'
                    }), 400
                else:
                    raise
            
            # Recognize speech
            answer_text = recognizer.recognize_google(audio_data, language=language)
            
            # Save to database (temporary storage until complete_onboarding)
            conn = get_db_connection()
            c = conn.cursor()
            
            # Get or create user record
            c.execute('SELECT raw_answers FROM workers WHERE phone_number = ?', (phone,))
            result = c.fetchone()
            
            if result and result['raw_answers']:
                answers = json.loads(result['raw_answers'])
            else:
                answers = {}
            
            # Update answer
            answers[question_key] = answer_text
            
            # Save back
            if result:
                c.execute('UPDATE workers SET raw_answers = ? WHERE phone_number = ?',
                         (json.dumps(answers, ensure_ascii=False), phone))
            else:
                ts = datetime.utcnow().isoformat()
                c.execute('''INSERT INTO workers (timestamp, phone_number, raw_answers, profile_created) 
                            VALUES (?, ?, ?, 0)''',
                         (ts, phone, json.dumps(answers, ensure_ascii=False)))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'question_key': question_key,
                'answer_text': answer_text,
                'phone_number': phone
            }), 200
            
        except sr.UnknownValueError:
            return jsonify({
                'success': False,
                'message': 'Could not understand audio. Please try again.'
            }), 400
        except sr.RequestError as e:
            return jsonify({
                'success': False,
                'message': f'Speech recognition service error: {str(e)}'
            }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error processing audio: {str(e)}'
            }), 500
    
    else:
        # Text answer
        data = request.get_json()
        question_key = data.get('question_key')
        answer_text = data.get('answer_text')
        
        if not question_key or not answer_text:
            return jsonify({
                'success': False,
                'message': 'question_key and answer_text are required'
            }), 400
        
        try:
            conn = get_db_connection()
            c = conn.cursor()
            
            # Get or create user record
            c.execute('SELECT raw_answers FROM workers WHERE phone_number = ?', (phone,))
            result = c.fetchone()
            
            if result and result['raw_answers']:
                answers = json.loads(result['raw_answers'])
            else:
                answers = {}
            
            # Update answer
            answers[question_key] = answer_text
            
            # Save back
            if result:
                c.execute('UPDATE workers SET raw_answers = ? WHERE phone_number = ?',
                         (json.dumps(answers, ensure_ascii=False), phone))
            else:
                ts = datetime.utcnow().isoformat()
                c.execute('''INSERT INTO workers (timestamp, phone_number, raw_answers, profile_created) 
                            VALUES (?, ?, ?, 0)''',
                         (ts, phone, json.dumps(answers, ensure_ascii=False)))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'question_key': question_key,
                'answer_text': answer_text,
                'phone_number': phone
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error saving answer: {str(e)}'
            }), 500

@app.route('/api/onboarding/complete', methods=['POST'])
@require_auth
def complete_onboarding():
    """Complete onboarding and save profile"""
    phone = get_phone_from_token()
    if not phone:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    answers = data.get('answers', {})
    
    if not answers:
        return jsonify({'success': False, 'message': 'Answers are required'}), 400
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if phone exists
        c.execute('SELECT id, profile_created FROM workers WHERE phone_number = ?', (phone,))
        existing = c.fetchone()
        
        raw_answers = json.dumps(answers, ensure_ascii=False)
        ts = datetime.utcnow().isoformat()
        
        if existing:
            # Update existing record
            c.execute('''UPDATE workers SET 
                timestamp = ?, profile_created = 1, name = ?, skill = ?, education = ?, age = ?, 
                sex = ?, experience = ?, location = ?, aadhaar = ?, wage_expected = ?, 
                languages_known = ?, raw_answers = ?
                WHERE id = ?''',
                (ts,
                 answers.get('name', ''),
                 answers.get('skill', ''),
                 answers.get('education', ''),
                 answers.get('age', ''),
                 answers.get('sex', ''),
                 answers.get('experience', ''),
                 answers.get('location', ''),
                 answers.get('aadhaar', ''),
                 answers.get('wage_expected', ''),
                 answers.get('languages_known', ''),
                 raw_answers,
                 existing['id']
                 ))
            worker_id = existing['id']
        else:
            # Insert new record
            c.execute('''INSERT INTO workers 
                (timestamp, phone_number, profile_created, name, skill, education, age, sex, 
                 experience, location, aadhaar, wage_expected, languages_known, raw_answers) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (ts, phone, 1,
                 answers.get('name', ''),
                 answers.get('skill', ''),
                 answers.get('education', ''),
                 answers.get('age', ''),
                 answers.get('sex', ''),
                 answers.get('experience', ''),
                 answers.get('location', ''),
                 answers.get('aadhaar', ''),
                 answers.get('wage_expected', ''),
                 answers.get('languages_known', ''),
                 raw_answers
                 ))
            worker_id = c.lastrowid
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Onboarding complete and saved',
            'worker_id': worker_id,
            'phone_number': phone
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to save onboarding: {str(e)}'
        }), 500

# ==================== WORKER PROFILE APIs ====================

@app.route('/api/worker/profile', methods=['GET'])
@require_auth
def get_worker_profile():
    """Get current worker's profile"""
    phone = get_phone_from_token()
    if not phone:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''SELECT id, phone_number, name, skill, education, age, sex, experience, 
                 location, aadhaar, wage_expected, languages_known, profile_created, timestamp
                 FROM workers WHERE phone_number = ?''', (phone,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'success': False, 'message': 'Profile not found'}), 404
    
    profile = dict(row)
    return jsonify({
        'success': True,
        'profile': profile
    }), 200

@app.route('/api/worker/profile', methods=['PUT'])
@require_auth
def update_worker_profile():
    """Update worker profile"""
    phone = get_phone_from_token()
    if not phone:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    data = request.get_json()
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''UPDATE workers SET 
            name = ?, skill = ?, education = ?, age = ?, sex = ?, experience = ?, 
            location = ?, wage_expected = ?, languages_known = ?
            WHERE phone_number = ?''',
            (data.get('name'),
             data.get('skill'),
             data.get('education'),
             data.get('age'),
             data.get('sex'),
             data.get('experience'),
             data.get('location'),
             data.get('wage_expected'),
             data.get('languages_known'),
             phone
             ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to update profile: {str(e)}'
        }), 500

# ==================== ADMIN APIs ====================

@app.route('/api/admin/workers', methods=['GET'])
@require_auth
def get_all_workers():
    """Get all workers (admin)"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    search = request.args.get('search', '')
    
    offset = (page - 1) * limit
    
    conn = get_db_connection()
    c = conn.cursor()
    
    if search:
        c.execute('''SELECT id, phone_number, name, skill, education, age, sex, experience, 
                     location, aadhaar, wage_expected, languages_known, profile_created, timestamp
                     FROM workers 
                     WHERE name LIKE ? OR phone_number LIKE ? OR skill LIKE ?
                     ORDER BY id DESC LIMIT ? OFFSET ?''',
                     (f'%{search}%', f'%{search}%', f'%{search}%', limit, offset))
    else:
        c.execute('''SELECT id, phone_number, name, skill, education, age, sex, experience, 
                     location, aadhaar, wage_expected, languages_known, profile_created, timestamp
                     FROM workers ORDER BY id DESC LIMIT ? OFFSET ?''',
                     (limit, offset))
    
    rows = c.fetchall()
    
    # Get total count
    if search:
        c.execute('SELECT COUNT(*) FROM workers WHERE name LIKE ? OR phone_number LIKE ? OR skill LIKE ?',
                 (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        c.execute('SELECT COUNT(*) FROM workers')
    total = c.fetchone()[0]
    
    conn.close()
    
    workers = [dict(row) for row in rows]
    
    return jsonify({
        'success': True,
        'workers': workers,
        'total': total,
        'page': page,
        'limit': limit
    }), 200

@app.route('/api/admin/workers/<int:worker_id>', methods=['GET'])
@require_auth
def get_worker_by_id(worker_id):
    """Get worker by ID (admin)"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''SELECT * FROM workers WHERE id = ?''', (worker_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'success': False, 'message': 'Worker not found'}), 404
    
    return jsonify({
        'success': True,
        'worker': dict(row)
    }), 200

@app.route('/api/admin/workers/<int:worker_id>', methods=['PUT'])
@require_auth
def update_worker_admin(worker_id):
    """Update worker (admin)"""
    data = request.get_json()
    
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''UPDATE workers SET 
            name = ?, skill = ?, education = ?, age = ?, sex = ?, experience = ?, 
            location = ?, wage_expected = ?, languages_known = ?
            WHERE id = ?''',
            (data.get('name'),
             data.get('skill'),
             data.get('education'),
             data.get('age'),
             data.get('sex'),
             data.get('experience'),
             data.get('location'),
             data.get('wage_expected'),
             data.get('languages_known'),
             worker_id
             ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Worker updated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to update worker: {str(e)}'
        }), 500

@app.route('/api/admin/workers/<int:worker_id>', methods=['DELETE'])
@require_auth
def delete_worker(worker_id):
    """Delete worker (admin)"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM workers WHERE id = ?', (worker_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Worker deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to delete worker: {str(e)}'
        }), 500

@app.route('/api/admin/workers/export', methods=['GET'])
@require_auth
def export_workers_csv():
    """Export workers to CSV (admin)"""
    import csv
    import io
    
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''SELECT id, timestamp, phone_number, name, skill, education, age, sex, 
                 experience, location, aadhaar, wage_expected, languages_known, raw_answers 
                 FROM workers ORDER BY id''')
    rows = c.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['id', 'timestamp', 'phone_number', 'name', 'skill', 'education', 'age', 
                     'sex', 'experience', 'location', 'aadhaar', 'wage_expected', 
                     'languages_known', 'raw_answers'])
    
    # Write data
    for row in rows:
        writer.writerow([row['id'], row['timestamp'], row['phone_number'], row['name'], 
                        row['skill'], row['education'], row['age'], row['sex'], 
                        row['experience'], row['location'], row['aadhaar'], 
                        row['wage_expected'], row['languages_known'], row['raw_answers']])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='workers_export.csv'
    )

# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'message': 'API server is running',
        'status': 'healthy'
    }), 200

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Get local IP address for network access
    import socket
    try:
        # Get local IP by connecting to external address (doesn't actually send data)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "Unable to detect IP"
    
    # Run server
    print("=" * 70)
    print("🚀 API Server Starting...")
    print("=" * 70)
    print(f"✅ Local access:    http://localhost:5000")
    print(f"✅ Local access:    http://127.0.0.1:5000")
    print(f"🌐 Network access:  http://{local_ip}:5000")
    print("=" * 70)
    print("📱 From other devices (same Wi-Fi), use:")
    print(f"   http://{local_ip}:5000")
    print("=" * 70)
    print("Press CTRL+C to stop the server")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=5000, debug=True)


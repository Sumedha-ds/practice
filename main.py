import sys
import json
import sqlite3
import os
from datetime import datetime

# Compatibility shims for modules removed in Python 3.13
# These are needed by speech_recognition library
import types

# aifc compatibility shim
try:
    import aifc
except ModuleNotFoundError:
    aifc_module = types.ModuleType('aifc')
    aifc_module.Error = Exception
    aifc_module.open = lambda *args, **kwargs: None  # Stub function
    sys.modules['aifc'] = aifc_module

# audioop compatibility - try to import audioop-lts package first (proper replacement)
# If not available, create minimal stubs (though audioop-lts should be installed)
try:
    import audioop
except ModuleNotFoundError:
    try:
        # Try importing from audioop-lts package if installed
        import audioop_lts as audioop
        sys.modules['audioop'] = audioop
    except ImportError:
        # Fallback: Create minimal stubs (not recommended - install audioop-lts instead)
        def _audioop_stub(*args, **kwargs):
            """Stub for audioop functions - returns empty bytes or input"""
            if args:
                return args[0] if isinstance(args[0], bytes) else b''
            return b''
        
        audioop_module = types.ModuleType('audioop')
        # Common audioop functions that speech_recognition might use
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
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QComboBox,
    QGraphicsOpacityEffect,
    QScrollArea,
    QStatusBar,
    QPlainTextEdit,
    QLabel,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHBoxLayout,
    QDialog,
    QLineEdit,
    QMessageBox,
)
from PyQt5.QtCore import (
    QThread,
    pyqtSignal,
    QUrl,
    QPropertyAnimation,
    QEasingCurve
)
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont
import speech_recognition as sr
from translate import Translator
from gtts import gTTS
import requests
import urllib.parse
import re
import difflib


class SpeechRecognitionThread(QThread):
    recognition_result = pyqtSignal(str)
    status_signal = pyqtSignal(str)

    def __init__(self, recognizer, language=None):
        super().__init__()
        self.recognizer = recognizer
        # language passed to recognizer.recognize_google, e.g. 'en-US' or 'hi-IN'
        self.language = language

    def run(self):
        try:
            with sr.Microphone() as source:
                self.status_signal.emit("Adjusting for ambient noise...")
                # Adjust for ambient noise and set timeout
                try:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                except Exception:
                    # If adjust fails, continue with defaults
                    pass
                # tweak thresholds for better capture
                try:
                    self.recognizer.energy_threshold = 4000
                    self.recognizer.dynamic_energy_threshold = True
                except Exception:
                    pass
                self.status_signal.emit("Microphone ready - speak now")

                # Listen with reasonable timeout and phrase limit
                try:
                    audio = self.recognizer.listen(
                        source,
                        timeout=10,  # max seconds to wait for phrase to start
                        phrase_time_limit=30,  # max seconds for phrase
                    )
                    self.status_signal.emit("Audio recorded")
                except sr.WaitTimeoutError:
                    # No speech detected in timeout window - emit empty result to keep flow
                    self.status_signal.emit("No speech detected (timeout)")
                    self.recognition_result.emit("")
                    return

            try:
                self.status_signal.emit("Recognizing...")
                # pass language if provided
                if self.language:
                    text = self.recognizer.recognize_google(audio, language=self.language)
                else:
                    text = self.recognizer.recognize_google(audio)
                self.status_signal.emit("Audio recognized")
                # Emit recognized text (could be empty if recognition returns '')
                self.recognition_result.emit(text)
            except sr.UnknownValueError:
                # Could not understand audio - emit empty string so callers continue
                self.status_signal.emit("Could not understand audio")
                self.recognition_result.emit("")
            except sr.RequestError as e:
                # API was unreachable or unresponsive - emit empty and report
                self.status_signal.emit(f"Recognition request failed: {e}")
                self.recognition_result.emit("")
        except Exception as e:
            # Any other microphone/IO error - emit empty so caller doesn't block
            self.status_signal.emit(f"An error occurred: {str(e)}")
            try:
                self.recognition_result.emit("")
            except Exception:
                pass


class LoginDialog(QDialog):
    """Login dialog with phone number and OTP verification"""
    login_success = pyqtSignal(str)  # Emits phone number on successful login
    new_user = pyqtSignal(str)  # Emits phone number for new user onboarding
    
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.db_path = db_path
        self.otp = None
        self.phone_number = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle('Login - Phone Number & OTP')
        self.setGeometry(200, 200, 400, 300)
        
        layout = QVBoxLayout()
        
        # Phone number input
        phone_label = QLabel('Phone Number:')
        phone_label.setFont(QFont('Arial', 12))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText('Enter 10-digit phone number')
        self.phone_input.setFont(QFont('Arial', 12))
        self.phone_input.setMaxLength(10)
        # Only allow digits
        self.phone_input.textChanged.connect(self.validate_phone)
        
        # OTP input (initially hidden)
        otp_label = QLabel('OTP:')
        otp_label.setFont(QFont('Arial', 12))
        otp_label.setVisible(False)
        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText('Enter 6-digit OTP')
        self.otp_input.setFont(QFont('Arial', 12))
        self.otp_input.setMaxLength(6)
        self.otp_input.setVisible(False)
        self.otp_input.textChanged.connect(self.validate_otp)
        self.otp_label = otp_label
        
        # Buttons
        self.send_otp_button = QPushButton('Send OTP')
        self.send_otp_button.setStyleSheet(
            "QPushButton { background-color: #2196F3; border: none; color: white; padding: 10px; font-size: 14px; border-radius: 6px;}"
            "QPushButton:hover { background-color: #1976D2; }"
            "QPushButton:disabled { background-color: #ccc; }"
        )
        self.send_otp_button.clicked.connect(self.send_otp)
        
        self.verify_otp_button = QPushButton('Verify OTP & Login')
        self.verify_otp_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; border: none; color: white; padding: 10px; font-size: 14px; border-radius: 6px;}"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:disabled { background-color: #ccc; }"
        )
        self.verify_otp_button.clicked.connect(self.verify_otp)
        self.verify_otp_button.setVisible(False)
        self.verify_otp_button.setEnabled(False)
        
        # Status label
        self.status_label = QLabel('')
        self.status_label.setStyleSheet("color: red;")
        self.status_label.setWordWrap(True)
        
        # Layout
        layout.addWidget(phone_label)
        layout.addWidget(self.phone_input)
        layout.addWidget(otp_label)
        layout.addWidget(self.otp_input)
        layout.addWidget(self.send_otp_button)
        layout.addWidget(self.verify_otp_button)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def validate_phone(self):
        """Validate phone number input (only digits, 10 digits)"""
        text = self.phone_input.text()
        # Remove non-digits
        digits_only = ''.join(filter(str.isdigit, text))
        if digits_only != text:
            self.phone_input.setText(digits_only)
        # Enable/disable send OTP button
        self.send_otp_button.setEnabled(len(digits_only) == 10)
    
    def validate_otp(self):
        """Validate OTP input (only digits, 6 digits)"""
        text = self.otp_input.text()
        # Remove non-digits
        digits_only = ''.join(filter(str.isdigit, text))
        if digits_only != text:
            self.otp_input.setText(digits_only)
        # Enable/disable verify button
        self.verify_otp_button.setEnabled(len(digits_only) == 6)
    
    def generate_otp(self):
        """Generate a 6-digit OTP"""
        import random
        return str(random.randint(100000, 999999))
    
    def send_otp(self):
        """Send OTP to phone number"""
        phone = self.phone_input.text().strip()
        if len(phone) != 10 or not phone.isdigit():
            self.status_label.setText('Please enter a valid 10-digit phone number')
            return
        
        # Generate and store OTP
        self.otp = self.generate_otp()
        self.phone_number = phone
        
        # In a real application, you would send this OTP via SMS
        # For now, we'll display it (in production, use SMS service like Twilio)
        self.status_label.setText(f'OTP sent! (Demo: Your OTP is {self.otp})')
        self.status_label.setStyleSheet("color: green;")
        
        # Show OTP input and verify button
        self.otp_label.setVisible(True)
        self.otp_input.setVisible(True)
        self.verify_otp_button.setVisible(True)
        self.phone_input.setEnabled(False)
        self.send_otp_button.setEnabled(False)
        
        # Clear OTP input
        self.otp_input.clear()
        self.otp_input.setFocus()
    
    def verify_otp(self):
        """Verify OTP and check if profile exists (accept any 6-digit OTP)"""
        entered_otp = self.otp_input.text().strip()
        
        # Accept any 6-digit number (no validation)
        if len(entered_otp) != 6 or not entered_otp.isdigit():
            self.status_label.setText('Please enter a 6-digit OTP')
            self.status_label.setStyleSheet("color: red;")
            return
        
        # OTP accepted (any 6-digit number), check if profile exists
        profile_exists = self.check_profile_exists(self.phone_number)
        
        print(f"DEBUG: Phone: {self.phone_number}, Profile exists: {profile_exists}")  # Debug output
        
        if profile_exists:
            # Profile exists - onboarding completed
            self.status_label.setText('Onboarding completed! Login successful.')
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            # Show message for longer before closing
            QTimer.singleShot(2000, lambda: self.accept())
            QTimer.singleShot(2000, lambda: self.login_success.emit(self.phone_number))
        else:
            # No profile - trigger onboarding
            self.status_label.setText('No profile found. Starting onboarding...')
            self.status_label.setStyleSheet("color: blue;")
            QTimer.singleShot(2000, lambda: self.accept())
            QTimer.singleShot(2000, lambda: self.new_user.emit(self.phone_number))
    
    def check_profile_exists(self, phone):
        """Check if profile is created for this phone number"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            # Check if phone exists AND profile_created = 1
            c.execute('SELECT profile_created FROM workers WHERE phone_number = ?', (phone,))
            result = c.fetchone()
            conn.close()
            # Return True if profile_created = 1, False otherwise
            if result is not None:
                profile_created = result[0]
                print(f"DEBUG: Found phone {phone}, profile_created = {profile_created}")
                return profile_created == 1
            else:
                print(f"DEBUG: Phone {phone} not found in database")
                return False
        except Exception as e:
            print(f"Error checking profile: {e}")
            import traceback
            traceback.print_exc()
            return False


class VoiceConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.current_phone = None  # Store current logged-in phone number
        self.init_ui()
        # Show login dialog first
        self.show_login()

    def init_ui(self):
        self.setGeometry(100, 100, 800, 600)  # Increased window size
        self.setWindowTitle('Multilingual Voice Transcriber and Translator')
        # Initially hide the main window until login
        self.hide()

        self.start_button_label = QLabel('Start Recording', self)
        self.start_button = QPushButton('Start Recording', self)
        self.start_button.setStyleSheet(
            "QPushButton {"
            " background-color: #4CAF50;"
            " border: none;"
            " color: white;"
            " padding: 10px;"
            " font-size: 16px;"
            " border-radius: 6px;"
            "}"
            "QPushButton:hover {"
            " background-color: #45a049;"
            "}"
        )

        self.spoken_scroll_area = QScrollArea(self)
        self.spoken_label = QPlainTextEdit(self.spoken_scroll_area)
        self.spoken_label.setFont(QFont('Arial', 14))  # Increased font size
        self.spoken_label.setReadOnly(True)
        self.spoken_scroll_area.setWidgetResizable(True)
        self.spoken_scroll_area.setWidget(self.spoken_label)
        # Hide spoken and translated areas as per requirement
        self.spoken_scroll_area.setVisible(False)

        self.translated_scroll_area = QScrollArea(self)
        self.translated_label = QPlainTextEdit(self.translated_scroll_area)
        # Increased font size
        self.translated_label.setFont(QFont('Arial', 14))
        self.translated_label.setReadOnly(True)
        self.translated_scroll_area.setWidgetResizable(True)
        self.translated_scroll_area.setWidget(self.translated_label)
        self.translated_scroll_area.setVisible(False)

        self.language_dropdown = QComboBox(self)
        # Increased font size
        self.language_dropdown.setFont(QFont('Arial', 14))
        # Restrict to two translation directions: English<->Hindi
        # Each entry maps to source recognition locale and language codes
        self.preset_langs = {
            'English to Hindi': {'src_code': 'en', 'src_recog': 'en-US', 'tgt_code': 'hi'},
            'Hindi to English': {'src_code': 'hi', 'src_recog': 'hi-IN', 'tgt_code': 'en'},
        }
        self.language_dropdown.addItems(list(self.preset_langs.keys()))

        self.status_bar = QStatusBar(self)

        # Removed Download/Copy/History buttons per user request
        # Onboard worker button
        self.onboard_button = QPushButton('Onboard Worker', self)
        self.onboard_button.setStyleSheet(
            "QPushButton { background-color: #6A5ACD; border: none; color: white; padding: 10px; font-size: 14px; border-radius: 6px;}"
        )
        self.onboard_button.clicked.connect(self.start_onboarding)

        # Admin dashboard button
        self.admin_button = QPushButton('Admin Dashboard', self)
        self.admin_button.setStyleSheet(
            "QPushButton { background-color: #444; border: none; color: white; padding: 8px; font-size: 12px; border-radius: 6px;}"
        )
        self.admin_button.clicked.connect(self.show_admin_dashboard)

        # Logout button
        self.logout_button = QPushButton('Logout', self)
        self.logout_button.setStyleSheet(
            "QPushButton { background-color: #f44336; border: none; color: white; padding: 8px; font-size: 12px; border-radius: 6px;}"
            "QPushButton:hover { background-color: #d32f2f; }"
        )
        self.logout_button.clicked.connect(self.logout)

        vbox = QVBoxLayout()
        vbox.addWidget(self.language_dropdown)
        # Onboarding + admin
        vbox.addWidget(self.onboard_button)
        vbox.addWidget(self.admin_button)
        vbox.addWidget(self.logout_button)
        # Do not add start button or text areas to layout (hidden)
        vbox.addWidget(self.status_bar)

        # Add some spacing between widgets
        vbox.setSpacing(15)

        self.setLayout(vbox)

        # Hide the start button and disable interaction
        self.start_button.setVisible(False)
        try:
            self.start_button.clicked.disconnect()
        except Exception:
            pass

        self.recording = False
        self.selected_src = None
        self.selected_tgt = None
        self.selected_recog = None
        # translator will be set per-request
        self.translator = Translator(to_lang="")

        # create a recognition thread placeholder; real one created when recording starts
        self.recognition_thread = SpeechRecognitionThread(sr.Recognizer())
        self.recognition_thread.recognition_result.connect(
            self.translate_and_play
        )
        self.recognition_thread.status_signal.connect(self.update_status)
        self.recognition_thread.finished.connect(self.on_recognition_finished)

        self.player = QMediaPlayer()

        self.fade_in_animation()

        # initialize DB
        self.db_path = os.path.join(os.path.dirname(__file__), 'transcripts.db')
        self.init_db()
        # prepare audio directory for all generated audio files
        self.audio_dir = os.path.join(os.path.dirname(__file__), 'audio')
        try:
            os.makedirs(self.audio_dir, exist_ok=True)
        except Exception:
            pass

        # onboarding state
        self.onboarding = False
        self.onboard_questions = []
        self.onboard_answers = {}
        self.current_question_index = 0
        self.onboard_phone = None  # Phone number for new user onboarding
        # CSV export helper (local import)
        import csv

        # Ensure threads are shut down when the application quits
        try:
            app = QApplication.instance()
            if app is not None:
                app.aboutToQuit.connect(self._shutdown_threads)
        except Exception:
            pass

    def fade_in_animation(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(1000)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()

    def init_db(self):
        """Initialize SQLite DB and create table if missing."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                '''
                CREATE TABLE IF NOT EXISTS transcripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    src_lang TEXT,
                    tgt_lang TEXT,
                    original_text TEXT,
                    translated_text TEXT,
                    audio_path TEXT
                )
                '''
            )
            conn.commit()
            # workers table for onboarding profiles
            c.execute(
                '''
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
                '''
            )
            conn.commit()
            # Add missing columns if they don't exist (for existing databases)
            try:
                # Check if columns exist first
                c.execute("PRAGMA table_info(workers)")
                columns = [row[1] for row in c.fetchall()]
                
                if 'phone_number' not in columns:
                    c.execute("ALTER TABLE workers ADD COLUMN phone_number TEXT")
                    conn.commit()
                
                if 'profile_created' not in columns:
                    c.execute("ALTER TABLE workers ADD COLUMN profile_created INTEGER DEFAULT 0")
                    conn.commit()
                    # Update existing records to have profile_created = 1 (they have profiles)
                    c.execute("UPDATE workers SET profile_created = 1 WHERE profile_created IS NULL OR profile_created = 0")
                    conn.commit()
            except sqlite3.OperationalError as e:
                # Column might already exist or other error
                print(f"Note: {e}")
                pass
        finally:
            conn.close()

    def _fallback_google_translate(self, text, src, tgt):
        """Use the unofficial Google Translate web API as a fallback.
        Returns translated text or raises on failure.
        """
        try:
            # build request to translate.googleapis.com
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
            # data[0] contains list of translation segments
            parts = [seg[0] for seg in data[0] if seg and seg[0]]
            return ''.join(parts)
        except Exception as e:
            raise

    def _is_suspicious_translation(self, src_text, translated_text):
        """Detect obviously-broken translations: identical to source or many tiny-line fragments.
        Returns True if translation looks bad.
        """
        if not translated_text:
            return True
        # identical or trivial
        if translated_text.strip() == src_text.strip():
            return True
        # too short compared to source
        if len(translated_text.strip()) < max(3, len(src_text.strip()) // 3):
            return True
        # multiple short lines or many single-letter tokens
        lines = translated_text.splitlines()
        short_lines = sum(1 for L in lines if len(L.strip()) <= 2)
        if len(lines) >= 2 and short_lines >= len(lines) // 2:
            return True
        # suspicious repeated single-letter tokens
        tokens = re.findall(r"\b\w\b", translated_text)
        if len(tokens) >= 2:
            # e.g., "s \n S \n Sinivas" produces single letters
            return True
        return False

    def _contains_hindi(self, text):
        try:
            return bool(re.search(r'[\u0900-\u097F]', str(text or '')))
        except Exception:
            return False

    def _normalize_digits(self, text):
        """Convert Devanagari digits to ASCII and trim spaces inside digit groups."""
        if text is None:
            return ''
        s = str(text)
        # Map Devanagari digits to ASCII
        trans = str.maketrans('०१२३४५६७८९', '0123456789')
        s = s.translate(trans)
        # Collapse spaces between digits like '1 2 3' -> '123' only for long digit runs
        s = re.sub(r'(?<=\d)\s+(?=\d)', '', s)
        return s

    def _translate_to_english(self, text, assumed_src=None):
        """Translate arbitrary text to English with fallback and heuristics."""
        try:
            src = assumed_src
            if src is None:
                src = 'hi' if self._contains_hindi(text) else 'en'
            if src == 'en':
                return text
            # primary
            try:
                t = Translator(from_lang=src, to_lang='en').translate(text)
            except Exception:
                t = ''
            if not t or self._is_suspicious_translation(str(text or ''), t):
                try:
                    t_fb = self._fallback_google_translate(str(text or ''), src, 'en')
                    return t_fb or t or str(text or '')
                except Exception:
                    return t or str(text or '')
            return t
        except Exception:
            return str(text or '')

    def _normalize_languages(self, text):
        """Normalize language list to canonical English names using fuzzy match."""
        if not text:
            return ''
        canonical = [
            'Hindi','English','Kannada','Telugu','Marathi','Bengali','Tamil','Gujarati',
            'Urdu','Punjabi','Malayalam','Odia','Assamese','Konkani'
        ]
        # common confusions map
        manual = {
            'canada': 'Kannada',
            'kanada': 'Kannada',
            'kannad': 'Kannada',
            'hinglish': 'English',
            'eng': 'English',
            'hin': 'Hindi',
        }
        tokens = re.split(r'[,\|/]+|\s{2,}', str(text))
        out = []
        for tok in tokens:
            t = tok.strip()
            if not t:
                continue
            lower = t.lower()
            if lower in manual:
                out.append(manual[lower])
                continue
            # fuzzy to canonical
            match = difflib.get_close_matches(t, canonical, n=1, cutoff=0.75)
            if not match:
                match = difflib.get_close_matches(t.title(), canonical, n=1, cutoff=0.72)
            out.append(match[0] if match else t)
        # de-duplicate while preserving order
        seen = set()
        uniq = []
        for l in out:
            if l and l not in seen:
                seen.add(l)
                uniq.append(l)
        return ' '.join(uniq)

    def _normalize_skill(self, text):
        """Map common Hindi/phonetic variants to English roles; otherwise return the cleaned English text."""
        if not text:
            return ''
        s = str(text).strip()
        # Translate to English if appears Hindi
        if self._contains_hindi(s):
            s = self._translate_to_english(s, assumed_src='hi')
        lower = s.lower()
        replacements = {
            'vaidya': 'Doctor',
            'vaidhya': 'Doctor',
            'vaid': 'Doctor',
            'vedya': 'Doctor',
            'doctor': 'Doctor',
            'physician': 'Doctor',
            'plumber': 'Plumber',
            'painter': 'Painter',
            'carpenter': 'Carpenter',
            'electrician': 'Electrician',
            'software engineer': 'Software Engineer',
            'driver': 'Driver',
            'cook': 'Cook',
            'chef': 'Cook',
            'mason': 'Mason',
        }
        # choose best fuzzy match among keys
        keys = list(replacements.keys())
        match = difflib.get_close_matches(lower, keys, n=1, cutoff=0.8)
        if match:
            return replacements[match[0]]
        # try looser cutoff
        match = difflib.get_close_matches(lower, keys, n=1, cutoff=0.7)
        if match:
            return replacements[match[0]]
        # Capitalize words
        return ' '.join(w.capitalize() for w in s.split())

    def _normalize_gender(self, text):
        if not text:
            return ''
        s = str(text).strip().lower()
        mapping = {
            'male': 'Male',
            'man': 'Male',
            'men': 'Male',
            'female': 'Female',
            'woman': 'Female',
            'women': 'Female',
            'पुरुष': 'Male',
            'महिला': 'Female',
        }
        if s in mapping:
            return mapping[s]
        # fuzzy
        match = difflib.get_close_matches(s, list(mapping.keys()), n=1, cutoff=0.8)
        return mapping.get(match[0], s.capitalize() if s else '')

    def _parse_number_words(self, text):
        """Parse simple English/Hindi number words to digits. Returns string digits or ''."""
        if not text:
            return ''
        s = str(text).strip().lower()
        # Remove non-letter separators
        s = re.sub(r'[^a-zA-Z\u0900-\u097F\s\-]', ' ', s)
        tokens = s.split()
        # Basic mappings up to 100 and common tens
        en = {
            'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,
            'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18,'nineteen':19,
            'twenty':20,'thirty':30,'forty':40,'fifty':50,'sixty':60,'seventy':70,'eighty':80,'ninety':90,'hundred':100
        }
        hi = {
            'शून्य':0,'एक':1,'दो':2,'तीन':3,'चार':4,'पांच':5,'पाँच':5,'छह':6,'सात':7,'आठ':8,'नौ':9,
            'दस':10,'ग्यारह':11,'बारह':12,'तेरह':13,'चौदह':14,'पंद्रह':15,'सोलह':16,'सत्रह':17,'अठारह':18,'उन्नीस':19,
            'बीस':20,'तीस':30,'चालीस':40,'पचास':50,'साठ':60,'सत्तर':70,'अस्सी':80,'नब्बे':90,'सौ':100
        }
        total = 0
        current = 0
        matched = False
        for t in tokens:
            if t in en:
                val = en[t]
                matched = True
            elif t in hi:
                val = hi[t]
                matched = True
            else:
                continue
            if val == 100:
                current = max(1, current) * val
            elif val >= 20 and val % 10 == 0:
                current += val
            else:
                current += val
        total += current
        return str(total) if matched and total > 0 else ''

    # ----------------- Login flow -----------------
    def show_login(self):
        """Show login dialog"""
        login_dialog = LoginDialog(self.db_path, self)
        login_dialog.login_success.connect(self.on_login_success)
        login_dialog.new_user.connect(self.on_new_user)
        login_dialog.exec_()
    
    def on_login_success(self, phone_number):
        """Handle successful login for existing user"""
        self.current_phone = phone_number
        self.update_status(f'Logged in as: {phone_number}')
        # Show the main dashboard
        self.show()
    
    def on_new_user(self, phone_number):
        """Handle new user - start onboarding"""
        self.onboard_phone = phone_number
        self.current_phone = phone_number
        self.update_status(f'New user: {phone_number}. Starting onboarding...')
        # Show the main window first
        self.show()
        # Start onboarding flow
        self.start_onboarding()
    
    def logout(self):
        """Logout and show login dialog again"""
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.current_phone = None
            self.onboard_phone = None
            self.hide()
            self.show_login()
    
    # ----------------- Onboarding flow -----------------
    def start_onboarding(self):
        # prepare onboarding questions
        if self.recording:
            self.update_status('Busy recording; try later')
            return
        sel = self.language_dropdown.currentText()
        cfg = self.preset_langs.get(sel)
        if not cfg:
            self.update_status('Select language direction')
            return
        self.selected_src = cfg['src_code']
        self.selected_tgt = cfg['tgt_code']
        self.selected_recog = cfg['src_recog']

        # questions with English and Hindi prompt texts (Aadhaar removed)
        self.onboard_questions = [
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
        self.onboard_answers = {}
        self.current_question_index = 0
        self.onboarding = True
        # per-question retry counters to avoid stalling on short/noisy answers
        self.onboard_retries = {}
        self.update_status('Starting onboarding')
        self.ask_next_onboard_question()

    def ask_next_onboard_question(self):
        if self.current_question_index >= len(self.onboard_questions):
            self.finish_onboarding()
            return
        q = self.onboard_questions[self.current_question_index]
        # choose prompt language based on selected_src
        prompt = q['hi'] if self.selected_src == 'hi' else q['en']
        # speak prompt then listen
        self.speak_prompt_and_listen(prompt)

    def speak_prompt_and_listen(self, prompt_text):
        # create TTS file and play; on playback end, start recognizer
        try:
            tts = gTTS(prompt_text, lang=self.selected_src)
            fname = os.path.join(self.audio_dir, f"onboard_prompt_{int(datetime.utcnow().timestamp())}.mp3")
            tts.save(fname)
        except Exception as e:
            self.update_status(f"TTS failed: {e}")
            # still proceed to listen
            fname = None

        if fname:
            # connect a one-shot handler to start listening when playback ends
            def _on_status(status):
                from PyQt5.QtMultimedia import QMediaPlayer
                if status == QMediaPlayer.EndOfMedia:
                    try:
                        self.player.mediaStatusChanged.disconnect(_on_status)
                    except Exception:
                        pass
                    # start recognition
                    self.start_onboard_recognition()

            try:
                self.player.setMedia(QMediaContent(QUrl.fromLocalFile(fname)))
                self.player.play()
                self.player.mediaStatusChanged.connect(_on_status)
            except Exception:
                # fallback: start recognition immediately
                self.start_onboard_recognition()
        else:
            self.start_onboard_recognition()

    def start_onboard_recognition(self):
        # start a recognition thread for onboarding
        # ensure any previous thread is stopped before creating new one
        try:
            if hasattr(self, 'recognition_thread') and self.recognition_thread is not None:
                if self.recognition_thread.isRunning():
                    try:
                        self.recognition_thread.terminate()
                    except Exception:
                        pass
                    try:
                        self.recognition_thread.wait(500)
                    except Exception:
                        pass
                try:
                    self.recognition_thread.deleteLater()
                except Exception:
                    pass
        except Exception:
            pass

        self.recognition_thread = SpeechRecognitionThread(sr.Recognizer(), language=self.selected_recog)
        self.recognition_thread.recognition_result.connect(self.handle_onboard_answer)
        self.recognition_thread.status_signal.connect(self.update_status)
        self.recognition_thread.finished.connect(self.on_recognition_finished)
        self.recognition_thread.start()

    def handle_onboard_answer(self, text):
        # store answer for current question
        try:
            q = self.onboard_questions[self.current_question_index]
        except Exception:
            return
        # normalize text
        text_norm = '' if text is None else ' '.join(str(text).split())

        # if nothing recognized, allow a retry or move on after 2 attempts
        if not text_norm:
            tries = self.onboard_retries.get(self.current_question_index, 0) + 1
            self.onboard_retries[self.current_question_index] = tries
            if tries <= 2:
                # retry same question: prompt again
                self.update_status(f"Didn't catch that for {q['key']}. Retrying ({tries}/2)")
                # ask the same question again after a short pause
                QTimer.singleShot(500, self.ask_next_onboard_question)
                return
            else:
                # record empty answer and move on
                self.update_status(f"Skipping {q['key']} after {tries} failed attempts")

        # Early normalization for gender to reduce errors
        if q['key'] == 'sex':
            text_norm = self._normalize_gender(text_norm)
        # Early numeric extraction for experience/age/wage_expected (not aadhaar - store as string)
        if q['key'] in ('age','experience','wage_expected'):
            # prefer digits if present, else parse words
            digits = self._normalize_digits(text_norm)
            if not digits:
                digits = self._parse_number_words(text_norm)
            text_norm = digits or text_norm
        # For aadhaar, just store the raw string value as-is

        self.onboard_answers[q['key']] = text_norm
        self.update_status(f"Captured answer for {q['key']}")
        self.current_question_index += 1
        # small pause then ask next using QTimer
        QTimer.singleShot(300, self.ask_next_onboard_question)

    def finish_onboarding(self):
        # Persist worker record directly using normalization pipeline (no dialog)
        try:
            # Check if phone number already exists (shouldn't happen, but safety check)
            if not self.onboard_phone:
                self.update_status('Error: No phone number found for onboarding')
                self.onboarding = False
                return
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Check if phone number already exists
            c.execute('SELECT id, profile_created FROM workers WHERE phone_number = ?', (self.onboard_phone,))
            existing = c.fetchone()
            
            raw = json.dumps(self.onboard_answers, ensure_ascii=False)
            # Translate and normalize to English for storage
            ans = dict(self.onboard_answers)
            for k in ['name','education','sex','location','languages_known']:
                ans[k] = self._translate_to_english(ans.get(k))
            ans['skill'] = self._normalize_skill(ans.get('skill'))
            ans['languages_known'] = self._normalize_languages(ans.get('languages_known'))
            ans['sex'] = self._normalize_gender(ans.get('sex'))
            # Numeric-like fields with robust parsing
            def _num_clean(v):
                d = self._normalize_digits(self._translate_to_english(v))
                if not d:
                    d = self._parse_number_words(v)
                return d
            ans['age'] = _num_clean(ans.get('age'))
            ans['experience'] = _num_clean(ans.get('experience'))
            ans['wage_expected'] = _num_clean(ans.get('wage_expected'))
            # Store Aadhaar as raw string value (no normalization)
            ans['aadhaar'] = str(ans.get('aadhaar', '')).strip()
            ts = datetime.utcnow().isoformat()
            
            if existing:
                # Phone exists - update the profile and set profile_created = 1
                worker_id = existing[0]
                c.execute('''UPDATE workers SET 
                    timestamp = ?, profile_created = 1, name = ?, skill = ?, education = ?, age = ?, 
                    sex = ?, experience = ?, location = ?, aadhaar = ?, wage_expected = ?, 
                    languages_known = ?, raw_answers = ?, audio_path = ?
                    WHERE id = ?''',
                    (ts,
                     ans.get('name'),
                     ans.get('skill'),
                     ans.get('education'),
                     ans.get('age'),
                     ans.get('sex'),
                     ans.get('experience'),
                     ans.get('location'),
                     ans.get('aadhaar'),
                     ans.get('wage_expected'),
                     ans.get('languages_known'),
                     raw,
                     None,
                     worker_id
                     ))
            else:
                # New phone number - insert with profile_created = 1
                c.execute('INSERT INTO workers (timestamp, phone_number, profile_created, name, skill, education, age, sex, experience, location, aadhaar, wage_expected, languages_known, raw_answers, audio_path) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                          (ts,
                           self.onboard_phone,  # Phone number from login
                           1,  # profile_created = 1
                           ans.get('name'),
                           ans.get('skill'),
                           ans.get('education'),
                           ans.get('age'),
                           ans.get('sex'),
                           ans.get('experience'),
                           ans.get('location'),
                           ans.get('aadhaar'),
                           ans.get('wage_expected'),
                           ans.get('languages_known'),
                           raw,
                           None
                           ))
            conn.commit()
            conn.close()
            self.update_status(f'Onboarding complete and saved for {self.onboard_phone}')
        except sqlite3.IntegrityError as e:
            self.update_status(f'Phone number already exists. Please login instead.')
        except Exception as e:
            self.update_status(f'Failed to save onboarding: {e}')
        finally:
            self.onboarding = False

    # ----------------- Admin dashboard -----------------
    def show_admin_dashboard(self):
        dlg = QWidget()
        dlg.setWindowTitle('Admin Dashboard - Worker Profiles')
        dlg.setGeometry(150, 150, 1000, 600)
        layout = QVBoxLayout()

        table = QTableWidget()
        # Remove ID column from display; keep it internally for actions
        cols = ['Phone','Name','Skill Type','Education','Age','Gender','Experience','Location','Aadhaar','Wage','Languages','Actions']
        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels(cols)

        def load_rows():
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute('SELECT id, phone_number, name, skill, education, age, sex, experience, location, aadhaar, wage_expected, languages_known FROM workers ORDER BY id DESC')
                rows = c.fetchall()
                conn.close()
            except Exception as e:
                rows = []
                self.update_status(f'Failed to load workers: {e}')

            table.setRowCount(len(rows))
            for r_i, r in enumerate(rows):
                worker_id = r[0]
                # place display columns (skip id at index 0, phone_number is at index 1)
                # Display: phone_number, name, skill, education, age, sex, experience, location, aadhaar, wage_expected, languages_known
                for disp_i in range(11):
                    val = r[disp_i + 1]  # Skip id (index 0)
                    # Ensure English-only display; translate if Hindi detected
                    if isinstance(val, str) and self._contains_hindi(val):
                        val = self._translate_to_english(val, assumed_src='hi')
                    # Normalize numeric-like columns for display
                    # display indices: 4=Age, 6=Experience, 9=Wage (shifted by 1 for phone)
                    # Aadhaar (index 8) is stored as string, no normalization needed
                    if disp_i in (4, 6, 9):
                        val = self._normalize_digits(val)
                    # Normalize languages column for display (index 10 before actions)
                    if disp_i == 10:
                        val = self._normalize_languages(val)
                    # Normalize skill column (index 2, after phone and name)
                    if disp_i == 2:
                        val = self._normalize_skill(val)
                    # Normalize gender column (index 5, after age)
                    if disp_i == 5:
                        val = self._normalize_gender(val)
                    item = QTableWidgetItem(str(val or ''))
                    table.setItem(r_i, disp_i, item)

                # actions
                action_w = QWidget()
                ah = QHBoxLayout()
                ah.setContentsMargins(0,0,0,0)
                edit_btn = QPushButton('Edit')
                del_btn = QPushButton('Delete')

                def make_edit_fn(worker_id):
                    def _edit():
                        # open simple edit dialog
                        dlg_e = QDialog(dlg)
                        dlg_e.setWindowTitle(f'Edit Worker {worker_id}')
                        form = QVBoxLayout()
                        fields = {}
                        labels = ['phone_number','name','skill','education','age','sex','experience','location','aadhaar','wage_expected','languages_known']
                        try:
                            conn = sqlite3.connect(self.db_path)
                            c = conn.cursor()
                            c.execute('SELECT '+','.join(labels)+' FROM workers WHERE id=?',(worker_id,))
                            row = c.fetchone()
                            conn.close()
                        except Exception as e:
                            self.update_status(f'Load for edit failed: {e}')
                            return
                        for i,lab in enumerate(labels):
                            le = QLineEdit()
                            le.setText(str(row[i] or ''))
                            if lab == 'phone_number':
                                le.setReadOnly(True)  # Don't allow phone number changes
                            form.addWidget(QLabel(lab.capitalize()))
                            form.addWidget(le)
                            fields[lab]=le

                        btn_save = QPushButton('Save')
                        def _save():
                            try:
                                vals = [fields[l].text() for l in labels]
                                conn = sqlite3.connect(self.db_path)
                                c = conn.cursor()
                                q = 'UPDATE workers SET ' + ','.join([f"{l}=?" for l in labels]) + ' WHERE id=?'
                                c.execute(q, vals+[worker_id])
                                conn.commit()
                                conn.close()
                                dlg_e.accept()
                                load_rows()
                                self.update_status('Worker updated')
                            except Exception as e:
                                QMessageBox.warning(dlg_e, 'Error', f'Update failed: {e}')

                        btn_save.clicked.connect(_save)
                        form.addWidget(btn_save)
                        dlg_e.setLayout(form)
                        dlg_e.exec_()
                    return _edit

                def make_del_fn(worker_id, row_index):
                    def _del():
                        if QMessageBox.question(dlg, 'Confirm', f'Delete worker {worker_id}?')!=QMessageBox.Yes:
                            return
                        try:
                            conn = sqlite3.connect(self.db_path)
                            c = conn.cursor()
                            c.execute('DELETE FROM workers WHERE id=?',(worker_id,))
                            conn.commit()
                            conn.close()
                            load_rows()
                            self.update_status('Worker deleted')
                        except Exception as e:
                            QMessageBox.warning(dlg, 'Error', f'Delete failed: {e}')
                    return _del

                edit_btn.clicked.connect(make_edit_fn(r[0]))
                del_btn.clicked.connect(make_del_fn(r[0], r_i))

                ah.addWidget(edit_btn)
                ah.addWidget(del_btn)
                action_w.setLayout(ah)
                table.setCellWidget(r_i, 11, action_w)  # Actions column is now at index 11

            table.resizeColumnsToContents()

        load_rows()

        layout.addWidget(table)

        # export CSV
        exp_btn = QPushButton('Export CSV')
        def _export():
            path, _ = QFileDialog.getSaveFileName(dlg, 'Save CSV', 'workers_export.csv', 'CSV Files (*.csv)')
            if path:
                try:
                    conn = sqlite3.connect(self.db_path)
                    c = conn.cursor()
                    c.execute('SELECT id, timestamp, phone_number, name, skill, education, age, sex, experience, location, aadhaar, wage_expected, languages_known, raw_answers FROM workers ORDER BY id')
                    allrows = c.fetchall()
                    conn.close()
                    import csv as _csv
                    with open(path, 'w', newline='', encoding='utf-8') as f:
                        writer = _csv.writer(f)
                        writer.writerow(['id','timestamp','phone_number','name','skill','education','age','sex','experience','location','aadhaar','wage_expected','languages_known','raw_answers'])
                        writer.writerows(allrows)
                    self.update_status('Exported CSV')
                except Exception as e:
                    self.update_status(f'Export failed: {e}')

        exp_btn.clicked.connect(_export)
        layout.addWidget(exp_btn)

        dlg.setLayout(layout)
        dlg.show()

    def save_record(self, src_lang, tgt_lang, original_text, translated_text, audio_path=None):
        """Insert a transcript/translation record and return inserted id."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        ts = datetime.utcnow().isoformat()
        c.execute(
            'INSERT INTO transcripts (timestamp, src_lang, tgt_lang, original_text, translated_text, audio_path) VALUES (?,?,?,?,?,?)',
            (ts, src_lang, tgt_lang, original_text, translated_text, audio_path),
        )
        conn.commit()
        rowid = c.lastrowid
        conn.close()
        return rowid

    def update_audio_path(self, record_id, audio_path):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('UPDATE transcripts SET audio_path = ? WHERE id = ?', (audio_path, record_id))
        conn.commit()
        conn.close()

    def start_recording(self):
        if not self.recording:
            self.recording = True
            self.start_button.setEnabled(False)
            self.spoken_label.clear()
            self.translated_label.clear()
            sel = self.language_dropdown.currentText()
            cfg = self.preset_langs.get(sel)
            if cfg:
                self.selected_src = cfg['src_code']
                self.selected_tgt = cfg['tgt_code']
                self.selected_recog = cfg['src_recog']
                
                # Initialize a new recognizer with enhanced settings
                recognizer = sr.Recognizer()
                # Increase sensitivity for better word capture
                recognizer.energy_threshold = 4000
                recognizer.dynamic_energy_threshold = True
                recognizer.pause_threshold = 0.8  # Shorter pause between phrases
                recognizer.operation_timeout = 30  # Longer operation timeout
                # Improve Hindi capture: don't cut off tails, tolerate brief pauses
                try:
                    recognizer.non_speaking_duration = 0.5
                    recognizer.phrase_threshold = 0.3
                except Exception:
                    pass
                
                # Set translator with explicit source and target
                self.translator = Translator(from_lang=self.selected_src, to_lang=self.selected_tgt)
                
                # Create a fresh recognition thread with improved recognizer
                self.recognition_thread = SpeechRecognitionThread(recognizer, language=self.selected_recog)
                self.recognition_thread.recognition_result.connect(self.translate_and_play)
                self.recognition_thread.status_signal.connect(self.update_status)
                self.recognition_thread.finished.connect(self.on_recognition_finished)
                self.recognition_thread.start()

    def translate_and_play(self, text):
        self.update_status("Processing recognized text")
        
        # Clean up the text - remove extra whitespace and normalize
        text = ' '.join(text.split())
        if not text:
            self.update_status("No text was recognized")
            return
            
        self.spoken_label.setPlainText('Spoken Text: ' + text)
        self.update_status("Translating text...")
        
        # Try primary translation first
        translator = Translator(from_lang=self.selected_src, to_lang=self.selected_tgt)
        try:
            translated_text = translator.translate(text)
            if not translated_text:
                raise Exception("Empty translation result")
        except Exception as e:
            self.update_status(f"Primary translation failed: {e}")
            translated_text = ''

        # If the translation looks suspicious, fallback to the Google web API
        try:
            if self._is_suspicious_translation(text, translated_text):
                self.update_status("Primary translation looks suspicious; using fallback translator")
                try:
                    translated_text_fb = self._fallback_google_translate(text, self.selected_src, self.selected_tgt)
                    if translated_text_fb:
                        translated_text = translated_text_fb
                except Exception:
                    # if fallback fails, keep the best we have
                    pass
        except Exception:
            # safety: don't let heuristic errors block flow
            pass

        self.update_status("Text translated")

        self.translated_label.setPlainText(
            'Translated Text: ' + translated_text
        )

        # Always compute English text for saving (requirement):
        # - If target is English, use translated_text
        # - Else if source is English, use original text
        # - Else translate source -> English using same fallback heuristic
        save_text_en = None
        try:
            if (self.selected_tgt or '').lower().startswith('en'):
                save_text_en = translated_text
            elif (self.selected_src or '').lower().startswith('en'):
                save_text_en = text
            else:
                # Force translate to English
                try:
                    en_primary = Translator(from_lang=self.selected_src, to_lang='en').translate(text)
                except Exception:
                    en_primary = ''
                if not en_primary or self._is_suspicious_translation(text, en_primary):
                    try:
                        en_fb = self._fallback_google_translate(text, self.selected_src, 'en')
                        save_text_en = en_fb or en_primary or text
                    except Exception:
                        save_text_en = en_primary or text
                else:
                    save_text_en = en_primary
        except Exception:
            # last resort, do not block flow
            save_text_en = translated_text or text

        self.player.stop()
        self.player.setMedia(QMediaContent())

        self.update_status("Saving audio file")
        # save TTS of translated text
        try:
            tts = gTTS(translated_text, lang=self.selected_tgt)
            # unique name per translation
            ts = int(datetime.utcnow().timestamp())
            dir_tag = f"{self.selected_src or 'src'}_to_{self.selected_tgt or 'tgt'}"
            safe_tag = re.sub(r'[^a-zA-Z0-9_]+', '_', dir_tag)
            tmp_audio = os.path.join(self.audio_dir, f"translated_{safe_tag}_{ts}.mp3")
            tts.save(tmp_audio)
        except Exception as e:
            self.update_status(f"TTS save failed: {e}")
            tmp_audio = None
        self.update_status("Audio file saved")

    # download button removed; continue

        self.update_status("Playing audio")
        self.player.setMedia(
            QMediaContent(
                QUrl.fromLocalFile(
                    tmp_audio if tmp_audio else ""
                )
            )
        )
        self.player.play()
        self.update_status("Audio played")

        # Save record to DB
        try:
            audio_path = os.path.abspath(tmp_audio) if tmp_audio else None
            # Save English-only translated text per requirement
            self.save_record(self.selected_src, self.selected_tgt, text, save_text_en, audio_path)
        except Exception as e:
            self.update_status(f"DB save failed: {e}")

    def on_recognition_finished(self):
        self.recognition_thread.deleteLater()

        # prepare a fresh thread for next recording using same recognition locale
        self.recognition_thread = SpeechRecognitionThread(sr.Recognizer(), language=self.selected_recog)
        self.recognition_thread.recognition_result.connect(self.translate_and_play)
        self.recognition_thread.status_signal.connect(self.update_status)
        self.recognition_thread.finished.connect(self.on_recognition_finished)

        self.recording = False
        self.start_button.setEnabled(True)

    def closeEvent(self, event):
        # Attempt graceful shutdown of running threads and player
        try:
            try:
                if hasattr(self, 'recognition_thread') and self.recognition_thread.isRunning():
                    # best-effort terminate the thread to avoid Qt warnings on exit
                    try:
                        self.recognition_thread.terminate()
                    except Exception:
                        pass
                    try:
                        self.recognition_thread.wait(1000)
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                if hasattr(self, 'player'):
                    self.player.stop()
            except Exception:
                pass
        finally:
            event.accept()

    def _shutdown_threads(self):
        # Best-effort stop/terminate running threads and stop player
        try:
            thr = getattr(self, 'recognition_thread', None)
            if thr is not None and thr.isRunning():
                try:
                    thr.quit()
                except Exception:
                    pass
                try:
                    thr.terminate()
                except Exception:
                    pass
                try:
                    thr.wait(1000)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            player = getattr(self, 'player', None)
            if player is not None:
                try:
                    player.stop()
                except Exception:
                    pass
        except Exception:
            pass

    def update_status(self, status):
        self.status_bar.showMessage(status)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    converter_app = VoiceConverterApp()
    # Don't show immediately - login dialog will handle visibility
    # converter_app.show()  # Removed - login dialog controls visibility
    sys.exit(app.exec_())

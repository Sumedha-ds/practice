import json
import os
import random
import re
import sqlite3
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import difflib

import requests
from gtts import gTTS
from translate import Translator


class ValidationError(Exception):
    """Raised when supplied data fails validation."""


def _fallback_google_translate(text: str, src: str, tgt: str) -> str:
    base = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": src,
        "tl": tgt,
        "dt": "t",
        "q": text,
    }
    url = base + "?" + urllib.parse.urlencode(params)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    parts = [seg[0] for seg in data[0] if seg and seg[0]]
    return "".join(parts)


def _is_suspicious_translation(src_text: str, translated_text: str) -> bool:
    if not translated_text:
        return True
    if translated_text.strip() == src_text.strip():
        return True
    if len(translated_text.strip()) < max(3, len(src_text.strip()) // 3):
        return True
    lines = translated_text.splitlines()
    short_lines = sum(1 for line in lines if len(line.strip()) <= 2)
    if len(lines) >= 2 and short_lines >= len(lines) // 2:
        return True
    tokens = re.findall(r"\b\w\b", translated_text)
    if len(tokens) >= 2:
        return True
    return False


def _contains_hindi(text: Optional[str]) -> bool:
    if text is None:
        return False
    return bool(re.search(r"[\u0900-\u097F]", text))


def _normalize_digits(text: Optional[str]) -> str:
    if text is None:
        return ""
    s = str(text)
    trans = str.maketrans("०१२३४५६७८९", "0123456789")
    s = s.translate(trans)
    s = re.sub(r"(?<=\d)\s+(?=\d)", "", s)
    return s


def _parse_number_words(text: Optional[str]) -> str:
    if not text:
        return ""
    s = str(text).strip().lower()
    s = re.sub(r"[^a-zA-Z\u0900-\u097F\s\-]", " ", s)
    tokens = s.split()
    en = {
        "zero": 0,
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
        "thirty": 30,
        "forty": 40,
        "fifty": 50,
        "sixty": 60,
        "seventy": 70,
        "eighty": 80,
        "ninety": 90,
        "hundred": 100,
    }
    hi = {
        "शून्य": 0,
        "एक": 1,
        "दो": 2,
        "तीन": 3,
        "चार": 4,
        "पांच": 5,
        "पाँच": 5,
        "छह": 6,
        "सात": 7,
        "आठ": 8,
        "नौ": 9,
        "दस": 10,
        "ग्यारह": 11,
        "बारह": 12,
        "तेरह": 13,
        "चौदह": 14,
        "पंद्रह": 15,
        "सोलह": 16,
        "सत्रह": 17,
        "अठारह": 18,
        "उन्नीस": 19,
        "बीस": 20,
        "तीस": 30,
        "चालीस": 40,
        "पचास": 50,
        "साठ": 60,
        "सत्तर": 70,
        "अस्सी": 80,
        "नब्बे": 90,
        "सौ": 100,
    }
    total = 0
    current = 0
    matched = False
    for token in tokens:
        if token in en:
            val = en[token]
            matched = True
        elif token in hi:
            val = hi[token]
            matched = True
        else:
            continue
        if val == 100:
            current = max(1, current) * val
        else:
            current += val
    total += current
    return str(total) if matched and total > 0 else ""


def _normalize_languages(text: Optional[str]) -> str:
    if not text:
        return ""
    canonical = [
        "Hindi",
        "English",
        "Kannada",
        "Telugu",
        "Marathi",
        "Bengali",
        "Tamil",
        "Gujarati",
        "Urdu",
        "Punjabi",
        "Malayalam",
        "Odia",
        "Assamese",
        "Konkani",
    ]
    manual = {
        "canada": "Kannada",
        "kanada": "Kannada",
        "kannad": "Kannada",
        "hinglish": "English",
        "eng": "English",
        "hin": "Hindi",
    }
    tokens = re.split(r"[,\|/]+|\s{2,}", str(text))
    output = []
    for token in tokens:
        t = token.strip()
        if not t:
            continue
        lower = t.lower()
        if lower in manual:
            output.append(manual[lower])
            continue
        match = difflib.get_close_matches(t, canonical, n=1, cutoff=0.75)
        if not match:
            match = difflib.get_close_matches(t.title(), canonical, n=1, cutoff=0.72)
        output.append(match[0] if match else t)
    seen = set()
    uniq = []
    for language in output:
        if language and language not in seen:
            seen.add(language)
            uniq.append(language)
    return " ".join(uniq)


def _normalize_skill(text: Optional[str]) -> str:
    if not text:
        return ""
    s = str(text).strip()
    if _contains_hindi(s):
        try:
            s = Translator(from_lang="hi", to_lang="en").translate(s)
        except Exception:
            pass
    lower = s.lower()
    replacements = {
        "vaidya": "Doctor",
        "vaidhya": "Doctor",
        "vaid": "Doctor",
        "vedya": "Doctor",
        "doctor": "Doctor",
        "physician": "Doctor",
        "plumber": "Plumber",
        "painter": "Painter",
        "carpenter": "Carpenter",
        "electrician": "Electrician",
        "software engineer": "Software Engineer",
        "driver": "Driver",
        "cook": "Cook",
        "chef": "Cook",
        "mason": "Mason",
    }
    keys = list(replacements.keys())
    match = difflib.get_close_matches(lower, keys, n=1, cutoff=0.8)
    if match:
        return replacements[match[0]]
    match = difflib.get_close_matches(lower, keys, n=1, cutoff=0.7)
    if match:
        return replacements[match[0]]
    return " ".join(word.capitalize() for word in s.split())


def _normalize_gender(text: Optional[str]) -> str:
    if not text:
        return ""
    s = str(text).strip().lower()
    mapping = {
        "male": "Male",
        "man": "Male",
        "men": "Male",
        "female": "Female",
        "woman": "Female",
        "women": "Female",
        "पुरुष": "Male",
        "महिला": "Female",
    }
    if s in mapping:
        return mapping[s]
    match = difflib.get_close_matches(s, list(mapping.keys()), n=1, cutoff=0.8)
    return mapping.get(match[0], s.capitalize() if s else "")


def _translate_to_english(text: Optional[str]) -> str:
    if text is None:
        return ""
    src = "hi" if _contains_hindi(text) else "en"
    if src == "en":
        return text
    try:
        translation = Translator(from_lang=src, to_lang="en").translate(text)
    except Exception:
        translation = ""
    if not translation or _is_suspicious_translation(str(text), translation):
        try:
            translation_fb = _fallback_google_translate(str(text), src, "en")
            return translation_fb or translation or str(text)
        except Exception:
            return translation or str(text)
    return translation


def _clean_numeric(value: Optional[str]) -> str:
    if value is None:
        return ""
    digits = _normalize_digits(value)
    if not digits:
        digits = _parse_number_words(value)
    return digits


@dataclass
class TranslationResult:
    translated_text: str
    english_text: str
    audio_path: Optional[str]


class WorkerService:
    def __init__(
        self,
        db_path: str,
        audio_dir: Optional[str] = None,
        otp_ttl_seconds: int = 300,
    ) -> None:
        self.db_path = db_path
        self.audio_dir = audio_dir or os.path.join(os.path.dirname(db_path), "audio")
        self.otp_ttl = timedelta(seconds=otp_ttl_seconds)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transcripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    src_lang TEXT,
                    tgt_lang TEXT,
                    original_text TEXT,
                    translated_text TEXT,
                    audio_path TEXT
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS workers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    phone_number TEXT UNIQUE,
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
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS otp_sessions (
                    phone_number TEXT PRIMARY KEY,
                    otp TEXT,
                    created_at TEXT
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def create_otp(self, phone_number: str) -> str:
        if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
            raise ValidationError("Phone number must be 10 digits.")
        otp = str(random.randint(100000, 999999))
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO otp_sessions (phone_number, otp, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(phone_number) DO UPDATE SET
                    otp=excluded.otp,
                    created_at=excluded.created_at
                """,
                (phone_number, otp, datetime.utcnow().isoformat()),
            )
            conn.commit()
        finally:
            conn.close()
        return otp

    def verify_otp(self, phone_number: str, otp: str) -> bool:
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT otp, created_at FROM otp_sessions WHERE phone_number = ?",
                (phone_number,),
            )
            row = cursor.fetchone()
            if not row:
                return False
            stored_otp, created_at = row
            created = datetime.fromisoformat(created_at)
            if datetime.utcnow() - created > self.otp_ttl:
                cursor.execute(
                    "DELETE FROM otp_sessions WHERE phone_number = ?", (phone_number,)
                )
                conn.commit()
                return False
            if stored_otp != otp:
                return False
            cursor.execute(
                "DELETE FROM otp_sessions WHERE phone_number = ?", (phone_number,)
            )
            conn.commit()
            return True
        finally:
            conn.close()

    def create_worker(self, phone_number: str, answers: Dict[str, Any]) -> int:
        if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
            raise ValidationError("Phone number must be 10 digits.")
        normalized = dict(answers or {})
        raw_json = json.dumps(normalized, ensure_ascii=False)

        normalized["name"] = _translate_to_english(normalized.get("name"))
        normalized["education"] = _translate_to_english(normalized.get("education"))
        normalized["sex"] = _normalize_gender(normalized.get("sex"))
        normalized["location"] = _translate_to_english(normalized.get("location"))
        normalized["languages_known"] = _normalize_languages(
            normalized.get("languages_known")
        )
        normalized["skill"] = _normalize_skill(normalized.get("skill"))
        normalized["age"] = _clean_numeric(normalized.get("age"))
        normalized["experience"] = _clean_numeric(normalized.get("experience"))
        normalized["wage_expected"] = _clean_numeric(normalized.get("wage_expected"))
        aadhaar_clean = re.sub(
            r"\D", "", _clean_numeric(normalized.get("aadhaar"))
        )
        normalized["aadhaar"] = aadhaar_clean

        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO workers (
                    timestamp,
                    phone_number,
                    name,
                    skill,
                    education,
                    age,
                    sex,
                    experience,
                    location,
                    aadhaar,
                    wage_expected,
                    languages_known,
                    raw_answers,
                    audio_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    phone_number,
                    normalized.get("name"),
                    normalized.get("skill"),
                    normalized.get("education"),
                    normalized.get("age"),
                    normalized.get("sex"),
                    normalized.get("experience"),
                    normalized.get("location"),
                    normalized.get("aadhaar"),
                    normalized.get("wage_expected"),
                    normalized.get("languages_known"),
                    raw_json,
                    answers.get("audio_path"),
                ),
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as exc:
            raise ValidationError("Worker already exists for this phone number.") from exc
        finally:
            conn.close()

    def list_workers(self) -> list[Dict[str, Any]]:
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp, phone_number, name, skill, education, age,
                       sex, experience, location, aadhaar, wage_expected,
                       languages_known, raw_answers
                FROM workers
                ORDER BY id DESC
                """
            )
            rows = cursor.fetchall()
            return [
                {
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
                    "languages_known": row[12],
                    "raw_answers": json.loads(row[13]) if row[13] else {},
                }
                for row in rows
            ]
        finally:
            conn.close()

    def translate_text(
        self,
        text: str,
        src_lang: str,
        tgt_lang: str,
        generate_audio: bool = False,
    ) -> TranslationResult:
        if not text:
            raise ValidationError("Text is required for translation.")
        if not src_lang or not tgt_lang:
            raise ValidationError("Source and target languages are required.")

        cleaned_text = " ".join(text.split())
        try:
            primary = Translator(from_lang=src_lang, to_lang=tgt_lang).translate(
                cleaned_text
            )
        except Exception:
            primary = ""

        translated = primary
        if not translated or _is_suspicious_translation(cleaned_text, translated):
            try:
                translated_fb = _fallback_google_translate(
                    cleaned_text, src_lang, tgt_lang
                )
                if translated_fb:
                    translated = translated_fb
            except Exception:
                translated = translated or cleaned_text

        english_text = translated
        if not tgt_lang.lower().startswith("en"):
            if src_lang.lower().startswith("en"):
                english_text = cleaned_text
            else:
                try:
                    en_primary = Translator(from_lang=src_lang, to_lang="en").translate(
                        cleaned_text
                    )
                except Exception:
                    en_primary = ""
                if not en_primary or _is_suspicious_translation(
                    cleaned_text, en_primary
                ):
                    try:
                        en_fb = _fallback_google_translate(cleaned_text, src_lang, "en")
                        english_text = en_fb or en_primary or cleaned_text
                    except Exception:
                        english_text = en_primary or cleaned_text
                else:
                    english_text = en_primary

        audio_path = None
        if generate_audio and translated:
            timestamp = int(datetime.utcnow().timestamp())
            safe_tag = re.sub(
                r"[^a-zA-Z0-9_]+", "_", f"{src_lang}_to_{tgt_lang}"
            )
            audio_path = os.path.join(
                self.audio_dir, f"translated_{safe_tag}_{timestamp}.mp3"
            )
            try:
                gTTS(translated, lang=tgt_lang).save(audio_path)
            except Exception:
                audio_path = None

        return TranslationResult(
            translated_text=translated, english_text=english_text, audio_path=audio_path
        )

    def create_transcript(
        self,
        original_text: str,
        src_lang: str,
        tgt_lang: str,
        generate_audio: bool = False,
    ) -> Dict[str, Any]:
        translation = self.translate_text(
            original_text, src_lang, tgt_lang, generate_audio=generate_audio
        )
        conn = self._connect()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO transcripts (
                    timestamp,
                    src_lang,
                    tgt_lang,
                    original_text,
                    translated_text,
                    audio_path
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    src_lang,
                    tgt_lang,
                    original_text,
                    translation.english_text,
                    translation.audio_path,
                ),
            )
            conn.commit()
            transcript_id = cursor.lastrowid
        finally:
            conn.close()
        return {
            "id": transcript_id,
            "original_text": original_text,
            "translated_text": translation.translated_text,
            "english_text": translation.english_text,
            "audio_path": translation.audio_path,
        }



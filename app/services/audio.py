"""Audio generation services for job announcements."""
from __future__ import annotations

import base64
import io

try:
    from gtts import gTTS

    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    print("Warning: gTTS not available. Audio generation will be disabled.")

JOB_TITLES_HINDI = {
    "Carpenter": "बढ़ई",
    "Painter": "पेंटर",
    "Plumber": "प्लम्बर",
    "Cook": "रसोइया",
    "Maid": "नौकरानी",
    "Pet Caretaker": "पालतू जानवर की देखभाल करने वाला",
    "Electrician": "इलेक्ट्रीशियन",
    "Delivery Driver": "डिलीवरी ड्राइवर",
}

CITIES_HINDI = {
    "Pune": "पुणे",
    "Jaipur": "जयपुर",
    "Lucknow": "लखनऊ",
    "Indore": "इंदौर",
    "Chandigarh": "चंडीगढ़",
    "Nagpur": "नागपुर",
    "Coimbatore": "कोयंबटूर",
}

GENDER_HINDI = {
    "Any": "कोई भी",
    "Male": "पुरुष",
    "Female": "महिला",
}


def number_to_hindi_words(number: int) -> str:
    """Convert a number to Hindi words."""
    ones = ["", "एक", "दो", "तीन", "चार", "पांच", "छह", "सात", "आठ", "नौ"]
    teens = [
        "दस",
        "ग्यारह",
        "बारह",
        "तेरह",
        "चौदह",
        "पंद्रह",
        "सोलह",
        "सत्रह",
        "अठारह",
        "उन्नीस",
    ]
    tens_words = ["", "", "बीस", "तीस", "चालीस", "पचास", "साठ", "सत्तर", "अस्सी", "नब्बे"]

    twenties = {
        21: "इक्कीस",
        22: "बाईस",
        23: "तेईस",
        24: "चौबीस",
        25: "पच्चीस",
        26: "छब्बीस",
        27: "सत्ताईस",
        28: "अट्ठाईस",
        29: "उनतीस",
    }

    if number == 0:
        return "शून्य"

    if number < 10:
        return ones[number]
    if number < 20:
        return teens[number - 10]
    if 21 <= number <= 29:
        return twenties[number]
    if number < 100:
        tens_digit = number // 10
        ones_digit = number % 10
        if ones_digit == 0:
            return tens_words[tens_digit]
        return tens_words[tens_digit] + " " + ones[ones_digit]
    if number < 1000:
        hundreds_digit = number // 100
        remainder = number % 100
        if remainder == 0:
            if hundreds_digit == 1:
                return "एक सौ"
            return ones[hundreds_digit] + " सौ"
        if hundreds_digit == 1:
            return "एक सौ " + number_to_hindi_words(remainder)
        return ones[hundreds_digit] + " सौ " + number_to_hindi_words(remainder)
    if number < 100000:
        thousands = number // 1000
        remainder = number % 1000
        if remainder == 0:
            if thousands == 1:
                return "एक हज़ार"
            if thousands < 10:
                return ones[thousands] + " हज़ार"
            return number_to_hindi_words(thousands) + " हज़ार"
        if thousands == 1:
            return "एक हज़ार " + number_to_hindi_words(remainder)
        if thousands < 10:
            return ones[thousands] + " हज़ार " + number_to_hindi_words(remainder)
        return number_to_hindi_words(thousands) + " हज़ार " + number_to_hindi_words(remainder)
    return str(number)


def generate_hindi_audio_script(job_title: str, wage: float, city: str, gender: str) -> str:
    """Generate Hindi audio script for a job in a natural, conversational format."""
    job_title_hindi = JOB_TITLES_HINDI.get(job_title, job_title)
    city_hindi = CITIES_HINDI.get(city, city)
    gender_hindi = GENDER_HINDI.get(gender, gender)

    wage_int = int(wage)
    wage_in_thousands = wage_int // 1000
    wage_hindi = number_to_hindi_words(wage_in_thousands)

    if gender == "Female":
        gender_text = "इसके लिए महिलाओं की जरूरत है।"
    elif gender == "Male":
        gender_text = "इसके लिए पुरुषों की जरूरत है।"
    else:
        gender_text = "कोई भी व्यक्ति आवेदन कर सकता है।"

    audio_script = (
        f"नमस्ते, यहाँ {job_title_hindi} की नौकरी है। "
        f"वेतन {wage_hindi} हज़ार रुपये महीने का है। "
        f"यह नौकरी {city_hindi} में है। "
        f"{gender_text}"
    )

    return audio_script


def generate_hindi_audio_base64(hindi_text: str, lang: str = "hi") -> str:
    """Generate Hindi audio from text and return as base64 encoded string."""
    if not GTTS_AVAILABLE:
        print("Warning: gTTS not available. Returning empty audio string.")
        return ""

    try:
        tts = gTTS(text=hindi_text, lang=lang, slow=False)

        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        audio_base64 = base64.b64encode(audio_buffer.read()).decode("utf-8")
        return f"data:audio/mp3;base64,{audio_base64}"
    except Exception as exc:  # noqa: BLE001
        print(f"Error generating audio: {exc}")
        return ""


def generate_job_audio_with_script(job_title: str, wage: float, city: str, gender: str) -> tuple[str, str]:
    """Generate both Hindi audio script text and base64 encoded audio for a job."""
    audio_script = generate_hindi_audio_script(job_title, wage, city, gender)
    audio_base64 = generate_hindi_audio_base64(audio_script, lang="hi")

    return audio_script, audio_base64


__all__ = [
    "generate_job_audio_with_script",
    "generate_hindi_audio_script",
    "generate_hindi_audio_base64",
    "number_to_hindi_words",
]



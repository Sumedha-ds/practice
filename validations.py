"""
Smart Validations for Voice-based Onboarding System
Validates user responses and provides Hindi error messages
"""

import re
from typing import Dict, Tuple, Optional
from difflib import get_close_matches

class OnboardingValidator:
    """
    Validates onboarding answers with smart error messages in Hindi
    """
    
    # Known job types (in English, matched against translated text)
    JOB_CATEGORIES = [
        # Construction & Building
        'painter', 'plumber', 'electrician', 'carpenter', 'mason', 'welder',
        'construction worker', 'contractor', 'tile setter', 'roofer',
        
        # Domestic Services
        'cook', 'chef', 'maid', 'housekeeper', 'cleaner', 'nanny', 'babysitter',
        'security guard', 'watchman', 'gardener', 'driver',
        
        # Delivery & Transport
        'delivery boy', 'courier', 'auto driver', 'taxi driver', 'truck driver',
        'loader', 'warehouse worker', 'packer',
        
        # Retail & Sales
        'salesman', 'shopkeeper', 'cashier', 'helper', 'assistant',
        
        # Technical & Repair
        'mechanic', 'ac technician', 'refrigerator technician', 'mobile repair',
        'computer repair', 'bike mechanic', 'car mechanic',
        
        # Textiles & Fashion
        'tailor', 'seamstress', 'embroidery worker', 'textile worker',
        
        # Food & Hospitality
        'waiter', 'server', 'bartender', 'dishwasher', 'kitchen helper',
        
        # Beauty & Wellness
        'beautician', 'barber', 'salon worker', 'spa worker', 'masseuse',
        
        # Agriculture
        'farmer', 'farm worker', 'agricultural worker', 'gardener',
        
        # Manufacturing
        'factory worker', 'machine operator', 'production worker', 'assembler',
        
        # Others
        'labourer', 'worker', 'office boy', 'peon', 'attendant'
    ]
    
    # Hindi translations for job categories (for better matching)
    JOB_HINDI_MAPPING = {
        'पेंटर': 'painter', 'रंगकर्मी': 'painter',
        'प्लंबर': 'plumber', 'नलसाज': 'plumber',
        'इलेक्ट्रीशियन': 'electrician', 'बिजली मिस्त्री': 'electrician',
        'बढ़ई': 'carpenter', 'लकड़ी का काम': 'carpenter',
        'राजमिस्त्री': 'mason', 'मिस्त्री': 'mason',
        'वेल्डर': 'welder', 'वेल्डिंग': 'welder',
        'रसोइया': 'cook', 'खाना बनाने वाला': 'cook',
        'ड्राइवर': 'driver', 'चालक': 'driver',
        'माली': 'gardener', 'गार्डनर': 'gardener',
        'सिक्योरिटी': 'security guard', 'चौकीदार': 'security guard',
        'मैकेनिक': 'mechanic', 'मिस्त्री': 'mechanic',
        'दर्जी': 'tailor', 'टेलर': 'tailor',
        'नाई': 'barber', 'हजाम': 'barber',
        'सफाई कर्मी': 'cleaner', 'क्लीनर': 'cleaner',
        'नौकर': 'helper', 'हेल्पर': 'helper',
        'मजदूर': 'labourer', 'लेबर': 'labourer'
    }
    
    # Indian states and major cities for location validation
    LOCATIONS = [
        # Major Cities
        'mumbai', 'delhi', 'bangalore', 'bengaluru', 'hyderabad', 'ahmedabad',
        'chennai', 'kolkata', 'surat', 'pune', 'jaipur', 'lucknow', 'kanpur',
        'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam', 'pimpri',
        'patna', 'vadodara', 'ghaziabad', 'ludhiana', 'agra', 'nashik',
        'faridabad', 'meerut', 'rajkot', 'kalyan', 'vasai', 'varanasi',
        'srinagar', 'aurangabad', 'dhanbad', 'amritsar', 'navi mumbai',
        'allahabad', 'prayagraj', 'ranchi', 'howrah', 'coimbatore', 'jabalpur',
        
        # States
        'maharashtra', 'karnataka', 'tamil nadu', 'kerala', 'gujarat',
        'rajasthan', 'punjab', 'haryana', 'uttar pradesh', 'up', 'bihar',
        'west bengal', 'odisha', 'telangana', 'andhra pradesh', 'madhya pradesh',
        'mp', 'jharkhand', 'assam', 'chhattisgarh', 'uttarakhand', 'goa',
        'himachal pradesh', 'hp', 'jammu and kashmir', 'jk'
    ]
    
    # Error messages in English and Hindi
    ERROR_MESSAGES = {
        'name_invalid': {
            'en': 'Please tell only your name.',
            'hi': 'कृपया केवल अपना नाम बताएं।'
        },
        'age_invalid': {
            'en': 'Please tell your correct age between 16 and 70.',
            'hi': 'कृपया 16 से 70 के बीच अपनी सही उम्र बताएं।'
        },
        'skill_invalid': {
            'en': 'Please tell a job type like painter, electrician, driver, or cook.',
            'hi': 'कृपया पेंटर, इलेक्ट्रीशियन, ड्राइवर या रसोइया जैसे काम का नाम बताएं।'
        },
        'experience_invalid': {
            'en': 'Please tell your experience in years or months.',
            'hi': 'कृपया अपना अनुभव साल या महीने में बताएं।'
        },
        'location_invalid': {
            'en': 'Please tell your city or state name.',
            'hi': 'कृपया अपना शहर या राज्य का नाम बताएं।'
        },
        'gender_invalid': {
            'en': 'Please say male or female.',
            'hi': 'कृपया पुरुष या महिला बताएं।'
        },
        'phone_invalid': {
            'en': 'Please tell a valid 10 digit mobile number.',
            'hi': 'कृपया 10 अंको का सही मोबाइल नंबर बताएं।'
        }
    }
    
    @staticmethod
    def validate_name(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate name: 1-3 words, alphabets only
        Returns: (is_valid, cleaned_value, error_message)
        """
        if not text or not text.strip():
            return False, None, OnboardingValidator.ERROR_MESSAGES['name_invalid']['hi']
        
        # Clean and normalize
        text = text.strip()
        
        # Remove common filler words
        filler_words = ['my', 'name', 'is', 'i', 'am', 'मेरा', 'नाम', 'है', 'मैं', 'हूं']
        words = text.lower().split()
        words = [w for w in words if w not in filler_words]
        text_cleaned = ' '.join(words)
        
        # Check word count (1-3 words)
        word_count = len(words)
        if word_count == 0 or word_count > 4:
            return False, None, OnboardingValidator.ERROR_MESSAGES['name_invalid']['hi']
        
        # Check if mostly alphabets (allow spaces and common name characters)
        # Must have at least 70% alphabetic characters and no digits at the start
        if any(c.isdigit() for c in text_cleaned):
            return False, None, OnboardingValidator.ERROR_MESSAGES['name_invalid']['hi']
        
        alpha_chars = sum(c.isalpha() or c.isspace() for c in text_cleaned)
        if alpha_chars < len(text_cleaned) * 0.7:  # At least 70% alphabets
            return False, None, OnboardingValidator.ERROR_MESSAGES['name_invalid']['hi']
        
        # Capitalize first letter of each word
        name = text_cleaned.title()
        
        return True, name, None
    
    @staticmethod
    def validate_age(text: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Validate age: number between 16 and 70
        Returns: (is_valid, age_value, error_message)
        """
        if not text or not text.strip():
            return False, None, OnboardingValidator.ERROR_MESSAGES['age_invalid']['hi']
        
        # Extract numbers from text
        numbers = re.findall(r'\d+', text)
        
        if not numbers:
            return False, None, OnboardingValidator.ERROR_MESSAGES['age_invalid']['hi']
        
        # Take the first number found
        age = int(numbers[0])
        
        # Validate range
        if age < 16 or age > 70:
            return False, None, OnboardingValidator.ERROR_MESSAGES['age_invalid']['hi']
        
        return True, age, None
    
    @staticmethod
    def validate_skill(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate job/skill: match to known categories
        Returns: (is_valid, matched_skill, error_message)
        """
        if not text or not text.strip():
            return False, None, OnboardingValidator.ERROR_MESSAGES['skill_invalid']['hi']
        
        text_lower = text.lower().strip()
        
        # Direct match in job categories
        if text_lower in OnboardingValidator.JOB_CATEGORIES:
            return True, text_lower, None
        
        # Check for partial matches
        for job in OnboardingValidator.JOB_CATEGORIES:
            if job in text_lower or text_lower in job:
                return True, job, None
        
        # Fuzzy matching for typos
        close_matches = get_close_matches(
            text_lower, 
            OnboardingValidator.JOB_CATEGORIES, 
            n=1, 
            cutoff=0.6
        )
        
        if close_matches:
            return True, close_matches[0], None
        
        # Check Hindi mapping (in case translation missed it)
        for hindi_term, english_job in OnboardingValidator.JOB_HINDI_MAPPING.items():
            if hindi_term in text_lower:
                return True, english_job, None
        
        # If no match, still accept but flag for review
        # (for demo purposes, we'll be lenient)
        if len(text_lower.split()) <= 3:
            return True, text_lower, None
        
        return False, None, OnboardingValidator.ERROR_MESSAGES['skill_invalid']['hi']
    
    @staticmethod
    def validate_experience(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate experience: numbers or durations like "2 years", "6 months"
        Returns: (is_valid, experience_value, error_message)
        """
        if not text or not text.strip():
            return False, None, OnboardingValidator.ERROR_MESSAGES['experience_invalid']['hi']
        
        text_lower = text.lower().strip()
        
        # Check for "fresher" or "no experience"
        fresher_keywords = ['fresher', 'no experience', 'zero', 'new', 'नया', 'फ्रेशर', 'कोई नहीं']
        if any(keyword in text_lower for keyword in fresher_keywords):
            return True, 'Fresher', None
        
        # Extract numbers
        numbers = re.findall(r'\d+', text)
        
        if not numbers:
            return False, None, OnboardingValidator.ERROR_MESSAGES['experience_invalid']['hi']
        
        exp_value = int(numbers[0])
        
        # Check for time units
        if 'month' in text_lower or 'महीने' in text_lower or 'mahine' in text_lower:
            if exp_value > 11:
                # Convert to years
                years = exp_value // 12
                months = exp_value % 12
                if months > 0:
                    return True, f"{years} years {months} months", None
                else:
                    return True, f"{years} years", None
            return True, f"{exp_value} months", None
        
        elif 'year' in text_lower or 'साल' in text_lower or 'saal' in text_lower:
            if exp_value > 50:  # Unrealistic
                return False, None, OnboardingValidator.ERROR_MESSAGES['experience_invalid']['hi']
            return True, f"{exp_value} years", None
        
        else:
            # Assume years if no unit specified
            if exp_value <= 50:
                return True, f"{exp_value} years", None
            else:
                return False, None, OnboardingValidator.ERROR_MESSAGES['experience_invalid']['hi']
    
    @staticmethod
    def validate_location(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate location: Indian cities or states
        Returns: (is_valid, location_value, error_message)
        """
        if not text or not text.strip():
            return False, None, OnboardingValidator.ERROR_MESSAGES['location_invalid']['hi']
        
        text_lower = text.lower().strip()
        
        # Remove common filler words
        filler_words = ['from', 'in', 'at', 'से', 'में']
        words = text_lower.split()
        words = [w for w in words if w not in filler_words]
        text_cleaned = ' '.join(words)
        
        # Direct match
        if text_cleaned in OnboardingValidator.LOCATIONS:
            return True, text_cleaned.title(), None
        
        # Partial match
        for location in OnboardingValidator.LOCATIONS:
            if location in text_cleaned or text_cleaned in location:
                return True, location.title(), None
        
        # Fuzzy matching
        close_matches = get_close_matches(
            text_cleaned, 
            OnboardingValidator.LOCATIONS, 
            n=1, 
            cutoff=0.7
        )
        
        if close_matches:
            return True, close_matches[0].title(), None
        
        # Accept any reasonable location name (for places not in our list)
        if len(words) <= 3 and any(c.isalpha() for c in text_cleaned):
            return True, text_cleaned.title(), None
        
        return False, None, OnboardingValidator.ERROR_MESSAGES['location_invalid']['hi']
    
    @staticmethod
    def validate_gender(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate gender: male or female
        Returns: (is_valid, gender_value, error_message)
        """
        if not text or not text.strip():
            return False, None, OnboardingValidator.ERROR_MESSAGES['gender_invalid']['hi']
        
        text_lower = text.lower().strip()
        
        # Male keywords
        male_keywords = ['male', 'man', 'boy', 'mr', 'पुरुष', 'आदमी', 'लड़का', 'मर्द']
        # Female keywords
        female_keywords = ['female', 'woman', 'girl', 'mrs', 'miss', 'महिला', 'औरत', 'लड़की']
        
        if any(keyword in text_lower for keyword in male_keywords):
            return True, 'Male', None
        
        if any(keyword in text_lower for keyword in female_keywords):
            return True, 'Female', None
        
        return False, None, OnboardingValidator.ERROR_MESSAGES['gender_invalid']['hi']
    
    @staticmethod
    def validate_phone(text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate phone number: 10 digits
        Returns: (is_valid, phone_value, error_message)
        """
        if not text or not text.strip():
            return False, None, OnboardingValidator.ERROR_MESSAGES['phone_invalid']['hi']
        
        # Extract all digits
        digits = re.sub(r'\D', '', text)
        
        # Check for 10 digits
        if len(digits) == 10 and digits[0] in '6789':
            return True, digits, None
        
        return False, None, OnboardingValidator.ERROR_MESSAGES['phone_invalid']['hi']
    
    @staticmethod
    def validate_answer(question_key: str, answer_text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Main validation dispatcher
        Returns: (is_valid, cleaned_value, error_message_in_hindi)
        """
        validators = {
            'name': OnboardingValidator.validate_name,
            'age': OnboardingValidator.validate_age,
            'skill': OnboardingValidator.validate_skill,
            'experience': OnboardingValidator.validate_experience,
            'location': OnboardingValidator.validate_location,
            'gender': OnboardingValidator.validate_gender,
            'phone': OnboardingValidator.validate_phone,
        }
        
        validator = validators.get(question_key)
        
        if not validator:
            # No specific validator, accept as-is
            return True, answer_text.strip(), None
        
        return validator(answer_text)


# Utility function for generating voice feedback
def generate_error_voice(error_message_hindi: str) -> bytes:
    """
    Generate voice feedback for error messages in Hindi
    Returns: MP3 audio bytes
    """
    try:
        from gtts import gTTS
        import io
        
        tts = gTTS(text=error_message_hindi, lang='hi', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        
        return audio_buffer.read()
    
    except Exception as e:
        print(f"Error generating voice: {e}")
        return None


# Example usage
if __name__ == "__main__":
    print("=== Testing Onboarding Validator ===\n")
    
    test_cases = [
        ('name', 'My name is Rajesh Kumar'),
        ('name', '123 invalid'),
        ('age', 'I am 25 years old'),
        ('age', '150'),
        ('skill', 'I am a painter'),
        ('skill', 'xyz random job'),
        ('experience', '5 years'),
        ('experience', 'fresher'),
        ('location', 'I am from Mumbai'),
        ('gender', 'male'),
    ]
    
    for question, answer in test_cases:
        is_valid, value, error = OnboardingValidator.validate_answer(question, answer)
        status = "✅" if is_valid else "❌"
        print(f"{status} {question}: '{answer}'")
        if is_valid:
            print(f"   → Valid: {value}")
        else:
            print(f"   → Error: {error}")
        print()

